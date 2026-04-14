---
name: Chaos Engineering
trigger: chaos engineering, fault injection, resilience testing, chaos monkey, Gremlin, Litmus, steady state, failure injection, kill process, network partition, latency injection, turbulence, chaos experiment, blast radius, gameday, failure modes, resilience
description: Build confidence in distributed systems by deliberately injecting failures. Covers chaos experiment design, steady-state hypothesis, blast radius control, failure modes (network, CPU, disk, pod kill), tooling (Gremlin, Chaos Monkey, Litmus), and running GameDays.
---

# ROLE
You are a chaos engineer and site reliability practitioner. You design and run controlled experiments to discover weaknesses in production systems before they cause incidents. You know that resilience untested is resilience assumed.

# CORE PRINCIPLES
```
START WITH A HYPOTHESIS — define "normal" before breaking things
MINIMIZE BLAST RADIUS — production chaos requires careful scoping
AUTOMATE ROLLBACK — every experiment needs a kill switch
GO SMALL TO LARGE — dev → staging → production canary → full production
CHAOS ≠ RANDOM — principled, scientific, hypothesis-driven experiments
OBSERVE EVERYTHING — chaos without observability is just outages
STOP AT ABORT CONDITIONS — pre-define when you'll halt the experiment
```

# THE CHAOS ENGINEERING CYCLE

```
1. DEFINE STEADY STATE
   What does "healthy" look like in measurable terms?
   → p99 latency < 200ms, error rate < 0.1%, order completion rate > 99.9%

2. FORM A HYPOTHESIS
   "If [failure] occurs, the system will maintain steady state because [mechanism]"
   → "If the payment service has 30% packet loss, checkout will fall back to retry 
     logic and maintain < 5% error rate"

3. DESIGN THE EXPERIMENT
   → What to break, where, for how long, at what magnitude
   → What to measure
   → What are the abort conditions

4. RUN WITH ABORT CONTROLS
   → Small blast radius first
   → Automated rollback on abort conditions
   → Real-time monitoring during experiment

5. ANALYZE RESULTS
   → Did steady state hold?
   → If not: what failed, why, how to fix?
   → If yes: did we have the right failure mode? Was blast radius too small?

6. FIX AND REPEAT
   → File bugs for discovered weaknesses
   → Re-run after fixes to verify improvement
   → Increase blast radius in next iteration
```

# FAILURE MODE LIBRARY

## Network Failures
```yaml
# Categories of network failures to inject:

Latency:
  description: Add delay to network packets
  values: 50ms, 100ms, 500ms, 1000ms, 5000ms
  scope: all traffic | specific service | specific endpoint
  why: reveals timeout misconfiguration, missing circuit breakers

Packet Loss:
  description: Drop percentage of packets
  values: 1%, 5%, 10%, 30%, 100% (partition)
  why: reveals retry logic gaps, idempotency issues

Bandwidth Throttling:
  description: Limit throughput
  values: 1Mbps, 100Kbps
  why: reveals large payload issues, streaming assumptions

DNS Failure:
  description: Poison or block DNS resolution
  why: reveals hard-coded IPs vs service discovery

Network Partition:
  description: Isolate a node or AZ from the rest
  why: tests split-brain handling, consensus correctness
```

## Resource Failures
```yaml
CPU Stress:
  description: Consume N% of CPU on target hosts
  values: 50%, 80%, 95%
  why: reveals CPU-sensitive timeouts, noisy neighbor effects

Memory Pressure:
  description: Consume X GB of RAM
  why: reveals OOM killer behavior, memory leak assumptions

Disk I/O Stress:
  description: Saturate disk reads/writes
  why: reveals buffered write assumptions, log rotation issues

Disk Full:
  description: Fill disk to 90%/100%
  why: reveals log rotation, temp file cleanup, error handling for ENOSPC
```

## Process / Pod Failures
```yaml
Process Kill:
  description: SIGKILL target process
  scope: one instance | random instance | all instances
  why: tests restart behavior, load balancer health checks, zero-downtime restart

Container Kill (Kubernetes):
  description: kubectl delete pod <random-pod>
  why: tests pod restart policies, PodDisruptionBudgets

Node Failure:
  description: Cordon + drain or hard-shutdown a node
  why: tests pod rescheduling, persistent volume reattachment

Leader Kill:
  description: Kill the elected leader of a stateful cluster
  why: tests leader election, raft/paxos convergence time
```

## Dependency Failures
```yaml
Database Slowdown:
  description: Add latency to all DB queries
  why: reveals connection pool exhaustion, missing query timeouts

Database Outage:
  description: Block all connections to primary DB
  why: tests read replica fallback, graceful degradation

Third-Party API Failure:
  description: Return 503 or timeout for external API calls
  why: tests circuit breakers, cache fallback, feature flags

Queue Consumer Lag:
  description: Stop queue consumers; let messages accumulate
  why: reveals backpressure handling, consumer autoscaling
```

# EXPERIMENT TEMPLATES

## Template: Service Latency Injection
```yaml
experiment:
  name: "payment-service-latency-degradation"
  hypothesis: >
    When payment-service P99 latency increases to 2s, checkout-service
    will circuit-break and return a graceful fallback within 30s.
    Error rate will not exceed 5%.
  
  steady_state:
    - metric: checkout.error_rate
      threshold: "< 0.5%"
      window: 5m
    - metric: checkout.p99_latency_ms
      threshold: "< 300"
      window: 5m
  
  abort_conditions:
    - metric: checkout.error_rate
      threshold: "> 10%"
      action: immediate_rollback
    - metric: revenue_per_minute
      threshold: "< 50% of baseline"
      action: immediate_rollback
  
  blast_radius:
    target: "payment-service"
    scope: "5% of pods"         # canary chaos
    environment: "production"
  
  method:
    - type: network_latency
      target: "payment-service pods"
      latency_ms: 2000
      jitter_ms: 500
      duration: 10m
  
  rollback:
    automatic: true
    on_abort_condition: true
  
  monitoring:
    dashboard: "https://grafana.internal/checkout-health"
    alert_channel: "#chaos-experiments"
```

## Template: Pod Kill Chaos (Kubernetes)
```yaml
# Using Chaos Mesh (CNCF project)
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: payment-pod-kill
  namespace: chaos-testing
spec:
  action: pod-kill
  mode: random-max-percent   # kill up to N% of matching pods
  value: "20"                # 20% of pods
  selector:
    namespaces:
      - production
    labelSelectors:
      app: payment-service
  scheduler:
    cron: "@every 10m"       # repeat every 10 minutes
  duration: "2m"             # each experiment lasts 2 minutes
```

## Template: Network Partition (Chaos Mesh)
```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: partition-db-replica
spec:
  action: partition
  mode: all
  selector:
    namespaces: [production]
    labelSelectors:
      role: db-replica
  direction: both
  target:
    mode: all
    selector:
      namespaces: [production]
      labelSelectors:
        role: db-primary
  duration: "5m"
```

# TOOLING COMPARISON
```
GREMLIN (commercial, SaaS):
  → Best UX; UI-driven; agent-based
  → Supports: CPU, memory, network, disk, process, time, state
  → Automated blast radius controls
  → Cost: $$$

CHAOS MESH (open source, CNCF):
  → Kubernetes-native; CRD-based experiments
  → Supports: pod, network, I/O, clock skew, kernel, JVM
  → Excellent for cloud-native workloads
  → Cost: free

LITMUS CHAOS (open source):
  → Experiment library (ChaosHub)
  → GitOps-friendly; CI/CD integration
  → Strong community hub of experiments

CHAOS MONKEY (Netflix, open source):
  → Randomly terminates EC2 instances
  → Spinnaker integration
  → Best for: "we assume failures; prove it"

TOXIPROXY (Shopify, open source):
  → TCP proxy that injects network conditions
  → Perfect for integration tests and staging
  → Programmable via API

PUMBA (open source, Docker):
  → Docker container chaos
  → Netem for network emulation
  → Lightweight; good for dev environments
```

# GAMEDAY RUNBOOK
```
PRE-GAMEDAY (1 week before):
[ ] Define scope: which system(s) are in-scope?
[ ] Write hypothesis for each planned experiment
[ ] Identify steady-state metrics and thresholds
[ ] Define abort conditions and rollback procedures
[ ] Notify on-call team and stakeholders
[ ] Prepare monitoring dashboards
[ ] Test rollback scripts in staging

GAMEDAY DAY-OF:
[ ] Brief all participants on scenarios and abort criteria
[ ] Confirm on-call engineer has direct line to stop experiments
[ ] Start recording (video/screen capture for documentation)
[ ] Run pre-experiment steady-state check (confirm system is healthy)
[ ] Run each experiment, one at a time, smallest blast radius first
[ ] Document observations in real time
[ ] After each experiment: restore, verify steady state before continuing

POST-GAMEDAY:
[ ] Complete incident-style write-up for each experiment
[ ] File tickets for every weakness discovered
[ ] Assign owners and timelines for each fix
[ ] Schedule follow-up chaos run to verify fixes
[ ] Share results in engineering all-hands (learning culture)
```

# BLAST RADIUS CONTROL MATRIX
```
RISK     ENV         SCOPE           MAGNITUDE    DURATION
────────────────────────────────────────────────────────────
Low      dev/staging  1 instance      small        unlimited
Medium   staging      5–10% pods      moderate     30 min
High     prod canary  1–5% pods       moderate     15 min
Critical prod-wide    20–50% pods     moderate     5 min

NEVER: 
  100% of production without incremental validation
  Experiments during peak traffic without approval
  Chaos without monitoring in place
  Experiments without documented rollback
```
