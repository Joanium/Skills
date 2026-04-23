---
name: Django Idempotency Controls
trigger: django idempotency controls, help with django idempotency controls, plan django idempotency controls, improve django idempotency controls, expert django idempotency controls
description: Expert-level guidance for django idempotency controls with domain-specific heuristics, workflow, review criteria, and failure patterns.
---

Django Idempotency Controls is an expert backend skill for Django. The focal concern is Idempotency Controls, but the real task is creating server behavior that remains understandable under load, retries, and partial failure.

## When To Use

- Use this when Django Idempotency Controls shapes correctness, reliability, or compatibility for a backend surface that other systems depend on.
- Use this when the API or service contract is more important than the controller or framework syntax.
- Use this when retries, concurrent requests, or background work expose hidden design debt.
- Use this when operational clarity matters as much as feature completeness.

## Core Principles

- Design the behavior clients depend on, not only the handler code you control.
- Retries, timeouts, and duplicates are normal operating conditions, not anomalies.
- Compatibility is a product decision as much as a technical decision.
- Good observability is part of the contract because operators also consume the system.
- Background work and caching need the same rigor as request-response paths.

## Key Questions

- What assumption inside Django Idempotency Controls breaks first under concurrency, retries, or partial failure?
- Which client or downstream system will feel contract ambiguity most painfully in Django Idempotency Controls?
- Where does Django Idempotency Controls need stronger semantics: authentication, errors, ordering, or isolation?
- How will operators know whether Django Idempotency Controls is unhealthy before customers do?
- What compatibility promise is implied by Django Idempotency Controls even if it was never written down?

## Workflow

1. Define the public behavior of the endpoint, service, or contract before implementation details.
2. Model retries, duplicates, timeouts, and stale reads as expected events.
3. Specify the error model, observability hooks, and compatibility story explicitly.
4. Test the design under concurrency, slow dependencies, and partial failure.
5. Review the data, cache, and background-job interactions that make the behavior non-trivial.
6. Ship with a contract note that explains how clients and operators should reason about {0}.

## Artifacts

- A contract note for Django Idempotency Controls that includes failure semantics.
- A request, retry, and background-work interaction diagram.
- A compatibility and rollout note for downstream consumers.
- An observability checklist tied to the operational contract.

## Tradeoffs

- Strict guarantees versus operational cost and complexity.
- Immediate consistency versus throughput and isolation.
- Flexible contracts versus safer evolution paths.
- Latency optimization versus debuggability and safety.

## Signals To Watch

- Client-visible failure rate by scenario, not only by endpoint.
- Retry amplification, duplicate processing, and timeout behavior.
- Operational clarity during incidents: logs, traces, and metric usefulness.
- Compatibility regressions after changes to contract or serialization.
- Tenant, cache, or job leakage across boundaries.

## Review Checklist

- [ ] The contract for Django Idempotency Controls is explicit about success and failure behavior.
- [ ] Retries and duplicates were treated as design inputs.
- [ ] Observability explains both client and operator perspectives.
- [ ] Cache and background processing interactions are accounted for.
- [ ] Compatibility and rollout implications are documented.
- [ ] The system can be reasoned about without private tribal knowledge.

## Common Failure Modes

- Optimizing the happy path while undefined behavior grows under retries.
- Breaking contract meaning while leaving the route name unchanged.
- Treating observability as logging volume instead of operational usefulness.
- Assuming background jobs or cache entries will align with the request path by default.
