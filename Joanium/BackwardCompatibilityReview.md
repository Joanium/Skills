---
name: Backward Compatibility Review
trigger: backward compatibility review, help with backward compatibility review, plan backward compatibility review, improve backward compatibility review
description: Practical guidance for planning and executing backward compatibility review with clear scope, tradeoffs, and validation steps.
---

Backward Compatibility Review is about improving engineering systems by making architecture and delivery rules explicit, reviewable, and repeatable.

## Core Principles

- Evolution beats rewrite when risk is high.
- Standards need clear exceptions and review paths.
- Compatibility and ownership must be designed intentionally.

## Workflow

1. Audit the current constraints and technical debt.
2. Define the target pattern and migration boundary.
3. Roll changes out incrementally with review checkpoints.
4. Capture decisions in docs, tooling, and team habits.

## Common Mistakes

- Changing too many layers at once.
- Skipping backward-compatibility checks.
- Leaving governance unwritten.
