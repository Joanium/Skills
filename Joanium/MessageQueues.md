---
name: Message Queues & Background Jobs
trigger: message queue, job queue, background jobs, BullMQ, bull queue, RabbitMQ, Kafka, pub/sub, worker, async processing, task queue, event queue, dead letter queue, retry logic, queue processing, delayed jobs
description: Build reliable async processing with message queues and background jobs. Covers BullMQ (Redis-backed), RabbitMQ, and Kafka patterns including job definitions, workers, retries, dead letter queues, scheduled jobs, and monitoring.
---

# ROLE
You are a backend engineer specializing in async systems. Your job is to offload slow, failure-prone, or high-volume work from the request-response cycle into reliable background processing. A well-designed queue system degrades gracefully and never loses jobs.

# WHEN TO USE A QUEUE
```
USE A QUEUE FOR:
  ✓ Sending emails / SMS (slow, third-party dependency)
  ✓ Image/video processing (CPU-intensive)
  ✓ Webhook delivery (retries needed)
  ✓ Report generation (takes seconds or minutes)
  ✓ Batch operations (process 10k records)
  ✓ Anything that can fail and needs retry
  ✓ Rate-limited external API calls
  ✓ Delayed/scheduled tasks

DON'T QUEUE:
  ✗ Simple DB reads/writes (just do them synchronously)
  ✗ Operations the user must wait for before continuing
  ✗ Things that must happen transactionally with the HTTP response
```

# BULLMQ (Redis-backed — Best for Node.js)

## Setup and Queue Definition
```typescript
import { Queue, Worker, QueueEvents } from 'bullmq'
import { createClient } from 'redis'

const connection = { host: 'localhost', port: 6379 }

// Define job types
interface EmailJob {
  to: string
  subject: string
  template: 'welcome' | 'password-reset' | 'invoice'
  context: Record<string, any>
}

interface ImageJob {
  sourceKey: string       // S3 key of uploaded image
  userId: string
  outputSizes: number[]   // [200, 400, 800]
}

// Create queues
export const emailQueue = new Queue<EmailJob>('email', { connection })
export const imageQueue = new Queue<ImageJob>('image-processing', {
  connection,
  defaultJobOptions: {
    attempts: 3,
    backoff: { type: 'exponential', delay: 2000 },
    removeOnComplete: { count: 100 },  // keep last 100 completed
    removeOnFail: false,               // keep failed jobs for inspection
  }
})
```

## Adding Jobs
```typescript
// Immediate job
await emailQueue.add('send-welcome', {
  to: 'user@example.com',
  subject: 'Welcome!',
  template: 'welcome',
  context: { name: 'Alice', loginUrl: 'https://app.example.com' }
})

// Delayed job (send after 1 hour)
await emailQueue.add('send-reminder', jobData, {
  delay: 60 * 60 * 1000   // ms
})

// Scheduled/recurring job (cron)
await emailQueue.add('weekly-digest', {}, {
  repeat: { cron: '0 9 * * 1' }  // every Monday at 9am
})

// Priority job (lower number = higher priority)
await emailQueue.add('send-password-reset', jobData, {
  priority: 1   // process before normal priority (default 0 = lowest)
})

// Bulk add
await emailQueue.addBulk([
  { name: 'send-invoice', data: job1 },
  { name: 'send-invoice', data: job2 },
])
```

## Workers — Process Jobs
```typescript
const emailWorker = new Worker<EmailJob>(
  'email',
  async (job) => {
    const { to, subject, template, context } = job.data

    job.log(`Sending ${template} email to ${to}`)

    // Update progress
    await job.updateProgress(10)

    const html = await renderTemplate(template, context)
    await job.updateProgress(50)

    await sendgrid.send({ to, subject, html })
    await job.updateProgress(100)

    job.log(`Email sent successfully`)

    return { sentAt: new Date().toISOString() }   // stored in job.returnvalue
  },
  {
    connection,
    concurrency: 5,   // process up to 5 jobs in parallel
    limiter: {
      max: 100,       // max 100 jobs
      duration: 60_000,  // per minute (rate limiting)
    }
  }
)

// Lifecycle events
emailWorker.on('completed', (job, result) => {
  console.log(`Job ${job.id} completed:`, result)
})

emailWorker.on('failed', (job, error) => {
  console.error(`Job ${job?.id} failed:`, error.message)
  // Alert if this was the last retry
  if (job?.attemptsMade === job?.opts.attempts) {
    alertTeam({ jobId: job.id, error: error.message })
  }
})

emailWorker.on('stalled', (jobId) => {
  console.warn(`Job ${jobId} stalled — worker may have crashed`)
})
```

## Dead Letter Queue (DLQ) Pattern
```typescript
// Jobs that exhaust all retries go here
const dlqQueue = new Queue('dead-letter', { connection })

const worker = new Worker('email', processJob, { connection })

worker.on('failed', async (job, error) => {
  if (!job) return
  const isLastAttempt = job.attemptsMade >= (job.opts.attempts ?? 1)

  if (isLastAttempt) {
    // Move to DLQ for manual inspection/replay
    await dlqQueue.add('failed-email', {
      originalJob: job.data,
      originalQueue: 'email',
      failedAt: new Date().toISOString(),
      error: error.message,
      stack: error.stack,
      attempts: job.attemptsMade,
    })
  }
})

// Replay from DLQ
async function replayFromDLQ(jobId: string) {
  const dlqJob = await dlqQueue.getJob(jobId)
  if (!dlqJob) throw new Error('Job not found in DLQ')

  const { originalQueue, originalJob } = dlqJob.data
  const queue = new Queue(originalQueue, { connection })
  await queue.add('replayed', originalJob)
  await dlqJob.remove()
}
```

## Job Progress and Monitoring
```typescript
// From worker: report progress
await job.updateProgress({ current: 50, total: 200, phase: 'resizing' })
await job.log('Completed 200px variant')

// From API: check progress
app.get('/jobs/:jobId/status', async (req, res) => {
  const job = await imageQueue.getJob(req.params.jobId)
  if (!job) return res.status(404).json({ error: 'Job not found' })

  const state = await job.getState()   // 'waiting' | 'active' | 'completed' | 'failed'

  res.json({
    id: job.id,
    state,
    progress: job.progress,
    result: state === 'completed' ? job.returnvalue : null,
    error: state === 'failed' ? job.failedReason : null,
    createdAt: new Date(job.timestamp).toISOString(),
    processedAt: job.processedOn ? new Date(job.processedOn).toISOString() : null,
    logs: await job.getLogs(),
  })
})

// Queue metrics
async function getQueueMetrics(queue: Queue) {
  const [waiting, active, completed, failed, delayed] = await Promise.all([
    queue.getWaitingCount(),
    queue.getActiveCount(),
    queue.getCompletedCount(),
    queue.getFailedCount(),
    queue.getDelayedCount(),
  ])
  return { waiting, active, completed, failed, delayed }
}
```

# RABBITMQ PATTERNS

## Direct Exchange (Point-to-Point)
```typescript
import amqp from 'amqplib'

const connection = await amqp.connect(process.env.RABBITMQ_URL!)
const channel = await connection.createConfirmChannel()

// Publisher
async function publishEmail(job: EmailJob) {
  const queue = 'email.send'
  await channel.assertQueue(queue, {
    durable: true,               // survive server restart
    deadLetterExchange: 'dlx',   // failed messages go here
  })

  const published = channel.sendToQueue(
    queue,
    Buffer.from(JSON.stringify(job)),
    {
      persistent: true,          // persist message to disk
      contentType: 'application/json',
      messageId: crypto.randomUUID(),
    }
  )

  if (!published) throw new Error('Queue is full — backpressure')
}

// Consumer
async function startEmailConsumer() {
  await channel.assertQueue('email.send', { durable: true })
  await channel.prefetch(5)   // process up to 5 at once

  channel.consume('email.send', async (msg) => {
    if (!msg) return

    const job = JSON.parse(msg.content.toString()) as EmailJob

    try {
      await sendEmail(job)
      channel.ack(msg)            // mark as processed
    } catch (error) {
      // Reject and requeue (nack) with requeue=false to send to DLX
      channel.nack(msg, false, false)
    }
  })
}
```

## Pub/Sub with Fanout Exchange
```typescript
// One message → multiple consumers
// Use for: event broadcasting (user.created → welcome email + analytics + CRM)

async function setupEventBus() {
  // Fanout: broadcasts to all bound queues
  await channel.assertExchange('events', 'fanout', { durable: true })

  // Each service declares its own queue
  const { queue: emailQueue } = await channel.assertQueue('events.email', { durable: true })
  const { queue: analyticsQueue } = await channel.assertQueue('events.analytics', { durable: true })

  await channel.bindQueue(emailQueue, 'events', '')
  await channel.bindQueue(analyticsQueue, 'events', '')
}

// Publish event — both consumers receive it
function publishEvent(event: object) {
  channel.publish('events', '', Buffer.from(JSON.stringify(event)), { persistent: true })
}
```

# KAFKA (High-Throughput Event Streaming)
```typescript
import { Kafka } from 'kafkajs'

const kafka = new Kafka({
  clientId: 'my-app',
  brokers: [process.env.KAFKA_BROKER!],
})

// Producer
const producer = kafka.producer()
await producer.connect()

await producer.send({
  topic: 'user-events',
  messages: [
    {
      key: userId,       // messages with same key go to same partition (ordering guarantee)
      value: JSON.stringify({ type: 'user.created', userId, timestamp: Date.now() }),
      headers: { source: 'auth-service' }
    }
  ]
})

// Consumer
const consumer = kafka.consumer({ groupId: 'analytics-service' })
await consumer.connect()
await consumer.subscribe({ topic: 'user-events', fromBeginning: false })

await consumer.run({
  eachMessage: async ({ topic, partition, message }) => {
    const event = JSON.parse(message.value!.toString())
    await processEvent(event)
    // Offset is committed automatically after eachMessage returns without error
  }
})
```

# PATTERNS AND BEST PRACTICES
```
IDEMPOTENCY — jobs may run more than once (retries, at-least-once delivery)
  → Every job must be safe to run multiple times
  → Use job.id as idempotency key in external systems
  → Store processed job IDs in Redis with TTL to deduplicate

TIMEOUTS — set job execution time limits
  await worker.on('... timeout ...')  // BullMQ: use lockDuration option

GRACEFUL SHUTDOWN — don't kill jobs mid-execution
  process.on('SIGTERM', async () => {
    await worker.close()     // wait for current job to finish
    await queue.close()
    process.exit(0)
  })

OBSERVABILITY:
  - Track: queue depth, processing rate, error rate, p95 job duration
  - Alert on: queue growing unboundedly, high error rate, stalled workers
  - Use Bull Board or Arena for visual monitoring of BullMQ queues

CIRCUIT BREAKER — stop hammering a failing service
  const breaker = new CircuitBreaker(sendEmail, { errorThresholdPercentage: 50 })
  // Opens after 50% failures → stops calling sendEmail until service recovers
```
