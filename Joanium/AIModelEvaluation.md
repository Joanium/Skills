---
name: AI Model Evaluation (Evals)
trigger: LLM evals, model evaluation, eval framework, benchmark LLM, evaluate AI output, prompt evaluation, model quality, hallucination detection, eval dataset, model regression, AI testing, eval harness, judge model
description: Design and run rigorous evaluations for LLM-powered products. Covers eval types, dataset construction, scoring methods, LLM-as-judge, regression tracking, and eval-driven development workflows.
---

# ROLE
You are a senior ML engineer specializing in evaluation. "Vibes" are not a release criterion. Your job is to build measurement systems that tell you, with evidence, whether a model or prompt change made things better or worse.

# WHY EVALS MATTER
```
WITHOUT EVALS:
  - "The new prompt seems better" — based on 5 examples tried
  - Ship a change, users complain, rollback 2 days later
  - Can't compare Model A vs Model B objectively
  - No way to know if a regression was introduced

WITH EVALS:
  - "The new prompt improved task accuracy from 74% → 81% on 500 examples"
  - Catch regressions in CI before they reach production
  - Compare models on YOUR tasks, not generic benchmarks
  - Make confident, evidence-based decisions about prompts and models
```

# EVAL TAXONOMY

## By Evaluation Method
```
EXACT MATCH:    Output must match expected answer exactly
  Best for: classification, structured extraction, yes/no, multiple choice
  Limit: brittle — "Yes" ≠ "yes" without normalization

SIMILARITY:     Semantic or lexical distance from reference
  Methods: ROUGE, BLEU, BERTScore, cosine similarity of embeddings
  Best for: summarization, translation, paraphrase
  Limit: can miss factual errors with high surface similarity

RULE-BASED:     Custom code validates output structure and constraints
  Best for: JSON schema validation, length limits, format compliance, code syntax
  Example: does output parse as valid JSON? does code execute?

LLM-AS-JUDGE:   Another LLM grades the output
  Best for: open-ended quality, reasoning, helpfulness, tone
  Limit: expensive, judge can be biased — must validate judge quality
  Calibration: judge must agree with human raters ≥ 80% of the time

HUMAN EVAL:     Humans rate or rank outputs
  Best for: final validation, calibrating automated judges, edge cases
  Limit: slow, expensive, doesn't scale to CI
```

## By Eval Purpose
```
FUNCTIONAL:   Does it do the task correctly?
  → Task accuracy, extraction precision/recall, answer correctness

SAFETY:       Does it ever say things it shouldn't?
  → Refusal rate on harmful prompts, toxicity, PII leakage

ROBUSTNESS:   Does it degrade on noisy or adversarial input?
  → Typos, prompt injection, jailbreak attempts, out-of-distribution inputs

LATENCY:      How fast is it?
  → p50/p95/p99 time-to-first-token, total completion time

COST:         What does it cost to run?
  → Input/output tokens, cost per task

CONSISTENCY:  Does it give the same answer when asked the same question?
  → Repeated sampling, temperature variation
```

# BUILDING YOUR EVAL DATASET

## Dataset Design Principles
```
SIZE: Minimum viable eval set sizes (task-dependent):
  Classification tasks:    100–300 examples per class
  Open-ended generation:   200–500 examples minimum
  Safety evals:            500+ adversarial examples
  Regression prevention:   All bugs/failures found in production → add as tests

SOURCES (in priority order):
  1. Real production data — closest to what users actually do
  2. Annotated edge cases — tricky inputs that caused failures
  3. Synthetic data — generated variations, but validate quality
  4. Benchmark datasets — useful for comparison, not your primary signal

LABELING:
  Golden answers for factual/structured tasks → use domain experts
  Relative ratings (A vs B) for generation quality → use paired comparisons
  Multi-annotator for subjective tasks → measure inter-annotator agreement
  Minimum kappa ≥ 0.6 for acceptable agreement; investigate if lower

SPLITS:
  Dev set:    active iteration — small (50–100 examples), fast feedback
  Test set:   locked — never used during development, only for final eval
  Regression: cases that previously failed — always re-run these
```

## Avoiding Dataset Contamination
```
NEVER use:
  ✗ Examples you already tested during prompt development
  ✗ Data from the same source as your training data (if fine-tuning)
  ✗ A test set to make decisions — use it only for final reporting

Prevent leakage:
  - Date-split: train on pre-date, eval on post-date events
  - Source-split: different data sources for train vs eval
  - Dedup: remove near-duplicates between splits (use MinHash or embedding similarity)
```

# LLM-AS-JUDGE DESIGN

## Judge Prompt Template
```
SYSTEM:
You are an expert evaluator. You will be given a task, an AI response,
and optionally a reference answer. Grade the response on the criteria below.
Your grade must be based on evidence in the response, not assumptions.

USER:
## Task
{task_description}

## User Input
{user_input}

## Reference Answer (if available)
{reference_answer}

## AI Response to Grade
{ai_response}

## Grading Criteria
Score the response 1–5 on each criterion:
- ACCURACY:     Does it correctly answer the question? Is every factual claim true?
- COMPLETENESS: Does it cover all important aspects of the question?
- RELEVANCE:    Is the response focused and free of irrelevant content?
- CLARITY:      Is it well-organized and easy to understand?

Output ONLY valid JSON in this format, nothing else:
{
  "accuracy": <1-5>,
  "completeness": <1-5>,
  "relevance": <1-5>,
  "clarity": <1-5>,
  "overall": <1-5>,
  "reasoning": "<brief explanation of scores>"
}
```

## Validating Your Judge
```python
# Judge calibration: judge must agree with humans on your test set
def calibrate_judge(human_ratings: list[int], judge_ratings: list[int]) -> dict:
    from scipy.stats import spearmanr, pearsonr
    from sklearn.metrics import cohen_kappa_score

    return {
        "spearman_correlation": spearmanr(human_ratings, judge_ratings).correlation,
        "pearson_correlation":  pearsonr(human_ratings, judge_ratings)[0],
        "cohen_kappa":          cohen_kappa_score(human_ratings, judge_ratings),
        "exact_agreement":      sum(h == j for h, j in zip(human_ratings, judge_ratings)) / len(human_ratings),
        "within_1_agreement":   sum(abs(h - j) <= 1 for h, j in zip(human_ratings, judge_ratings)) / len(human_ratings),
    }

# Minimum thresholds before trusting a judge:
# spearman >= 0.7   strong rank correlation
# kappa >= 0.6      substantial agreement
# within_1 >= 0.85  judge almost always within 1 point of human
```

# RUNNING EVALS

## Eval Runner Structure
```python
import asyncio
from dataclasses import dataclass

@dataclass
class EvalCase:
    id: str
    input: dict
    expected: str | None
    tags: list[str]  # for filtering: ["safety", "edge_case", "regression"]

@dataclass
class EvalResult:
    case_id: str
    output: str
    scores: dict[str, float]
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    passed: bool

async def run_eval(
    cases: list[EvalCase],
    model_fn: callable,
    scorer_fn: callable,
    concurrency: int = 10
) -> list[EvalResult]:
    semaphore = asyncio.Semaphore(concurrency)

    async def run_case(case: EvalCase) -> EvalResult:
        async with semaphore:
            start = time.monotonic()
            output, usage = await model_fn(case.input)
            latency = (time.monotonic() - start) * 1000

            scores = await scorer_fn(case, output)
            return EvalResult(
                case_id=case.id,
                output=output,
                scores=scores,
                latency_ms=latency,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                passed=scores.get("overall", 0) >= 3.5  # configurable threshold
            )

    return await asyncio.gather(*[run_case(c) for c in cases])
```

## Eval Reporting
```python
def summarize_results(results: list[EvalResult]) -> dict:
    scores = [r.scores["overall"] for r in results]
    return {
        "total_cases": len(results),
        "pass_rate": sum(r.passed for r in results) / len(results),
        "mean_score": sum(scores) / len(scores),
        "p10_score": sorted(scores)[int(len(scores) * 0.1)],
        "p90_score": sorted(scores)[int(len(scores) * 0.9)],
        "mean_latency_ms": sum(r.latency_ms for r in results) / len(results),
        "total_cost_usd": estimate_cost(results),
        "failures": [r for r in results if not r.passed]
    }
```

# EVAL-DRIVEN DEVELOPMENT

## Workflow
```
1. BASELINE:   Run eval on current production prompt/model → record scores
2. CHANGE:     Make prompt or model change
3. EVAL:       Re-run on same eval set (deterministic: temperature=0, seed fixed)
4. COMPARE:    Report delta — which cases improved? which regressed?
5. DECIDE:     Ship if improvement > threshold AND no new regressions
6. MONITOR:    Online eval in production — sample real traffic, grade it

Prompt change decision criteria:
  ✓ Ship: overall +3%+ improvement, no new regression cases
  ✗ Block: any regression in safety cases, degradation in high-priority tags
  ↺ Iterate: improvement exists but regressions in a subset — refine
```

## CI Integration
```yaml
# .github/workflows/eval.yml
name: LLM Evals
on:
  pull_request:
    paths:
      - 'prompts/**'
      - 'src/llm/**'

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run eval suite
        run: python evals/run.py --suite=regression --baseline=main
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - name: Check regression threshold
        run: python evals/check_regression.py --max-degradation=0.02

# Fail PR if pass_rate drops more than 2% from baseline
```

# ONLINE EVALUATION (PRODUCTION)
```python
# Sample real traffic and evaluate async — don't slow down users
async def log_for_online_eval(request: dict, response: str, metadata: dict):
    if random.random() > SAMPLE_RATE:  # e.g., 0.05 = 5% of traffic
        return

    await eval_queue.push({
        "input": request,
        "output": response,
        "metadata": metadata,
        "timestamp": datetime.utcnow().isoformat()
    })

# Background worker grades sampled outputs
async def online_eval_worker():
    async for item in eval_queue:
        score = await llm_judge(item["input"], item["output"])
        await metrics.record("online_eval_score", score, tags=item["metadata"])

# Alert if rolling 24h score drops significantly below baseline
```

# COMMON PITFALLS
```
MISTAKE: Evaluating on your dev examples
FIX: Strict train/test separation — never eval on data you used to develop

MISTAKE: Using a single aggregate score
FIX: Report scores per tag/category — overall hides important failures in subsets

MISTAKE: Running eval once and forgetting it
FIX: Eval in CI on every prompt change, report weekly trend in production

MISTAKE: Trusting an uncalibrated judge
FIX: Always validate judge vs humans before using judge output as ground truth

MISTAKE: Temperature > 0 in evals
FIX: temperature=0, fixed seed for reproducibility

MISTAKE: Too-small eval set ("we tested 20 examples")
FIX: Minimum 200 examples; use confidence intervals to report uncertainty

MISTAKE: "The benchmark says 90%" as your primary metric
FIX: Generic benchmarks ≠ your task; build task-specific evals
```
