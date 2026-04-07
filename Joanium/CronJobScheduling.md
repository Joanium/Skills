---
name: Cron Job Scheduling
trigger: cron job, scheduled task, task scheduling, cron expression, scheduled jobs, periodic task, background scheduler, job queue scheduling
description: Design and implement reliable scheduled tasks using cron expressions, job queues, and distributed schedulers. Covers idempotency, error handling, monitoring, and avoiding overlapping executions. Use when creating scheduled jobs, periodic tasks, or time-based workflows.
---

# ROLE
You are a backend engineer specializing in scheduled task design. Your job is to create reliable, idempotent cron jobs and scheduled tasks that handle failures gracefully and don't overlap.

# CRON EXPRESSIONS
```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6)
│ │ │ │ │
* * * * *

Examples:
*/5 * * * *     → Every 5 minutes
0 */2 * * *     → Every 2 hours
0 0 * * 0       → Every Sunday at midnight
0 0 1 * *       → First of every month at midnight
0 9-17 * * 1-5  → Every hour 9-5, Monday-Friday
```

# NODE.JS SCHEDULER
```typescript
import cron from 'node-cron'
import { logger } from './logger'

// Simple cron job
cron.schedule('0 2 * * *', async () => {
  logger.info('Starting daily cleanup job')
  try {
    await cleanupExpiredSessions()
    logger.info('Daily cleanup completed')
  } catch (error) {
    logger.error('Daily cleanup failed', { error })
  }
})

// With locking to prevent overlapping
import Redlock from 'redlock'

const redlock = new Redlock([redisClient])

cron.schedule('*/5 * * * *', async () => {
  const lockKey = 'lock:sync-metrics'
  
  try {
    const lock = await redlock.acquire([lockKey], 240000) // 4 min timeout
    
    try {
      await syncMetrics()
    } finally {
      await lock.release()
    }
  } catch (error) {
    if (error instanceof Redlock.LockError) {
      logger.info('Sync already running, skipping')
    } else {
      logger.error('Sync failed', { error })
    }
  }
})
```

# IDEMPOTENT JOBS
```typescript
// Jobs must be safe to run multiple times
async function sendDailyReport() {
  const today = new Date().toISOString().split('T')[0]
  
  // Check if already sent today
  const alreadySent = await db.jobLog.findFirst({
    where: { name: 'daily-report', date: today }
  })
  
  if (alreadySent) {
    logger.info('Daily report already sent today, skipping')
    return
  }
  
  const report = await generateReport(today)
  await emailService.send({
    to: 'team@example.com',
    subject: `Daily Report - ${today}`,
    body: report
  })
  
  // Log completion
  await db.jobLog.create({
    name: 'daily-report',
    date: today,
    status: 'completed'
  })
}
```

# MONITORING
```typescript
// Track job execution
async function runWithMonitoring(jobName: string, fn: () => Promise<void>) {
  const start = Date.now()
  
  await db.jobExecution.create({
    name: jobName,
    startedAt: new Date(),
    status: 'running'
  })
  
  try {
    await fn()
    
    await db.jobExecution.updateMany({
      where: { name: jobName, status: 'running' },
      data: {
        completedAt: new Date(),
        status: 'success',
        duration: Date.now() - start
      }
    })
  } catch (error) {
    await db.jobExecution.updateMany({
      where: { name: jobName, status: 'running' },
      data: {
        completedAt: new Date(),
        status: 'failed',
        error: error.message,
        duration: Date.now() - start
      }
    })
    
    // Alert on failure
    await alerting.notify({
      severity: 'warning',
      message: `Job ${jobName} failed: ${error.message}`
    })
    
    throw error
  }
}
```

# REVIEW CHECKLIST
```
[ ] Cron expressions validated and documented
[ ] Jobs are idempotent (safe to rerun)
[ ] Overlapping executions prevented (locking)
[ ] Errors logged and alerted
[ ] Execution history tracked
[ ] Timezone explicitly specified
[ ] Job timeouts configured
[ ] Retry logic for transient failures
[ ] Resource usage monitored
```
