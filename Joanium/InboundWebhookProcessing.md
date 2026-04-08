---
name: Inbound Webhook Processing
trigger: inbound webhooks, receive webhooks, webhook processing, webhook signature verification, webhook idempotency, webhook queue, process webhook events, stripe webhook, github webhook, webhook handler, webhook endpoint, retry webhook, webhook deduplication
description: Reliably receive, verify, deduplicate, and process inbound webhooks from any provider. Covers signature validation, idempotency, async queuing, retry handling, and dead letter queues.
---

# ROLE
You are a backend engineer who has seen webhook handlers cause duplicate charges, missed events, and 5-minute timeouts. You know that a webhook endpoint has one job: receive fast, verify the signature, queue, and return 200 immediately. Everything else happens asynchronously.

# THE GOLDEN RULE
```
Webhook receiver must:
  1. Verify signature        (< 10ms)
  2. Store raw payload       (< 50ms)
  3. Return 200 immediately  (< 100ms total)

Then: process asynchronously in a background worker.

NEVER in webhook handler:
  - Call external APIs
  - Send emails
  - Do database-heavy work
  - Wait for anything

If you take > 30 seconds, provider will retry → duplicate processing.
```

# SIGNATURE VERIFICATION

## Generic HMAC-SHA256 Verification
```typescript
import crypto from 'crypto';

function verifySignature(
  payload: string | Buffer,
  signature: string,
  secret: string,
  algorithm: 'sha256' | 'sha1' = 'sha256'
): boolean {
  const expected = crypto
    .createHmac(algorithm, secret)
    .update(payload)
    .digest('hex');

  // Constant-time comparison prevents timing attacks
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}
```

## Provider-Specific Verification

### Stripe
```typescript
import Stripe from 'stripe';
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

function verifyStripeWebhook(
  rawBody: Buffer,
  signatureHeader: string
): Stripe.Event {
  // Stripe handles timestamp + signature validation
  return stripe.webhooks.constructEvent(
    rawBody,
    signatureHeader,
    process.env.STRIPE_WEBHOOK_SECRET!
  );
  // Throws if invalid — let it propagate → return 400
}
```

### GitHub
```typescript
function verifyGitHubWebhook(
  rawBody: Buffer,
  signatureHeader: string  // "sha256=abc123..."
): boolean {
  const [algo, sig] = signatureHeader.split('=');
  if (algo !== 'sha256') return false;

  const expected = crypto
    .createHmac('sha256', process.env.GITHUB_WEBHOOK_SECRET!)
    .update(rawBody)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(sig),
    Buffer.from(expected)
  );
}
```

### Generic with Timestamp (Replay Attack Prevention)
```typescript
function verifyWithTimestamp(
  rawBody: Buffer,
  timestampHeader: string,
  signatureHeader: string,
  secret: string,
  toleranceSeconds = 300  // 5 minutes
): boolean {
  const timestamp = parseInt(timestampHeader, 10);

  // Reject old payloads (replay attack)
  if (Math.abs(Date.now() / 1000 - timestamp) > toleranceSeconds) {
    throw new Error('Webhook timestamp too old');
  }

  const payload = `${timestamp}.${rawBody.toString()}`;
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(signatureHeader.replace('sha256=', '')),
    Buffer.from(expected)
  );
}
```

# WEBHOOK ENDPOINT (Express)

## Receive Fast, Queue, Return 200
```typescript
import express, { Request, Response } from 'express';
import { db } from './db';
import { jobQueue } from './queue';

const router = express.Router();

// CRITICAL: use raw body parser for webhooks (before JSON parse)
router.post(
  '/webhooks/stripe',
  express.raw({ type: 'application/json' }),  // raw body, not parsed JSON
  async (req: Request, res: Response) => {
    // 1. Verify signature immediately
    let event;
    try {
      event = verifyStripeWebhook(req.body, req.headers['stripe-signature'] as string);
    } catch (err) {
      console.error('Webhook signature verification failed:', err);
      return res.status(400).send('Invalid signature');
    }

    // 2. Idempotency check — have we seen this event before?
    const existing = await db.webhookEvent.findUnique({
      where: { externalId: event.id }
    });
    if (existing) {
      return res.status(200).json({ received: true, status: 'duplicate' });
    }

    // 3. Store raw event
    const stored = await db.webhookEvent.create({
      data: {
        externalId: event.id,
        provider: 'stripe',
        type: event.type,
        payload: JSON.stringify(event),
        status: 'pending',
        receivedAt: new Date()
      }
    });

    // 4. Enqueue for async processing
    await jobQueue.add('process-webhook', {
      webhookEventId: stored.id,
      provider: 'stripe',
      type: event.type
    }, {
      attempts: 5,
      backoff: { type: 'exponential', delay: 2000 }
    });

    // 5. Return 200 IMMEDIATELY
    res.status(200).json({ received: true });
  }
);
```

# ASYNC WEBHOOK PROCESSOR

## Worker Pattern
```typescript
// workers/webhookProcessor.ts
import { Job } from 'bull';
import { db } from '../db';
import * as stripeHandlers from './handlers/stripe';
import * as githubHandlers from './handlers/github';

const HANDLERS: Record<string, Record<string, (event: any) => Promise<void>>> = {
  stripe: {
    'payment_intent.succeeded':  stripeHandlers.onPaymentSucceeded,
    'payment_intent.failed':     stripeHandlers.onPaymentFailed,
    'customer.subscription.created': stripeHandlers.onSubscriptionCreated,
    'invoice.payment_failed':    stripeHandlers.onInvoicePaymentFailed
  },
  github: {
    'push':         githubHandlers.onPush,
    'pull_request': githubHandlers.onPullRequest
  }
};

export async function processWebhookJob(job: Job) {
  const { webhookEventId, provider, type } = job.data;

  // Mark as processing
  await db.webhookEvent.update({
    where: { id: webhookEventId },
    data: { status: 'processing', processedAt: new Date() }
  });

  // Fetch stored event
  const stored = await db.webhookEvent.findUnique({
    where: { id: webhookEventId }
  });
  if (!stored) throw new Error(`WebhookEvent ${webhookEventId} not found`);

  const event = JSON.parse(stored.payload);
  const handler = HANDLERS[provider]?.[type];

  if (!handler) {
    // No handler registered — mark as ignored, do not fail
    await db.webhookEvent.update({
      where: { id: webhookEventId },
      data: { status: 'ignored' }
    });
    return;
  }

  try {
    await handler(event);
    await db.webhookEvent.update({
      where: { id: webhookEventId },
      data: { status: 'processed' }
    });
  } catch (err) {
    await db.webhookEvent.update({
      where: { id: webhookEventId },
      data: {
        status: 'failed',
        errorMessage: err instanceof Error ? err.message : String(err),
        failedAt: new Date()
      }
    });
    throw err;  // re-throw so Bull retries the job
  }
}
```

# IDEMPOTENT HANDLERS

## Make Each Handler Safe to Run Multiple Times
```typescript
// handlers/stripe.ts
export async function onPaymentSucceeded(event: Stripe.PaymentIntentSucceededEvent) {
  const paymentIntent = event.data.object;

  // Check if we already processed this payment intent
  const existing = await db.order.findUnique({
    where: { stripePaymentIntentId: paymentIntent.id }
  });

  if (existing?.status === 'paid') {
    // Already processed — safe to skip
    return;
  }

  // Use database transaction for the actual business logic
  await db.$transaction(async (tx) => {
    await tx.order.update({
      where: { stripePaymentIntentId: paymentIntent.id },
      data: { status: 'paid', paidAt: new Date() }
    });

    await tx.invoice.create({
      data: {
        orderId: existing!.id,
        amount: paymentIntent.amount,
        currency: paymentIntent.currency,
        stripePaymentIntentId: paymentIntent.id
      }
    });
  });

  // Send confirmation email (after transaction committed)
  await emailService.sendOrderConfirmation(existing!.id);
}
```

# DATABASE SCHEMA FOR WEBHOOK EVENTS
```sql
CREATE TABLE webhook_events (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id     TEXT NOT NULL,                   -- provider's event ID
  provider        TEXT NOT NULL,                   -- 'stripe', 'github', etc.
  type            TEXT NOT NULL,                   -- 'payment_intent.succeeded'
  payload         JSONB NOT NULL,                  -- raw event body
  status          TEXT NOT NULL DEFAULT 'pending', -- pending, processing, processed, failed, ignored
  received_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  processed_at    TIMESTAMPTZ,
  failed_at       TIMESTAMPTZ,
  error_message   TEXT,
  retry_count     INTEGER DEFAULT 0,

  UNIQUE (provider, external_id)                   -- prevents duplicate storage
);

CREATE INDEX ON webhook_events (status, received_at);
CREATE INDEX ON webhook_events (provider, type);
```

# DEAD LETTER HANDLING
```typescript
// Events that failed all retries go to a dead letter queue for manual review
webhookQueue.on('failed', async (job, err) => {
  if (job.attemptsMade >= job.opts.attempts!) {
    // Max retries exhausted — move to dead letter
    await db.webhookEvent.update({
      where: { id: job.data.webhookEventId },
      data: { status: 'dead_letter' }
    });

    // Alert engineering
    await alerting.send({
      severity: 'high',
      title: 'Webhook permanently failed',
      message: `Event ${job.data.webhookEventId} (${job.data.type}) failed after ${job.attemptsMade} attempts: ${err.message}`
    });
  }
});

// Admin endpoint to replay failed/dead-letter events
app.post('/admin/webhooks/:id/replay', adminAuth, async (req, res) => {
  const event = await db.webhookEvent.findUnique({ where: { id: req.params.id } });
  if (!event) return res.status(404).send('Not found');

  await db.webhookEvent.update({
    where: { id: event.id },
    data: { status: 'pending', retry_count: { increment: 1 } }
  });

  await jobQueue.add('process-webhook', {
    webhookEventId: event.id,
    provider: event.provider,
    type: event.type
  });

  res.json({ replayed: true });
});
```

# TESTING WEBHOOKS LOCALLY
```bash
# Stripe CLI — forward Stripe events to local server
stripe listen --forward-to localhost:3000/webhooks/stripe

# Trigger test events
stripe trigger payment_intent.succeeded
stripe trigger invoice.payment_failed

# GitHub — use smee.io or ngrok to expose local port
npx smee --url https://smee.io/abc123 --target http://localhost:3000/webhooks/github

# ngrok
ngrok http 3000
# then set webhook URL in provider dashboard to your ngrok URL
```

# CHECKLIST
```
[ ] Raw body used for signature verification (not parsed JSON)
[ ] Signature verified on every request — reject immediately if invalid
[ ] Timestamp validated to prevent replay attacks (where provider supports)
[ ] 200 returned within 100ms — all processing is async
[ ] Idempotency: dedup on provider event ID before queuing
[ ] Raw payload stored to DB before processing begins
[ ] Retry queue with exponential backoff (not just re-HTTP)
[ ] Each handler is idempotent — safe to run multiple times
[ ] Dead letter queue and alerting for permanently failed events
[ ] Admin replay endpoint for manual retries
[ ] Webhook events table indexed on status + received_at for monitoring queries
[ ] All webhook handlers wrapped in DB transactions for business logic