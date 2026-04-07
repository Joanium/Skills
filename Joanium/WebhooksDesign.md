---
name: Webhooks Design
trigger: webhook, webhooks, receive webhook, webhook endpoint, webhook signature, stripe webhook, github webhook, webhook retry, webhook queue, inbound webhook, webhook verification, webhook handler
description: Design, receive, verify, and process webhooks reliably. Covers signature verification, idempotency, async processing, retry handling, and debugging incoming webhook payloads.
---

# ROLE
You are a senior backend engineer. Your job is to build webhook receivers that never lose events, never process duplicates, and recover gracefully from failures. Webhooks are fire-and-forget from the sender's side — your receiver must be bulletproof.

# CORE PRINCIPLES
```
VERIFY FIRST:     Always verify the signature before processing anything
RESPOND FAST:     Return 200 immediately, process async — don't make sender wait
IDEMPOTENT:       Same event delivered twice must not cause duplicate side effects
QUEUE IT:         Never do heavy work in the webhook handler — push to queue
LOG EVERYTHING:   Store raw payload, headers, and processing result for debugging
```

# SIGNATURE VERIFICATION

## HMAC-SHA256 (Stripe, GitHub, most providers)
```javascript
import crypto from 'crypto';

function verifyWebhookSignature(rawBody, signature, secret) {
  // rawBody MUST be the raw Buffer — not parsed JSON
  const expected = crypto
    .createHmac('sha256', secret)
    .update(rawBody)
    .digest('hex');
  
  const received = signature.replace('sha256=', '');  // GitHub prefix

  // Use timingSafeEqual to prevent timing attacks
  return crypto.timingSafeEqual(
    Buffer.from(expected, 'hex'),
    Buffer.from(received, 'hex')
  );
}

// Express — CRITICAL: use raw body parser for webhook routes
app.post('/webhooks/github',
  express.raw({ type: 'application/json' }),  // ← raw, not json()
  (req, res) => {
    const sig = req.headers['x-hub-signature-256'];
    if (!sig || !verifyWebhookSignature(req.body, sig, process.env.GITHUB_WEBHOOK_SECRET)) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
    const payload = JSON.parse(req.body.toString());
    // process...
    res.status(200).json({ received: true });
  }
);
```

## Stripe Webhook Verification
```javascript
import Stripe from 'stripe';
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

app.post('/webhooks/stripe',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    const sig = req.headers['stripe-signature'];
    let event;

    try {
      event = stripe.webhooks.constructEvent(
        req.body,
        sig,
        process.env.STRIPE_WEBHOOK_SECRET
      );
    } catch (err) {
      return res.status(400).json({ error: `Webhook Error: ${err.message}` });
    }

    // Acknowledge immediately
    res.status(200).json({ received: true });

    // Process async
    await processStripeEvent(event);
  }
);
```

## Timestamp Replay Attack Prevention
```javascript
function verifyWithTimestamp(rawBody, signatureHeader, secret, toleranceSeconds = 300) {
  // Stripe format: t=1492774577,v1=abc123
  const parts = signatureHeader.split(',');
  const timestamp = parseInt(parts.find(p => p.startsWith('t=')).slice(2));
  const signature = parts.find(p => p.startsWith('v1=')).slice(3);

  // Check timestamp freshness
  const now = Math.floor(Date.now() / 1000);
  if (Math.abs(now - timestamp) > toleranceSeconds) {
    throw new Error('Webhook timestamp too old — possible replay attack');
  }

  const signedPayload = `${timestamp}.${rawBody}`;
  const expected = crypto.createHmac('sha256', secret).update(signedPayload).digest('hex');
  
  return crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(signature));
}
```

# IDEMPOTENCY

## Deduplication with Event ID
```javascript
// Store processed event IDs (Redis recommended — TTL of 24h)
async function processWebhookIdempotent(eventId, payload, handler) {
  const key = `webhook:processed:${eventId}`;
  
  // Check if already processed
  const alreadyProcessed = await redis.get(key);
  if (alreadyProcessed) {
    console.log(`Duplicate event ${eventId} — skipping`);
    return { duplicate: true };
  }

  // Process the event
  const result = await handler(payload);

  // Mark as processed (expire after 24h)
  await redis.setex(key, 86400, JSON.stringify({ processedAt: Date.now(), result }));
  
  return result;
}

// Usage
app.post('/webhooks/stripe', express.raw({ type: 'application/json' }), async (req, res) => {
  const event = stripe.webhooks.constructEvent(req.body, req.headers['stripe-signature'], secret);
  res.status(200).json({ received: true });
  
  await processWebhookIdempotent(event.id, event, handleStripeEvent);
});
```

## Database-Level Idempotency
```sql
-- Store webhook events in DB with unique constraint
CREATE TABLE webhook_events (
  id          TEXT PRIMARY KEY,   -- provider's event ID
  source      TEXT NOT NULL,      -- 'stripe', 'github', etc.
  event_type  TEXT NOT NULL,
  payload     JSONB NOT NULL,
  status      TEXT DEFAULT 'pending',  -- pending, processing, done, failed
  received_at TIMESTAMPTZ DEFAULT NOW(),
  processed_at TIMESTAMPTZ,
  error       TEXT
);

-- Upsert — skip if already exists
INSERT INTO webhook_events (id, source, event_type, payload)
VALUES ($1, $2, $3, $4)
ON CONFLICT (id) DO NOTHING
RETURNING *;
```

# ASYNC PROCESSING

## Queue Pattern (BullMQ / Redis)
```javascript
import { Queue, Worker } from 'bullmq';

const webhookQueue = new Queue('webhooks', { connection: redis });

// Webhook endpoint — just enqueue and return 200
app.post('/webhooks/:source',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    const verified = verifySignature(req.source, req.body, req.headers);
    if (!verified) return res.status(401).end();

    const payload = JSON.parse(req.body.toString());

    // Enqueue with retry config
    await webhookQueue.add('process', {
      source: req.params.source,
      eventId: payload.id,
      eventType: payload.type,
      payload,
    }, {
      attempts: 5,
      backoff: { type: 'exponential', delay: 2000 },
    });

    res.status(200).json({ received: true });  // immediate response
  }
);

// Worker processes asynchronously
const worker = new Worker('webhooks', async (job) => {
  const { source, eventType, payload } = job.data;
  
  const handlers = {
    'payment_intent.succeeded': handlePaymentSucceeded,
    'customer.subscription.deleted': handleSubscriptionCancelled,
    'invoice.payment_failed': handlePaymentFailed,
  };

  const handler = handlers[eventType];
  if (!handler) {
    console.warn(`No handler for event type: ${eventType}`);
    return;
  }

  await handler(payload);
}, { connection: redis });

worker.on('failed', (job, err) => {
  console.error(`Webhook job ${job.id} failed:`, err.message);
  // Alert if exhausted all retries
  if (job.attemptsMade === job.opts.attempts) {
    alertTeam(`Webhook permanently failed: ${job.data.eventType}`, err);
  }
});
```

# COMMON WEBHOOK EVENT HANDLERS

## Stripe Events
```javascript
async function handleStripeEvent(event) {
  switch (event.type) {
    case 'payment_intent.succeeded': {
      const pi = event.data.object;
      await db.orders.update({ stripePaymentIntentId: pi.id }, { status: 'paid' });
      await sendReceiptEmail(pi.metadata.userId);
      break;
    }
    case 'customer.subscription.created':
    case 'customer.subscription.updated': {
      const sub = event.data.object;
      await db.subscriptions.upsert({ stripeSubscriptionId: sub.id }, {
        status: sub.status,
        currentPeriodEnd: new Date(sub.current_period_end * 1000),
        planId: sub.items.data[0].price.id,
      });
      break;
    }
    case 'customer.subscription.deleted': {
      const sub = event.data.object;
      await db.subscriptions.update({ stripeSubscriptionId: sub.id }, { status: 'cancelled' });
      break;
    }
    default:
      console.log(`Unhandled Stripe event: ${event.type}`);
  }
}
```

## GitHub Events
```javascript
async function handleGitHubEvent(event, payload) {
  switch (event) {
    case 'push': {
      const { repository, commits, ref } = payload;
      if (ref === 'refs/heads/main') {
        await triggerDeployment(repository.name, commits[0].id);
      }
      break;
    }
    case 'pull_request': {
      if (payload.action === 'opened' || payload.action === 'synchronize') {
        await runCIChecks(payload.pull_request);
      }
      break;
    }
    case 'issues': {
      if (payload.action === 'opened') {
        await notifyTeam(payload.issue);
      }
      break;
    }
  }
}
```

# DEBUGGING & TESTING
```
Local development:
  1. Use ngrok / cloudflared to expose localhost:
     ngrok http 3000
     → https://abc123.ngrok.io

  2. Register the ngrok URL as webhook endpoint in provider dashboard

  3. Use provider's "resend" or "replay" feature to replay events

  4. Log all raw payloads:
     console.log(JSON.stringify({ headers: req.headers, body: payload }, null, 2));

Testing tools:
  - Stripe CLI:   stripe listen --forward-to localhost:3000/webhooks/stripe
  - GitHub:       Settings → Webhooks → Recent Deliveries → Redeliver
  - Webhook.site: https://webhook.site — inspect raw payloads before building handler

Always test:
  - Happy path (successful event)
  - Duplicate delivery (same event twice)
  - Old/replayed event (timestamp > tolerance)
  - Invalid signature (should 401)
  - Slow handler (should still 200 immediately)
```

# CHECKLIST
```
[ ] Signature verified before any processing
[ ] Raw body used for signature check (not parsed JSON)
[ ] 200 returned immediately, processing done async
[ ] Event IDs deduplicated (Redis or DB unique constraint)
[ ] Retry queue with exponential backoff configured
[ ] All raw payloads logged to storage for debugging
[ ] Dead-letter queue / alert for permanently failed events
[ ] Handler tested for all event types you care about
[ ] Replay attack prevention (timestamp check)
[ ] ngrok/cloudflared set up for local testing
```
