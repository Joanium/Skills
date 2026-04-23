---
name: Algorithms Debugging Tactics
trigger: algorithms debugging tactics, help with algorithms debugging tactics, plan algorithms debugging tactics, improve algorithms debugging tactics, expert algorithms debugging tactics
description: Expert-level guidance for algorithms debugging tactics with domain-specific heuristics, workflow, review criteria, and failure patterns.
---

Algorithms Debugging Tactics is an expert systems skill for Algorithms. The focal concern is Debugging Tactics, but the real bar is technical work that remains correct, observable, and optimizable in hard conditions.

## When To Use

- Use this when Algorithms Debugging Tactics is constrained by performance, correctness, or hardware realities that typical app-development patterns ignore.
- Use this when failure behavior is subtle and expensive to rediscover through trial and error.
- Use this when the team needs stronger models for debugging, testing, and proving behavior.
- Use this when optimization work risks hiding deeper correctness or observability problems.

## Core Principles

- The operating envelope matters as much as the nominal algorithm or architecture.
- Correctness under non-ideal conditions should be designed before optimization starts.
- A systems design is incomplete if it cannot be interrogated with good tooling.
- State, memory, and failure models should be explicit enough to teach and test.
- Performance work should explain where the time, memory, or bandwidth actually goes.

## Key Questions

- What hidden assumption inside Algorithms Debugging Tactics would break first under scale, timing, or hardware stress?
- Which state or resource in Algorithms Debugging Tactics is hardest to observe when behavior goes wrong?
- How does Algorithms Debugging Tactics trade correctness, throughput, and recoverability today?
- What tooling gap makes Algorithms Debugging Tactics harder to reason about than it should be?
- Which optimization target inside Algorithms Debugging Tactics is attractive but strategically secondary?

## Workflow

1. Define the correctness criteria, resource envelope, and worst credible scenarios for the system.
2. Map state, memory, timing, and dependency behavior before changing code or architecture.
3. Build observability and reproducibility into the workflow before chasing throughput.
4. Use constrained experiments to isolate where the system is spending time or losing correctness.
5. Review the design for testability, operator clarity, and performance under stress.
6. Capture the resulting model so future engineers can reason from evidence instead of folklore.

## Artifacts

- A system model for Algorithms Debugging Tactics that names resources, state, and failure boundaries.
- A debugging or benchmarking harness for the hardest path.
- A correctness and performance checklist tied to the selected architecture.
- A note on which optimizations are worth doing and which are seductive noise.

## Tradeoffs

- Peak performance versus observability and reproducibility.
- General-purpose design versus specialized efficiency.
- Stronger safety guarantees versus raw control and tuning freedom.
- Tooling investment now versus slower diagnosis later.

## Signals To Watch

- Correctness failures that only appear under timing, contention, or memory pressure.
- Performance variance between synthetic and representative workloads.
- Debugging time lost because the state model is too implicit.
- Tooling friction that prevents engineers from validating assumptions quickly.
- Optimization gains that disappear when measured against realistic scenarios.

## Review Checklist

- [ ] The operating envelope for Algorithms Debugging Tactics is explicit.
- [ ] Correctness and observability were considered before optimization.
- [ ] The state and resource model are understandable enough to debug.
- [ ] Tooling exists to reproduce and inspect the hard cases.
- [ ] Performance claims are based on representative workloads.
- [ ] Future work can build on a shared systems model instead of guesswork.

## Common Failure Modes

- Optimizing before building a trustworthy model of the system.
- Treating rare timing or memory bugs as impossible instead of merely hard to see.
- Using benchmarks that flatter the design while hiding realistic constraints.
- Leaving state and failure behavior implicit until debugging becomes archaeological.
