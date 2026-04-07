---
name: OpenTelemetry Observability
trigger: opentelemetry, otel, distributed tracing, spans, traces, metrics instrumentation, logs correlation, observability, jaeger, tempo, prometheus otel, trace context propagation, instrument my app, add tracing, otel sdk, otel collector
description: Instrument applications with OpenTelemetry for traces, metrics, and logs. Use this skill whenever the user wants to add observability to their app, asks about distributed tracing, span creation, context propagation, or wants to connect OpenTelemetry to a backend (Jaeger, Tempo, Prometheus, Datadog). Covers Node.js, Python, and Go.
---

# ROLE
You are an observability engineer. You instrument code with OpenTelemetry so that when production breaks at 3am, the team can trace requests end-to-end, find the bottleneck, and fix it without guessing.

# THE THREE SIGNALS

```
Traces   → "What happened during this request, and how long did each step take?"
Metrics  → "How is the system behaving over time? Error rate, latency, throughput"
Logs     → "What was the state of the system at this moment?"

OpenTelemetry unifies all three with a common SDK + collector.
```

# NODE.JS SETUP

```bash
npm install @opentelemetry/sdk-node \
            @opentelemetry/auto-instrumentations-node \
            @opentelemetry/exporter-trace-otlp-http \
            @opentelemetry/exporter-metrics-otlp-http \
            @opentelemetry/resources \
            @opentelemetry/semantic-conventions
```

```typescript
// instrumentation.ts — MUST load before anything else
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-http';
import { PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics';
import { Resource } from '@opentelemetry/resources';
import { SEMRESATTRS_SERVICE_NAME, SEMRESATTRS_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';

const sdk = new NodeSDK({
  resource: new Resource({
    [SEMRESATTRS_SERVICE_NAME]: 'order-service',
    [SEMRESATTRS_SERVICE_VERSION]: process.env.APP_VERSION ?? '0.0.1',
    environment: process.env.NODE_ENV ?? 'development',
  }),
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT ?? 'http://localhost:4318/v1/traces',
  }),
  metricReader: new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter({
      url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT ?? 'http://localhost:4318/v1/metrics',
    }),
    exportIntervalMillis: 10000,
  }),
  instrumentations: [
    getNodeAutoInstrumentations({
      '@opentelemetry/instrumentation-http': { enabled: true },
      '@opentelemetry/instrumentation-express': { enabled: true },
      '@opentelemetry/instrumentation-pg': { enabled: true },
      '@opentelemetry/instrumentation-redis': { enabled: true },
    }),
  ],
});

sdk.start();
process.on('SIGTERM', () => sdk.shutdown());

// package.json — load before app code
// "scripts": { "start": "node -r ./instrumentation.js dist/server.js" }
```

## Creating Custom Spans
```typescript
import { trace, context, SpanStatusCode, SpanKind } from '@opentelemetry/api';

const tracer = trace.getTracer('order-service', '1.0.0');

async function processOrder(orderId: string) {
  // Create a span wrapping the operation
  return tracer.startActiveSpan('processOrder', async (span) => {
    try {
      // Add attributes to the span (queryable in your tracing backend)
      span.setAttributes({
        'order.id': orderId,
        'order.source': 'web',
      });

      const order = await fetchOrder(orderId);
      span.setAttribute('order.total_cents', order.totalCents);

      // Nested spans for sub-operations
      const payment = await tracer.startActiveSpan('chargePayment', async (paymentSpan) => {
        paymentSpan.setAttribute('payment.gateway', 'stripe');
        try {
          const result = await stripe.charge(order);
          paymentSpan.setStatus({ code: SpanStatusCode.OK });
          return result;
        } catch (err) {
          paymentSpan.recordException(err as Error);
          paymentSpan.setStatus({ code: SpanStatusCode.ERROR, message: (err as Error).message });
          throw err;
        } finally {
          paymentSpan.end();
        }
      });

      // Add events (timestamped annotations on the span)
      span.addEvent('payment.charged', { 'payment.id': payment.id });

      span.setStatus({ code: SpanStatusCode.OK });
      return { orderId, paymentId: payment.id };
    } catch (err) {
      span.recordException(err as Error);
      span.setStatus({ code: SpanStatusCode.ERROR });
      throw err;
    } finally {
      span.end();
    }
  });
}
```

## Custom Metrics
```typescript
import { metrics } from '@opentelemetry/api';

const meter = metrics.getMeter('order-service', '1.0.0');

// Counter — things that go up (requests, errors, orders)
const orderCounter = meter.createCounter('orders.created', {
  description: 'Number of orders created',
  unit: '{orders}',
});
orderCounter.add(1, { 'order.type': 'subscription', 'order.region': 'us-east' });

// Histogram — measure distributions (latency, sizes)
const paymentDuration = meter.createHistogram('payment.duration', {
  description: 'Time to charge a payment',
  unit: 'ms',
});
const start = Date.now();
await chargePayment();
paymentDuration.record(Date.now() - start, { 'payment.gateway': 'stripe' });

// Gauge — current value (queue depth, cache size)
const queueDepth = meter.createObservableGauge('queue.depth', {
  description: 'Number of items in the processing queue',
});
queueDepth.addCallback(result => {
  result.observe(getCurrentQueueDepth(), { 'queue.name': 'orders' });
});
```

# PYTHON SETUP

```bash
pip install opentelemetry-sdk \
            opentelemetry-instrumentation-fastapi \
            opentelemetry-instrumentation-sqlalchemy \
            opentelemetry-instrumentation-httpx \
            opentelemetry-exporter-otlp
```

```python
# telemetry.py
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

def setup_telemetry():
    resource = Resource({
        ResourceAttributes.SERVICE_NAME: "order-service",
        ResourceAttributes.SERVICE_VERSION: "1.0.0",
    })
    
    # Traces
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces"))
    )
    trace.set_tracer_provider(tracer_provider)
    
    # Metrics
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint="http://localhost:4318/v1/metrics"), 
        export_interval_millis=10000
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

# main.py (FastAPI)
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

setup_telemetry()
app = FastAPI()
FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=engine)

# Custom span in Python
tracer = trace.get_tracer(__name__)

def process_order(order_id: str):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)
        try:
            result = charge_payment(order_id)
            return result
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR)
            raise
```

# OTEL COLLECTOR (PRODUCTION)

```yaml
# docker-compose.yml
otel-collector:
  image: otel/opentelemetry-collector-contrib:latest
  command: ["--config=/etc/otel-collector.yaml"]
  volumes:
    - ./otel-collector.yaml:/etc/otel-collector.yaml
  ports:
    - "4318:4318"   # OTLP HTTP
    - "4317:4317"   # OTLP gRPC
```

```yaml
# otel-collector.yaml
receivers:
  otlp:
    protocols:
      http:
        endpoint: 0.0.0.0:4318
      grpc:
        endpoint: 0.0.0.0:4317

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024
  memory_limiter:
    limit_mib: 256
  resource:
    attributes:
      - action: insert
        key: deployment.environment
        value: production

exporters:
  # Send traces to Tempo/Jaeger
  otlp/tempo:
    endpoint: "http://tempo:4317"
    tls:
      insecure: true
  
  # Send metrics to Prometheus
  prometheus:
    endpoint: "0.0.0.0:8889"
    namespace: myapp
  
  # Send to Datadog
  datadog:
    api:
      key: ${DD_API_KEY}
      site: datadoghq.com

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch, resource]
      exporters: [otlp/tempo]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus]
```

# CONNECTING TRACES TO LOGS

```typescript
// Inject trace context into log entries
import { trace, context } from '@opentelemetry/api';
import winston from 'winston';

const logger = winston.createLogger({
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json(),
    winston.format((info) => {
      // Add trace context to every log entry
      const span = trace.getActiveSpan();
      if (span) {
        const ctx = span.spanContext();
        info.traceId = ctx.traceId;
        info.spanId = ctx.spanId;
      }
      return info;
    })()
  ),
  transports: [new winston.transports.Console()],
});

// Now logs have { traceId, spanId } — Grafana can link logs to traces automatically
```

# SEMANTIC CONVENTIONS (USE THESE — DON'T INVENT)

```
HTTP:      http.method, http.status_code, http.url, http.user_agent
DB:        db.system, db.name, db.statement, db.operation
RPC:       rpc.system, rpc.service, rpc.method
Messaging: messaging.system, messaging.destination, messaging.operation
Errors:    exception.type, exception.message, exception.stacktrace

These are standardized — your traces will work with any backend that understands OTEL.
```
