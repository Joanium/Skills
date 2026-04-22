---
name: Auth Recovery Design
trigger: auth recovery design, help with auth recovery design, plan auth recovery design, improve auth recovery design
description: Practical guidance for planning and executing auth recovery design with clear scope, tradeoffs, and validation steps.
---

Auth Recovery Design is about reducing exploitable gaps by pairing preventive controls with review, evidence, and response readiness.

## Core Principles

- Threats should be modeled from attacker behavior, not assumptions.
- Controls must be operable by the team that owns them.
- Detection and response quality are part of the design.

## Workflow

1. Map assets, trust boundaries, and likely abuse paths.
2. Choose controls, alerts, and evidence requirements deliberately.
3. Test the control against realistic misuse and failure scenarios.
4. Document response ownership and recovery expectations.

## Common Mistakes

- Adding controls without defining who reviews the signals.
- Hardening only the primary request path.
- Treating security review as a one-time checkpoint.
