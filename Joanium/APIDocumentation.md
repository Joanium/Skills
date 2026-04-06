---
name: API Documentation
trigger: api documentation, document my api, openapi spec, swagger, api docs, write api docs, api reference, api guide, document endpoints, api spec, developer docs, rest api docs, api documentation best practices
description: Write excellent API documentation — OpenAPI specs, developer guides, reference docs, and authentication guides — that help developers integrate quickly and successfully. Use when launching an API, onboarding external developers, or improving existing docs.
---

Good API documentation is a product. Developers form opinions about your API in the first 15 minutes. If they can't get a working request in that time, most will leave. The goal is not completeness — it's speed to first successful API call, and clarity for every call after that.

## Documentation Architecture

A complete API documentation suite has distinct layers:

```
1. Getting Started Guide    → First request in < 5 minutes
2. Authentication Guide     → Clear, with working examples
3. Quick Start / Tutorials  → Common use cases, end-to-end
4. API Reference            → Every endpoint, parameter, and response
5. Error Reference          → Every error code, what it means, how to fix it
6. Changelog                → What changed, when, and what to update
7. SDK documentation        → Language-specific guides (if you have SDKs)
```

**The Getting Started Guide is the most important document you will write.**  
Everyone reads it. Most read only it. Make it exceptional.

## The Getting Started Guide

### Structure that works:
```markdown
# Getting Started with [API Name]

## Prerequisites
- An API key ([get one here](link-to-dashboard))
- curl (or [Postman collection](link) / [SDK](link))

## Your first API call

Replace `YOUR_API_KEY` with your actual key and run:

```bash
curl https://api.example.com/v1/users \
  -H "Authorization: Bearer YOUR_API_KEY"
```

You should see:
```json
{
  "data": [
    { "id": "usr_abc123", "email": "alice@example.com", "name": "Alice" }
  ],
  "meta": { "total": 1, "page": 1 }
}
```

If you see an error, check [common authentication errors](#auth-errors).

## Next steps
- [Create your first resource](link)
- [Understand pagination](link)
- [Handle webhooks](link)
```

Key principles for Getting Started:
- Working code in the first 100 words
- Real output, not `{ "result": "..." }`  
- An explicit "if this didn't work" path
- No explanation of architecture before the working example

## OpenAPI Specification (the canonical reference)

OpenAPI is the standard format — write it well and tooling (Swagger UI, Redoc, Postman) generates docs automatically.

### Full endpoint example
```yaml
# openapi.yaml
openapi: 3.1.0
info:
  title: Payments API
  version: 2.0.0
  description: |
    Process payments, manage subscriptions, and issue refunds.
    
    **Base URL:** `https://api.example.com/v2`
    
    **Authentication:** Bearer token in the `Authorization` header.
    See [Authentication](./authentication.md) for obtaining tokens.
  contact:
    name: API Support
    email: api-support@example.com
    url: https://docs.example.com

servers:
  - url: https://api.example.com/v2
    description: Production
  - url: https://sandbox.example.com/v2
    description: Sandbox (use test cards, no real charges)

paths:
  /charges:
    post:
      operationId: createCharge
      summary: Create a charge
      description: |
        Charge a payment method for a specified amount.
        
        The charge is processed immediately. For authorization-only (charge later),
        use `capture: false` and call [Capture Charge](#captureCharge) later.
        
        **Idempotency:** Pass an `Idempotency-Key` header to safely retry
        without double-charging. The same key returns the same response for 24 hours.
      tags: [Charges]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateChargeRequest'
            examples:
              basic_charge:
                summary: Simple credit card charge
                value:
                  amount: 2000
                  currency: "usd"
                  payment_method: "pm_card_visa"
                  description: "Order #1234"
              capture_later:
                summary: Authorize only, capture later
                value:
                  amount: 5000
                  currency: "usd"
                  payment_method: "pm_card_visa"
                  capture: false
      responses:
        '201':
          description: Charge created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Charge'
              examples:
                success:
                  value:
                    id: "ch_abc123"
                    amount: 2000
                    currency: "usd"
                    status: "succeeded"
                    created_at: "2024-03-15T10:30:00Z"
        '400':
          $ref: '#/components/responses/BadRequest'
        '402':
          description: Payment failed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
              example:
                error:
                  code: "card_declined"
                  message: "Your card was declined."
                  decline_code: "insufficient_funds"
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimited'

components:
  schemas:
    CreateChargeRequest:
      type: object
      required: [amount, currency, payment_method]
      properties:
        amount:
          type: integer
          description: |
            Amount in the **smallest currency unit** (cents for USD, pence for GBP).
            For $20.00 USD, pass `2000`.
          example: 2000
          minimum: 50
        currency:
          type: string
          description: ISO 4217 currency code, lowercase.
          example: usd
          enum: [usd, eur, gbp, cad, aud]
        payment_method:
          type: string
          description: |
            Payment method ID from [Create Payment Method](#createPaymentMethod).
            Use test IDs in sandbox: `pm_card_visa`, `pm_card_mastercard_declined`.
          example: pm_card_visa
        capture:
          type: boolean
          default: true
          description: |
            Set to `false` to only authorize the charge (hold the funds).
            Capture within 7 days or the authorization expires.
        description:
          type: string
          maxLength: 500
          description: Internal description. Not shown to the customer.
          example: "Order #1234"
        metadata:
          type: object
          additionalProperties:
            type: string
          description: |
            Up to 20 key-value pairs for your own reference.
            Keys up to 40 chars, values up to 500 chars.
          example:
            order_id: "ord_789"
            customer_name: "Alice Smith"

  responses:
    BadRequest:
      description: Invalid request parameters
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    Unauthorized:
      description: Missing or invalid API key
    RateLimited:
      description: Too many requests
      headers:
        Retry-After:
          schema:
            type: integer
          description: Seconds to wait before retrying

  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      description: API key obtained from your dashboard.

security:
  - BearerAuth: []
```

## Error Documentation

This is the most neglected section. Do it well and you'll save hours of developer support tickets.

```markdown
# Error Reference

All errors follow a consistent shape:
```json
{
  "error": {
    "code": "machine_readable_code",
    "message": "Human readable explanation.",
    "param": "the_invalid_field",  // when applicable
    "doc_url": "https://docs.example.com/errors#machine_readable_code"
  }
}
```

## Error Codes

### Authentication errors

| Code | HTTP | Meaning | How to fix |
|------|------|---------|------------|
| `invalid_api_key` | 401 | The API key is wrong or expired | Check your key in the dashboard. Keys start with `sk_live_` in production, `sk_test_` in sandbox. |
| `api_key_expired` | 401 | The key has been rotated | Generate a new key in the dashboard and update your server. |
| `insufficient_permissions` | 403 | The key doesn't have access to this endpoint | Your key is a restricted key. Enable the required permission in the dashboard. |

### Charge errors

| Code | HTTP | Meaning | How to fix |
|------|------|---------|------------|
| `card_declined` | 402 | Card declined by the issuer | Check `decline_code` for specifics. Show the customer a generic error; don't display `decline_code` to them. |
| `insufficient_funds` | 402 | Decline code: not enough funds | Ask the customer to use a different card. |
| `expired_card` | 402 | Card expiration date is in the past | Ask the customer to update their card. |
| `amount_too_small` | 400 | Amount below minimum ($0.50) | Minimum charge is 50 cents (or equivalent). |
| `idempotency_conflict` | 409 | Same idempotency key, different params | Do not reuse idempotency keys with different parameters. Generate a new key per unique request. |
```

## Code Examples — The Most Valuable Documentation

For every meaningful endpoint, provide examples in at least 3 languages:

```markdown
## Create a Charge

<Tabs>
<Tab label="curl">
```bash
curl https://api.example.com/v2/charges \
  -X POST \
  -H "Authorization: Bearer sk_test_..." \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 2000,
    "currency": "usd",
    "payment_method": "pm_card_visa",
    "description": "Order #1234"
  }'
```
</Tab>
<Tab label="Node.js">
```javascript
const response = await fetch('https://api.example.com/v2/charges', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${process.env.EXAMPLE_API_KEY}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    amount: 2000,
    currency: 'usd',
    payment_method: 'pm_card_visa',
    description: 'Order #1234',
  }),
});

const charge = await response.json();
console.log(charge.id); // ch_abc123
```
</Tab>
<Tab label="Python">
```python
import httpx

response = httpx.post(
    "https://api.example.com/v2/charges",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "amount": 2000,
        "currency": "usd",
        "payment_method": "pm_card_visa",
        "description": "Order #1234",
    }
)

charge = response.json()
print(charge["id"])  # ch_abc123
```
</Tab>
</Tabs>
```

## Documentation Checklist

```
Getting started:
☐ Working first request in < 5 minutes possible?
☐ Real response shown (not placeholders)?
☐ "If this failed" path provided?
☐ Link to sandbox/test environment with test credentials?

API reference (per endpoint):
☐ Every parameter has a type, description, and example?
☐ Required vs optional clearly marked?
☐ Multiple request/response examples (not just the happy path)?
☐ Every error response documented with how to fix it?
☐ Rate limits noted where applicable?

Overall:
☐ Authentication documented with real examples?
☐ Pagination documented for all list endpoints?
☐ Idempotency documented for mutation endpoints?
☐ Webhook payload format documented?
☐ Changelog maintained with dates?
☐ Tested: can a new engineer reach "Hello World" in < 5 minutes?
☐ Error codes cross-referenced from both the reference and the errors page?
```
