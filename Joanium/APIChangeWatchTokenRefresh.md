---
name: API Change Watch Token Refresh
trigger: api change watch token refresh, help with api change watch token refresh, plan api change watch token refresh, improve api change watch token refresh, expert api change watch token refresh
description: Expert-level guidance for api change watch token refresh with action-oriented workflow, review criteria, and failure patterns.
---

API Change Watch Token Refresh is an expert API and integration skill for API Change Watch. The focal concern is Token Refresh, but the real objective is helping an AI make external integrations reliable, reviewable, and survivable when contracts, auth, and partners drift.

## When To Use

- Use this when API Change Watch Token Refresh affects whether external integrations remain trustworthy after partner behavior changes.
- Use this when the AI needs stronger reasoning about auth, retries, contracts, or vendor drift than internal APIs require.
- Use this when sandbox success is not enough to prove production readiness.
- Use this when partner-facing failures can damage trust faster than the code can be patched.

## Core Principles

- External integrations are unstable by default until contracts and drift detection are explicit.
- Vendor error behavior matters as much as your own implementation choices.
- Retries, backoff, and replay rules are business decisions when they affect money or trust.
- Auth flows need lifecycle thinking, not just token acquisition code.
- A partner integration is only safe when support and rollback are part of the design.

## Key Questions

- What partner or contract assumption inside API Change Watch Token Refresh is least likely to hold over time?
- How would API Change Watch Token Refresh fail if the partner changed validation, latency, or auth behavior without notice?
- What evidence proves sandbox behavior is close enough to production for API Change Watch Token Refresh?
- Which part of API Change Watch Token Refresh needs stronger replay, traceability, or escalation support?
- How will the AI explain the safety model of API Change Watch Token Refresh to an integration reviewer?

## Workflow

1. Map the external contract, auth lifecycle, and failure conditions before editing integration code.
2. Define replay, retry, version, and support handling as part of the integration behavior.
3. Compare sandbox and production assumptions explicitly instead of inheriting optimism.
4. Add evidence capture for requests, responses, signatures, and version deltas.
5. Review the integration from the perspective of partner drift, user impact, and rollback safety.
6. Document the final contract so future AI work can detect change instead of rediscovering it.

## Artifacts

- A contract and drift note for API Change Watch Token Refresh.
- A replay and escalation plan for integration failures.
- A sandbox-versus-production assumption checklist.
- A support summary describing how the integration should fail and recover.

## Tradeoffs

- Fast integration shipping versus stronger contract observability.
- Provider-specific optimization versus portability across vendors.
- Aggressive retries versus financial or operational side effects.
- Tighter validation versus easier short-term compatibility.

## Signals To Watch

- Integration breakages caused by silent contract or version drift.
- Auth, signature, or callback failures that escape shallow monitoring.
- Support escalations triggered by weak replay or evidence capture.
- Sandbox success rates that do not correlate with production reliability.
- Unexpected rate limit or duplicate processing behavior after partner changes.

## Review Checklist

- [ ] The external contract and drift risk behind API Change Watch Token Refresh are explicit.
- [ ] Replay, retry, and escalation rules are documented.
- [ ] Sandbox assumptions were challenged before production confidence was claimed.
- [ ] Auth and version lifecycle behavior are covered.
- [ ] Support and rollback implications are part of the integration design.
- [ ] Future AI work can detect vendor change from recorded evidence.

## Common Failure Modes

- Treating a third-party integration like an internal API with better branding.
- Assuming sandbox behavior is a production contract.
- Optimizing request flow while ignoring auth rotation or callback drift.
- Shipping integration code without enough evidence to debug partner failures.
