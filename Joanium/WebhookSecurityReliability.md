---
name: Webhook Security and Reliability
trigger: webhook design, webhook security, webhook signature, webhook delivery, webhook retry, webhook verification, webhook payload, reliable webhooks, webhook best practices, outbound webhooks
description: Design and implement reliable, secure webhook systems. Covers payload signing, signature verification, retry logic, delivery guarantees, consumer best practices, and monitoring.
---

# ROLE
You are a senior backend engineer building webhook infrastructure. Webhooks are fire-and-forget distributed calls — the hardest part isn't sending them, it's delivering them reliably, securely, and in a way consumers can trust.

# CORE PRINCIPLES
```
SIGN EVERY PAYLOAD:   Consumers must be able to verify the webhook came from you.
AT-LEAST-ONCE:        Deliver with retries. Consumers must be idempotent.
ASYNC RECEIPT:        Consumer should return 200 immediately, process asynchronously.
OBSERVABLE:           Every delivery attempt logged. Consumers can replay.
SMALL, TYPED EVENTS:  One event type per webhook. Stable schema with versioning.
```

# PAYLOAD DESIGN
```json
{
  "id": "evt_01HX2J3K4L5M",          // unique event ID (for idempotency)
  "type": "order.completed",          // event type — dot-namespaced
  "apiVersion": "2024-01-01",         // the API version that generated this event
  "createdAt": "2024-01-15T10:30:00Z",
  "livemode": true,                   // false for test/sandbox events
  "data": {
    "object": {
      "id": "ord_01HX2J3K4L",
      "status": "completed",
      "total": 4999,
      "currency": "usd",
      "customerId": "cust_01HX2J3K"
    },
    "previousAttributes": {           // what changed (for update events)
      "status": "pending"
    }
  }
}

// Event type naming: resource.action
// Examples:
//   order.created, order.completed, order.cancelled
//   user.created, user.updated, user.deleted
//   payment.succeeded, payment.failed, payment.refunded
//   subscription.renewed, subscription.cancelled

// Keep payload small — include the resource, link for full details if needed
// Never include: passwords, raw card numbers, secrets
```

# SENDING WEBHOOKS — PRODUCER SIDE

## Signature Generation (HMAC-SHA256)
```typescript
import crypto from 'crypto';

function signPayload(payload: string, secret: string, timestamp: number): string {
  // Timestamp + payload to prevent replay attacks
  const signedContent = `${timestamp}.${payload}`;
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(signedContent);
  return `v1=${hmac.digest('hex')}`;
}

async function sendWebhook(endpoint: WebhookEndpoint, event: WebhookEvent): Promise<void> {
  const payload = JSON.stringify(event);
  const timestamp = Math.floor(Date.now() / 1000);
  const signature = signPayload(payload, endpoint.secret, timestamp);

  const response = await fetch(endpoint.url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-ID':        event.id,
      'X-Webhook-Timestamp': String(timestamp),
      'X-Webhook-Signature': signature,
    },
    body: payload,
    signal: AbortSignal.timeout(10_000),  // 10s timeout
  });

  await db.webhookDeliveries.create({
    eventId: event.id,
    endpointId: endpoint.id,
    statusCode: response.status,
    success: response.ok,
    attempt: 1,
    sentAt: new Date(),
  });

  if (!response.ok) {
    throw new WebhookDeliveryError(response.status, response.statusText);
  }
}
```

## Retry Logic with Exponential Backoff
```typescript
const RETRY_SCHEDULE = [
  5,          // 5 seconds
  30,         // 30 seconds
  60 * 2,     // 2 minutes
  60 * 5,     // 5 minutes
  60 * 30,    // 30 minutes
  60 * 60 * 2, // 2 hours
  60 * 60 * 5, // 5 hours
];  // 7 attempts over ~8 hours

async function scheduleWebhookRetry(
  deliveryId: string,
  attempt: number
): Promise<void> {
  if (attempt >= RETRY_SCHEDULE.length) {
    await db.webhookDeliveries.update(deliveryId, { status: 'permanently_failed' });
    await notifyEndpointOwner(deliveryId);  // email or dashboard alert
    return;
  }

  const delaySeconds = RETRY_SCHEDULE[attempt] * (1 + Math.random() * 0.1);  // +10% jitter
  await queue.enqueue('webhook.deliver', { deliveryId, attempt }, { delaySeconds });
}

// Queue worker
async function processWebhookDelivery({ deliveryId, attempt }: Job): Promise<void> {
  const delivery = await db.webhookDeliveries.findById(deliveryId);
  const endpoint = await db.webhookEndpoints.findById(delivery.endpointId);
  const event = await db.webhookEvents.findById(delivery.eventId);

  try {
    await sendWebhook(endpoint, event);
    await db.webhookDeliveries.update(deliveryId, {
      status: 'delivered',
      attempt,
      deliveredAt: new Date()
    });
  } catch (err) {
    await db.webhookDeliveries.update(deliveryId, {
      status: 'failed',
      attempt,
      errorMessage: err.message,
      statusCode: err.statusCode,
    });
    await scheduleWebhookRetry(deliveryId, attempt + 1);
  }
}
```

# RECEIVING WEBHOOKS — CONSUMER SIDE

## Signature Verification
```typescript
import crypto from 'crypto';

function verifyWebhookSignature(
  payload: string,
  signature: string,       // "v1=abc123"
  timestamp: string,       // Unix timestamp string
  secret: string,
  toleranceSeconds = 300   // reject if older than 5 minutes
): boolean {
  // 1. Check timestamp freshness (prevent replay attacks)
  const ts = parseInt(timestamp, 10);
  const now = Math.floor(Date.now() / 1000);
  if (Math.abs(now - ts) > toleranceSeconds) {
    throw new Error('Webhook timestamp too old — possible replay attack');
  }

  // 2. Recompute expected signature
  const signedContent = `${timestamp}.${payload}`;
  const expectedSig = crypto
    .createHmac('sha256', secret)
    .update(signedContent)
    .digest('hex');

  // 3. Compare using timing-safe equality (prevent timing attacks)
  const receivedSig = signature.replace('v1=', '');
  return crypto.timingSafeEqual(
    Buffer.from(expectedSig, 'hex'),
    Buffer.from(receivedSig, 'hex')
  );
}

// Express webhook endpoint
router.post('/webhooks/myservice', express.raw({ type: 'application/json' }), async (req, res) => {
  // IMPORTANT: use raw body, not parsed JSON — JSON.stringify(req.body) ≠ original payload

  const signature = req.headers['x-webhook-signature'] as string;
  const timestamp = req.headers['x-webhook-timestamp'] as string;
  const payload = req.body.toString('utf8');

  try {
    verifyWebhookSignature(payload, signature, timestamp, process.env.WEBHOOK_SECRET!);
  } catch (err) {
    return res.status(401).json({ error: 'Invalid webhook signature' });
  }

  const event = JSON.parse(payload);

  // CRITICAL: Return 200 IMMEDIATELY, process asynchronously
  // Never do slow work (DB writes, API calls) before responding
  res.status(200).send('OK');

  // Process in background
  processWebhookEvent(event).catch(err => {
    logger.error({ err, eventId: event.id }, 'Webhook processing failed');
  });
});
```

## Idempotent Processing
```typescript
async function processWebhookEvent(event: WebhookEvent): Promise<void> {
  // Idempotency check — event may be delivered multiple times
  const alreadyProcessed = await db.webhookEvents.exists({ externalId: event.id });
  if (alreadyProcessed) {
    logger.info({ eventId: event.id }, 'Duplicate webhook ignored');
    return;
  }

  // Record as received (upsert to handle concurrent deliveries)
  await db.webhookEvents.upsert({
    externalId: event.id,
    type: event.type,
    receivedAt: new Date(),
    status: 'processing',
  });

  try {
    switch (event.type) {
      case 'order.completed':
        await handleOrderCompleted(event.data.object);
        break;
      case 'payment.failed':
        await handlePaymentFailed(event.data.object);
        break;
      default:
        logger.info({ type: event.type }, 'Unknown webhook type — ignoring');
    }

    await db.webhookEvents.update({ externalId: event.id }, { status: 'processed' });
  } catch (err) {
    await db.webhookEvents.update({ externalId: event.id }, {
      status: 'failed',
      errorMessage: err.message
    });
    throw err;
  }
}
```

# DEVELOPER EXPERIENCE — WEBHOOK MANAGEMENT
```
Features for your webhook consumers:

ENDPOINT MANAGEMENT:
  POST   /webhooks                    Create an endpoint
  GET    /webhooks                    List endpoints
  PATCH  /webhooks/{id}               Update URL or enabled events
  DELETE /webhooks/{id}               Delete endpoint
  POST   /webhooks/{id}/test          Send a test event

EVENT CATALOG:
  GET /webhook-events                 List available event types with schema

DELIVERY HISTORY:
  GET /webhooks/{id}/deliveries       List recent delivery attempts
  GET /deliveries/{id}               Get delivery detail + request/response
  POST /deliveries/{id}/retry        Manually retry a failed delivery

REPLAY:
  POST /events/{id}/replay           Re-deliver an event to all endpoints
  POST /webhooks/{id}/replay         Re-deliver all events since timestamp to endpoint

Secret rotation (zero-downtime):
  POST /webhooks/{id}/rotate-secret  Returns new secret, old valid for 24h
  // During overlap: accept signatures from BOTH old and new secrets
```

# MONITORING & ALERTING
```
Metrics to track (per endpoint):
  delivery_success_rate         → Alert if < 95% over 1h
  delivery_p99_latency          → Alert if endpoint taking > 5s to respond
  permanently_failed_count      → Alert on any permanently failed deliveries
  queue_depth                   → Alert if delivery queue depth > 10k

Dashboard panels:
  - Delivery success rate (7d trend)
  - Events by type (volume over time)
  - Failed endpoints (sorted by error rate)
  - Retry queue depth (real-time)
  - Average consumer response time

Alerts:
  - Endpoint failure rate > 20% for 15 min → notify endpoint owner
  - Delivery queue depth > 50k → escalate (infrastructure issue)
  - Permanently failed event → notify consumer + log for replay
```

# SECURITY CHECKLIST
```
Producer (sending webhooks):
  [ ] Every payload signed with HMAC-SHA256 (or RS256)
  [ ] Timestamp included in signature to prevent replay attacks
  [ ] Per-endpoint unique secrets (not one global secret)
  [ ] Secrets rotatable with zero-downtime overlap window
  [ ] TLS enforced for all deliveries (reject http:// endpoints)
  [ ] No PII or secrets in webhook payloads
  [ ] Request timeout set (10s max — don't hang on slow consumers)

Consumer (receiving webhooks):
  [ ] Signature verified on every request (not just in production)
  [ ] Timestamp freshness checked (reject if > 5 minutes old)
  [ ] Raw body used for verification (not parsed JSON)
  [ ] 200 returned immediately, processing done asynchronously
  [ ] Idempotency check before processing (dedup by event ID)
  [ ] Webhook secret stored in vault (not environment variable in code)
```
