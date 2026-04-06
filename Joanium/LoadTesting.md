---
name: Load Testing
trigger: load test, stress test, performance test, load testing, k6, jmeter, locust, spike test, soak test, how many users can my app handle, capacity planning, throughput test, benchmark my api, load test script
description: Design and execute load tests to understand system capacity, find breaking points, and validate performance targets. Use when launching a new feature, planning for traffic spikes, or validating SLOs.
---

Load testing answers a question your production logs cannot: "What happens when X times more users show up?" The answer is almost always surprising. Run the test before users do.

## Types of Load Tests — Pick the Right One

```
Test Type        Purpose                              Shape
─────────────────────────────────────────────────────────────────────
Smoke            Sanity check: does it work at all?   1-5 users, 1 min
Load             Normal + peak traffic validation     Ramp to target, hold
Stress           Find the breaking point              Ramp until it breaks
Spike            Sudden traffic surge                 Instant jump, hold, drop
Soak (Endurance) Memory leaks, degradation over time  Steady for 1–24 hours
Breakpoint       Exact capacity limit                 Increase until failure
```

**Start with smoke → load → stress.** Never stress test production without smoke testing first.

## Defining Success Before You Test

Write these down before writing a single test script:

```
SLO Targets:
- p50 response time < 100ms
- p95 response time < 500ms
- p99 response time < 2000ms
- Error rate < 0.1%
- Throughput > 500 req/s

Test parameters:
- Expected normal load: 200 concurrent users
- Expected peak load: 1000 concurrent users
- Traffic model: [constant / ramp / spike / realistic]
- Test duration: 30 minutes hold after ramp
- Target endpoints: [list the critical paths]

Critical user journeys (weight these):
40% — Browse catalog
30% — Search
20% — Add to cart / checkout
10% — Login / signup
```

## k6 — Recommended Tool for Modern Teams

k6 is JavaScript-based, developer-friendly, and integrates with CI/CD.

### Basic load test script
```javascript
// load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('error_rate');
const checkoutDuration = new Trend('checkout_duration');

export const options = {
  stages: [
    { duration: '2m', target: 100 },   // Ramp up
    { duration: '10m', target: 100 },  // Hold at normal load
    { duration: '2m', target: 500 },   // Ramp to peak
    { duration: '10m', target: 500 },  // Hold at peak
    { duration: '2m', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<2000'],
    http_req_failed: ['rate<0.01'],
    error_rate: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'https://staging.example.com';

// Realistic user session
export default function () {
  // 1. Browse catalog
  const catalogRes = http.get(`${BASE_URL}/api/products`);
  check(catalogRes, {
    'catalog: status 200': (r) => r.status === 200,
    'catalog: has products': (r) => r.json('data').length > 0,
  });
  errorRate.add(catalogRes.status !== 200);
  sleep(1);

  // 2. View product
  const productId = catalogRes.json('data')[0].id;
  const productRes = http.get(`${BASE_URL}/api/products/${productId}`);
  check(productRes, { 'product: status 200': (r) => r.status === 200 });
  sleep(2);

  // 3. Add to cart (20% of users)
  if (Math.random() < 0.2) {
    const start = Date.now();
    const cartRes = http.post(
      `${BASE_URL}/api/cart`,
      JSON.stringify({ productId, quantity: 1 }),
      { headers: { 'Content-Type': 'application/json' } }
    );
    checkoutDuration.add(Date.now() - start);
    check(cartRes, { 'cart: status 201': (r) => r.status === 201 });
  }

  sleep(Math.random() * 3 + 1); // Think time: 1-4 seconds
}
```

### Running k6
```bash
# Install
brew install k6  # macOS
# or: docker run grafana/k6

# Run locally
k6 run load-test.js

# Run with env vars
BASE_URL=https://staging.example.com k6 run load-test.js

# Run with output to InfluxDB + Grafana
k6 run --out influxdb=http://localhost:8086/k6 load-test.js

# Stress test (ramp until it breaks)
k6 run --vus 10 --duration 30s load-test.js  # quick smoke
```

## Stress Test Pattern
```javascript
export const options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 100 },
    { duration: '2m', target: 500 },
    { duration: '5m', target: 500 },
    { duration: '2m', target: 1000 },  // Keep going...
    { duration: '5m', target: 1000 },
    { duration: '2m', target: 2000 },  // Until something breaks
    { duration: '5m', target: 2000 },
    { duration: '5m', target: 0 },     // Recovery — does it recover?
  ],
};
```

## Spike Test Pattern
```javascript
export const options = {
  stages: [
    { duration: '1m', target: 10 },    // Normal
    { duration: '30s', target: 1000 }, // SPIKE — sudden surge
    { duration: '5m', target: 1000 },  // Spike sustained
    { duration: '30s', target: 10 },   // Drop back
    { duration: '3m', target: 10 },    // Recovery period
  ],
};
```

## What to Monitor During the Test

Open these dashboards BEFORE you start:

```
Application metrics:
- Request rate (RPS)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx separately)
- Active connections

Infrastructure:
- CPU utilization (per service)
- Memory usage (watch for steady growth = leak)
- Network I/O (saturation?)

Database:
- Active connections (hitting pool limit?)
- Query latency (p95)
- Replication lag (if read replicas)
- Lock waits

Application-specific:
- Queue depth (are background jobs falling behind?)
- Cache hit rate (does it drop under load?)
- External API call rate + error rate
```

## Interpreting Results

### Reading the k6 summary
```
scenarios: (100.00%) 1 scenario, 500 max VUs
default: Up to 500 looping VUs for 26m0s

✓ catalog: status 200
✗ cart: status 201         ← FAILING CHECK — investigate
  ↳ 8% failures             ← 8% of cart adds failed at peak

http_req_duration............: avg=234ms  min=12ms   med=180ms  max=8.2s   p(90)=480ms  p(95)=720ms
                                                                                         ↑ OVER SLO
http_req_failed..............: 3.20%     ← Over the 1% threshold ← FAIL
vus_max......................: 500

Threshold failures:
- http_req_duration: p(95)<500ms — FAIL (p95=720ms)
- http_req_failed: rate<0.01 — FAIL (rate=0.032)
```

### Common failure patterns and causes
```
Pattern                          Likely cause
────────────────────────────────────────────────────────────────
Latency climbs linearly          DB connection pool exhausted
Error rate spikes at N users     Thread pool / worker limit
Memory grows steadily            Memory leak (soak test this)
Errors then self-heal            Auto-scaling kicked in (fine)
Errors then stay high            Cascading failure, need restart
Fast at first, slow after 10m   Cache eviction under load
```

## Pre-Test Checklist

```
Environment setup:
☐ Testing against staging (not production) — unless explicitly planned
☐ Staging is production-equivalent in config (same instance types)
☐ Database has production-scale data (anonymized)
☐ Monitoring dashboards are open and visible
☐ Team is aware the test is running (don't trigger alerts silently)

Test design:
☐ Success thresholds are defined before test starts
☐ Traffic model reflects real user behavior (think time, journey mix)
☐ Test data is parameterized (not the same user/product every time)
☐ Authentication works in the test environment
☐ External dependencies are accounted for (mocked or real?)

After the test:
☐ Export the full results (k6 cloud or HTML report)
☐ Capture the breaking point (what VU count did it fail at?)
☐ Check infrastructure metrics for anomalies after test ends
☐ Run VACUUM ANALYZE on the test DB (if you generated lots of data)
☐ Document findings with the result summary
```

## Load Test Report Template

```
## Load Test Report: [Feature / Service]

**Date:** [Date]
**Environment:** Staging (production-equivalent)
**Tool:** k6 v0.x.x

### Test Configuration
- Normal load: 100 VUs
- Peak load: 500 VUs
- Duration: 30 minutes hold at peak
- Traffic mix: 40% browse, 30% search, 20% checkout, 10% auth

### Results

| Metric            | Target  | Actual   | Pass/Fail |
|-------------------|---------|----------|-----------|
| p50 response time | < 100ms | 78ms     | ✓         |
| p95 response time | < 500ms | 720ms    | ✗         |
| p99 response time | < 2000ms| 1840ms   | ✓         |
| Error rate        | < 1%    | 3.2%     | ✗         |
| Max throughput    | 500 RPS | 380 RPS  | ✗         |

### Failures and Root Causes
1. **p95 exceeded at > 300 VUs** — DB connection pool hit limit (20 connections)
2. **Cart errors at peak** — Payment service timeout after 2s, no retry

### Recommended Fixes
1. Increase DB connection pool to 50; add pgBouncer
2. Add retry with exponential backoff on payment calls
3. Cache product catalog (5min TTL) — reduces DB reads by ~60%

### Retest Plan
- After fixes, retest with 500 VU target
- Add soak test (2h) after passing load test
```
