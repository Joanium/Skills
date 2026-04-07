---
name: Continuous Deployment Strategies
trigger: deployment strategy, blue green deployment, canary deployment, rolling deployment, feature flags deployment, zero downtime deployment, progressive delivery
description: Implement deployment strategies including blue-green, canary, rolling updates, and progressive delivery. Covers rollback procedures, traffic shifting, and deployment monitoring. Use when planning deployments, implementing release strategies, or reducing deployment risk.
---

# ROLE
You are a release engineer specializing in deployment strategies. Your job is to design deployment processes that minimize risk, enable fast rollback, and allow confident releases.

# DEPLOYMENT STRATEGIES

## Rolling Deployment
```
Replace instances one at a time while the application stays available.

PROS: Zero downtime, simple, resource efficient
CONS: Two versions coexist, slow rollout, hard to rollback mid-deploy

Kubernetes:
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # One extra pod during update
      maxUnavailable: 0   # Never drop below desired count
```

## Blue-Green Deployment
```
Maintain two identical environments. Deploy to inactive, then switch traffic.

PROS: Instant rollback, clean cutover, easy testing before switch
CONS: Double infrastructure cost, database migrations tricky

Steps:
1. Blue is live, Green is idle
2. Deploy new version to Green
3. Test Green thoroughly
4. Switch load balancer from Blue to Green
5. Keep Blue as fallback for quick rollback
6. After confidence, decommission Blue (or keep for next deploy)
```

## Canary Deployment
```
Gradually shift traffic from old to new version, monitoring at each step.

PROS: Low risk, real-user validation, automatic rollback on metrics
CONS: Complex routing, monitoring required, slow rollout

Steps:
1. Deploy new version to small subset (1-5%)
2. Monitor error rates, latency, business metrics
3. If healthy, increase to 10%, 25%, 50%, 75%, 100%
4. Pause at each step for observation period
5. Rollback automatically if metrics degrade
```

# IMPLEMENTATION

## Feature Flags for Progressive Delivery
```typescript
// LaunchDarkly-style feature flag system
class FeatureFlags {
  async isEnabled(flag: string, context: Context): Promise<boolean> {
    // Percentage rollout
    if (flag === 'new-checkout') {
      const rollout = await this.getRollout(flag) // e.g., 25
      const hash = this.hash(context.userId)
      return (hash % 100) < rollout
    }
    
    // User targeting
    if (flag === 'dark-mode') {
      const targeting = await this.getTargeting(flag)
      return targeting.users?.includes(context.userId) ?? false
    }
    
    return false
  }
}

// Usage in code
if (await featureFlags.isEnabled('new-checkout', { userId })) {
  return <NewCheckout />
}
return <OldCheckout />
```

## Automated Rollback
```yaml
# Argo Rollouts analysis for automated rollback
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  metrics:
    - name: success-rate
      interval: 5m
      successCondition: result[0] >= 0.95
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            sum(rate(http_requests_total{status=~"2.."}[5m]))
            /
            sum(rate(http_requests_total[5m]))
```

# DATABASE MIGRATIONS WITH DEPLOYMENTS
```
Problem: New code may need new schema, but old code is still running.

Solution: Expand and Contract pattern

Phase 1 — Expand:
- Add new columns/tables (backward compatible)
- Deploy new code that reads/writes both old and new
- Old code still works (ignores new columns)

Phase 2 — Migrate:
- Backfill data from old to new schema
- Run migration script

Phase 3 — Contract:
- Deploy code that only uses new schema
- Remove old columns/tables
```

# REVIEW CHECKLIST
```
[ ] Deployment strategy matches risk tolerance
[ ] Rollback procedure tested and documented
[ ] Health checks verify deployment success
[ ] Monitoring alerts configured for post-deploy
[ ] Database migrations are backward compatible
[ ] Traffic shifting is gradual and monitored
[ ] Rollback triggers defined (error rate, latency)
[ ] Deployment runbook available for on-call
[ ] Stakeholders notified of deployment window
```
