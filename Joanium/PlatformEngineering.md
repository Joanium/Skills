---
name: Platform Engineering & Internal Developer Platforms
trigger: platform engineering, internal developer platform, idp, developer platform, golden path, developer self-service, platform team, paved road, internal tooling, developer portal, backstage, developer productivity platform, devex platform
description: Design and build internal developer platforms (IDPs) that standardize infrastructure, improve developer experience, and let product teams ship faster. Use when forming a platform team, reducing infrastructure toil, or standardizing engineering workflows.
---

A platform team exists to make every other team faster without that team having to think about infrastructure. The best platform teams are invisible: developers choose the "golden path" because it's genuinely the fastest, easiest way to ship — not because they're forced to.

## The Platform Team Mission

```
Wrong: "The platform team owns infrastructure and enforces standards."
Right: "The platform team is an internal product team. 
        Their customers are other engineers. 
        Their product is developer productivity."
```

**The test of a good platform:** Are product teams voluntarily using your golden paths?  
If they're working around you, your platform is failing.

## The Four Pillars of an IDP

```
1. TEMPLATES (Scaffolding)
   → Standardized service templates that bootstrap new projects
   → Pre-configured with logging, tracing, auth, health checks
   → Reduces "day 0" setup from days to minutes

2. SELF-SERVICE INFRASTRUCTURE (Provision without tickets)
   → Developers can provision databases, queues, caches via UI or CLI
   → No waiting on infra tickets
   → Guardrails ensure compliance and cost controls

3. DEPLOYMENT (Ship confidently)
   → Standardized CI/CD pipelines that work out of the box
   → Progressive delivery (canary, feature flags) built in
   → One-click rollback

4. OBSERVABILITY (Know what's happening)
   → Logs, metrics, traces provisioned automatically per service
   → Alerting templates based on service type
   → Dashboards provisioned from service metadata
```

## The Golden Path

The golden path is the opinionated, supported, recommended way to do something. It should cover:

```markdown
# Our Golden Paths

## New service
Golden path: Use the service template (`platform create service`)
Time to first deploy: < 30 minutes
What you get automatically: Dockerfile, CI/CD, logging, health check, 
tracing, test scaffolding, Kubernetes manifests

## Database
Golden path: Provision via platform portal
Time to provision: < 5 minutes
What you get: RDS PostgreSQL, automated backups, connection string in 
secrets manager, alerts pre-configured

## Feature flags
Golden path: LaunchDarkly (managed by platform, product teams pay per seat)
What you get: SDK already installed in service template, standard flag conventions

## Secrets management
Golden path: AWS Secrets Manager, accessed via platform SDK
What you get: Automatic secret rotation, audit log, no secrets in code/env files
```

## Service Templates

The most impactful thing a platform team can build: a template that scaffolds a new service in one command.

```bash
# CLI command
platform create service --name payment-processor \
  --type api \
  --language typescript \
  --database postgres

# What it generates:
payment-processor/
├── src/
│   ├── index.ts           # Express server with health check
│   ├── config.ts          # Config from env, typed
│   └── logger.ts          # Structured logging (already configured)
├── Dockerfile             # Multi-stage, production-ready
├── .github/
│   └── workflows/
│       └── ci.yml         # CI with test, lint, build, deploy stages
├── k8s/
│   ├── deployment.yaml    # With resource limits, probes
│   ├── service.yaml
│   └── hpa.yaml           # Horizontal Pod Autoscaler
├── terraform/
│   └── main.tf            # Service-specific infra (if needed)
├── README.md              # Pre-filled with runbook links
└── platform.yaml          # Service registry entry
```

### platform.yaml — the service manifest
```yaml
# platform.yaml — checked in to the repo
service:
  name: payment-processor
  team: payments
  tier: critical       # critical | standard | internal — drives SLO thresholds
  language: typescript
  type: api
  
dependencies:
  - name: payments-db
    type: postgres
  - name: stripe
    type: external

contacts:
  oncall: payments-team    # maps to PagerDuty schedule
  slack: "#payments-eng"

slos:
  availability: 99.95%
  latency_p95_ms: 200

docs:
  runbook: https://notion.com/payments/runbooks
  architecture: https://notion.com/payments/architecture
```

This manifest auto-provisions: alerts, dashboards, on-call routing, service catalog entry.

## The Service Catalog

A service catalog is a living inventory of every service. Backstage is the de facto open-source standard.

```yaml
# catalog-info.yaml (Backstage format)
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: payment-processor
  description: Processes payment charges and refunds
  annotations:
    github.com/project-slug: myorg/payment-processor
    pagerduty.com/integration-key: abc123
    grafana/alert-label-selector: service=payment-processor
  tags:
    - payments
    - critical
    - typescript
  links:
    - url: https://grafana.example.com/d/payments
      title: Dashboard
    - url: https://notion.com/runbooks/payments
      title: Runbook

spec:
  type: service
  lifecycle: production
  owner: group:payments-team
  system: payments-platform
  dependsOn:
    - resource:payments-postgres
    - component:stripe-integration
```

## Self-Service Infrastructure

Engineers should be able to provision infrastructure without filing tickets. Implement guardrails, not gatekeepers.

```hcl
# Terraform module: platform-managed PostgreSQL
# product teams call this, platform team owns the module

module "database" {
  source = "github.com/myorg/platform//terraform/modules/postgres"
  
  name        = "payment-processor"
  environment = "production"
  tier        = "critical"  # drives instance size and backup retention
  
  # Platform module handles:
  # - Instance type selection based on tier
  # - Automated backups (30-day retention for critical)
  # - Connection pooling (PgBouncer)
  # - Password rotation (90 days)
  # - CloudWatch alarms (storage, connections, CPU)
  # - Connection string in Secrets Manager
  # - Read replica for critical tier
}
```

## Standardizing Observability

Every service gets the same observability automatically:

```javascript
// platform/sdk/observability.ts — ships in the service template
import { createLogger } from '@platform/logger';
import { createTracer } from '@platform/tracing';
import { createMetrics } from '@platform/metrics';

// In service template — all pre-configured
export const logger = createLogger({
  service: process.env.SERVICE_NAME,
  environment: process.env.NODE_ENV,
  // Automatically ships to: Datadog / CloudWatch / Grafana
});

export const tracer = createTracer({
  // Pre-configured with service name, sampling rate by tier
  // Integrates with: AWS X-Ray / Jaeger / Datadog APM
});

export const metrics = createMetrics({
  // Pre-defined metrics: http.requests, http.errors, http.duration
  // Auto-tagged with: service, environment, version
});

// Usage in service code:
// logger.info('Processing payment', { orderId, amount });  
// → structured JSON → Datadog → searchable
```

## Platform Team Metrics (how to measure success)

```
Developer satisfaction:
- Developer NPS (quarterly survey): "How satisfied are you with internal tools?"
- Time to first deploy for new services
- Number of support tickets from product teams

Platform adoption:
- % of services using the standard service template
- % of databases provisioned via self-service (vs tickets)
- % of services covered by automated observability

Reliability:
- Platform uptime (the platform is infrastructure for infrastructure)
- Mean time to provision a database
- CI/CD pipeline median build time

Toil reduction:
- Engineering hours spent on infra tickets (should trend to zero)
- Number of manual provisioning steps required for new service
```

## Platform Roadmap Template

```markdown
## Platform Team Q[X] Roadmap

**Theme:** [e.g., "Self-service first" / "Observability as code"]

### Problem statement
[What are product teams struggling with that the platform team can solve?]

### This quarter's bets

**P1 — Service template v2 (30% of capacity)**
- Problem: New service setup takes 3-5 days
- Solution: Template that provisions service + DB + CI in < 30 min
- Success metric: Time to first deploy < 30 minutes for new services

**P2 — Self-service database provisioning (30%)**
- Problem: 47 infra tickets per month for database provisioning
- Solution: Terraform module + portal UI
- Success metric: Infra tickets for DB < 5/month

**P3 — Standardized alerting templates (20%)**
- Problem: 40% of services have no alerts; 30% have noisy useless alerts
- Solution: Tiered alert templates, auto-provisioned from platform.yaml
- Success metric: 100% of critical services with P1 alerts

**20% — Unplanned / support / maintenance**

### Not doing this quarter (and why)
- [Thing]: Deprioritized because [reason]
```

## Platform Engineering Checklist

```
Foundation:
☐ Is there a service template that product teams voluntarily use?
☐ Can a new engineer deploy their first service in < 30 minutes?
☐ Is there a service catalog with all services, owners, and on-call?
☐ Can infrastructure be provisioned without filing a ticket?

Operations:
☐ Is logging standardized across all services?
☐ Are dashboards auto-provisioned from service metadata?
☐ Are alert templates based on service tier?
☐ Is on-call routing configured from the service manifest?

Process:
☐ Does the platform team do office hours / support hours?
☐ Is there a feedback channel for product engineers?
☐ Are golden paths documented AND promoted?
☐ Is platform adoption measured and reviewed quarterly?
```
