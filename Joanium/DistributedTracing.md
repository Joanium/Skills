---
name: Distributed Tracing
trigger: distributed tracing, request tracing, opentelemetry, jaeger, zipkin, trace context, span, observability tracing, microservice tracing
description: Implement distributed tracing across microservices using OpenTelemetry, Jaeger, or Zipkin. Covers trace context propagation, span creation, sampling, and trace analysis. Use when debugging microservices, implementing observability, or tracking requests across services.
---

# ROLE
You are an observability engineer specializing in distributed tracing. Your job is to implement tracing that provides end-to-end visibility into requests as they flow through multiple services.

# OPENTELEMETRY SETUP
```typescript
import { NodeSDK } from '@opentelemetry/sdk-node'
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node'
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http'

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({
    url: 'http://jaeger:4318/v1/traces'
  }),
  instrumentations: [getNodeAutoInstrumentations()],
  serviceName: 'order-service'
})

sdk.start()
```

# MANUAL INSTRUMENTATION
```typescript
import { trace, context, SpanStatusCode } from '@opentelemetry/api'

const tracer = trace.getTracer('order-service')

async function processOrder(orderId: string) {
  return tracer.startActiveSpan('processOrder', async (span) => {
    span.setAttribute('order.id', orderId)
    span.setAttribute('order.source', 'web')
    
    try {
      const inventory = await checkInventory(orderId)
      span.addEvent('inventory-checked', { 
        'inventory.available': inventory.available 
      })
      
      const payment = await chargePayment(orderId)
      span.addEvent('payment-charged', {
        'payment.amount': payment.amount,
        'payment.method': payment.method
      })
      
      span.setStatus({ code: SpanStatusCode.OK })
      return { success: true, orderId }
    } catch (error) {
      span.setStatus({ code: SpanStatusCode.ERROR })
      span.recordException(error)
      throw error
    } finally {
      span.end()
    }
  })
}
```

# CONTEXT PROPAGATION
```typescript
// HTTP client — inject trace context
import { propagation } from '@opentelemetry/api'

async function callUserService(orderId: string) {
  const headers: Record<string, string> = {}
  propagation.inject(context.active(), headers)
  
  const response = await fetch('http://user-service/api/users', {
    headers
  })
  
  return response.json()
}

// HTTP server — extract trace context
import { context, trace } from '@opentelemetry/api'

app.use((req, res, next) => {
  const extracted = propagation.extract(context.active(), req.headers)
  context.with(extracted, () => {
    next()
  })
})
```

# SAMPLING
```typescript
import { ParentBasedSampler, TraceIdRatioBasedSampler } from '@opentelemetry/sdk-trace-node'

// Sample 10% of requests
const sampler = new ParentBasedSampler({
  root: new TraceIdRatioBasedSampler(0.1)
})

// Always sample errors
const sampler = new ParentBasedSampler({
  root: new TraceIdRatioBasedSampler(0.1),
  parentSampled: new AlwaysOnSampler()
})
```

# TRACE ANALYSIS
```
Key metrics from traces:
- End-to-end latency (root span duration)
- Per-service latency (child span durations)
- Error rates by service
- Critical path (longest chain of dependent spans)
- Fan-out (parallel service calls)

Common patterns to identify:
- Slow database queries
- Unnecessary sequential calls (could be parallel)
- External service latency spikes
- Retry storms
```

# REVIEW CHECKLIST
```
[ ] OpenTelemetry SDK configured in all services
[ ] Trace context propagated across service boundaries
[ ] Key operations instrumented with spans
[ ] Attributes added for business context
[ ] Errors recorded on spans
[ ] Sampling configured for production volume
[ ] Trace collector/deployed (Jaeger, Zipkin, etc.)
[ ] Trace IDs included in structured logs
```
