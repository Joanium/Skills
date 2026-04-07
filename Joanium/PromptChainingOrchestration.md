---
name: Prompt Chaining & Orchestration
trigger: prompt chaining, llm orchestration, multi-step ai, langchain, chain of thought workflow, llm pipeline, ai workflow, sequential prompts, langgraph, llm agents workflow, prompt pipeline, agentic workflow, multi-step prompting
description: Design reliable multi-step LLM workflows. Covers chain decomposition, state passing, parallel execution, conditional branching, error recovery, human-in-the-loop checkpoints, and observability patterns.
---

# ROLE
You are an AI systems engineer who builds multi-step LLM workflows that are reliable, debuggable, and production-ready. You decompose complex tasks into verifiable steps, know when to use parallelism, and design for graceful failure — not just the happy path.

# WHEN TO CHAIN VS SINGLE PROMPT
```
Single prompt is enough when:
  ✓ Task fits in one context window
  ✓ Output quality is consistent
  ✓ No intermediate verification needed

Use chaining when:
  ✓ Task is too complex for one prompt (multi-stage reasoning)
  ✓ Different steps need different models (cost optimization)
  ✓ Intermediate outputs need validation before proceeding
  ✓ Parallel subtasks can be run concurrently
  ✓ Human review needed at specific checkpoints
  ✓ Context window would overflow with all steps in one prompt
```

# CHAIN DECOMPOSITION PATTERNS

## Sequential Chain
```python
# Each step's output feeds the next
async def research_and_write_pipeline(topic: str) -> str:
    # Step 1: Research — extract key facts
    research = await llm(
        system="You are a researcher. Extract 5 key facts about the topic.",
        user=f"Topic: {topic}",
        model="gpt-4o-mini"    # cheap model for extraction
    )
    
    # Step 2: Outline — structure the content
    outline = await llm(
        system="Create a structured article outline from these facts.",
        user=f"Facts:\n{research}",
        model="gpt-4o-mini"
    )
    
    # Step 3: Write — generate full content (more capable model)
    article = await llm(
        system="Write a polished article following this outline.",
        user=f"Outline:\n{outline}\n\nOriginal facts:\n{research}",
        model="gpt-4o"         # better model for final output
    )
    
    # Step 4: Edit — refine quality
    final = await llm(
        system="Edit for clarity, conciseness, and tone. Keep the meaning.",
        user=article,
        model="gpt-4o-mini"
    )
    
    return final
```

## Parallel Fan-Out / Fan-In
```python
import asyncio

async def parallel_analysis(document: str) -> dict:
    # Run independent analyses concurrently
    results = await asyncio.gather(
        analyze_sentiment(document),
        extract_entities(document),
        summarize(document),
        classify_topic(document),
    )
    
    sentiment, entities, summary, topic = results
    
    # Fan-in: combine all parallel results
    final_report = await llm(
        system="Synthesize these analyses into a coherent report.",
        user=f"""
Sentiment: {sentiment}
Entities:  {entities}
Summary:   {summary}
Topic:     {topic}
""",
        model="gpt-4o"
    )
    return {"report": final_report, "metadata": {"sentiment": sentiment, "topic": topic}}
```

## Conditional Branching
```python
async def triage_and_respond(ticket: str) -> str:
    # Step 1: Classify
    classification = await llm(
        system='Classify this support ticket. Respond with JSON: {"category": "billing|technical|general", "priority": "high|medium|low"}',
        user=ticket,
        model="gpt-4o-mini"
    )
    result = json.loads(classification)
    
    # Step 2: Branch based on classification
    match result["category"]:
        case "billing":
            return await billing_response_chain(ticket, result["priority"])
        case "technical":
            context = await fetch_knowledge_base(ticket)   # RAG lookup
            return await technical_response_chain(ticket, context)
        case "general":
            return await general_response_chain(ticket)
```

## Map-Reduce Pattern
```python
async def analyze_long_document(document: str) -> str:
    # Split into chunks
    chunks = split_into_chunks(document, chunk_size=2000)
    
    # Map: analyze each chunk independently
    chunk_analyses = await asyncio.gather(*[
        llm(system="Summarize the key points in this section.",
            user=chunk, model="gpt-4o-mini")
        for chunk in chunks
    ])
    
    # Reduce: synthesize all chunk summaries
    final_summary = await llm(
        system="Synthesize these section summaries into one coherent document summary.",
        user="\n\n---\n\n".join(chunk_analyses),
        model="gpt-4o"
    )
    return final_summary
```

# STATE MANAGEMENT
```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class PipelineState:
    """Explicit state object — pass between steps, log everything"""
    input: str
    steps: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def record(self, step_name: str, output: Any, tokens_used: int = 0):
        self.steps[step_name] = output
        self.metadata.setdefault("total_tokens", 0)
        self.metadata["total_tokens"] += tokens_used
    
    def get(self, step_name: str) -> Any:
        return self.steps.get(step_name)

# Usage
state = PipelineState(input=user_query)
research = await research_step(state.input)
state.record("research", research, tokens_used=850)

outline = await outline_step(state.get("research"))
state.record("outline", outline, tokens_used=320)
```

# VALIDATION BETWEEN STEPS
```python
async def extract_with_validation(text: str, schema: dict) -> dict:
    MAX_RETRIES = 3
    
    for attempt in range(MAX_RETRIES):
        raw = await llm(
            system=f"Extract data as JSON matching this schema: {json.dumps(schema)}. Return ONLY valid JSON.",
            user=text,
            model="gpt-4o-mini"
        )
        
        try:
            # Parse and validate
            data = json.loads(raw)
            validate(data, schema)   # jsonschema validation
            return data
            
        except (json.JSONDecodeError, ValidationError) as e:
            if attempt == MAX_RETRIES - 1:
                raise RuntimeError(f"Failed to extract valid JSON after {MAX_RETRIES} attempts: {e}")
            
            # Self-correction: feed error back to LLM
            text = f"Previous output was invalid ({e}). Original text: {text}\nFix and return valid JSON only."
    
    raise RuntimeError("Unreachable")
```

# HUMAN-IN-THE-LOOP CHECKPOINTS
```python
async def high_stakes_pipeline(request: str) -> str:
    # Step 1: Generate proposal
    proposal = await generate_proposal(request)
    
    # Step 2: Human review checkpoint (async — can wait hours)
    review_id = await send_for_human_review(proposal)
    approval = await wait_for_approval(review_id, timeout_hours=24)
    
    if approval.status == "rejected":
        # Regenerate with feedback
        revised = await revise_with_feedback(proposal, approval.feedback)
        return await high_stakes_pipeline_from_revision(revised)
    
    # Step 3: Execute approved proposal
    return await execute_proposal(proposal)

# For async human review: use a queue (SQS, Redis) + webhook callback
# Store pipeline state in DB so it survives restarts while waiting
```

# ERROR HANDLING & RETRY STRATEGIES
```python
import tenacity

@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=60),
    stop=tenacity.stop_after_attempt(3),
    retry=tenacity.retry_if_exception_type((RateLimitError, APITimeoutError)),
    reraise=True
)
async def llm_with_retry(prompt: str, **kwargs) -> str:
    return await llm(prompt, **kwargs)

# Pipeline-level error handling
async def resilient_pipeline(input: str) -> str:
    state = PipelineState(input=input)
    
    try:
        state.record("step1", await step1(input))
    except Exception as e:
        state.errors.append(f"step1 failed: {e}")
        # Decide: fail fast, skip step, or use fallback
        state.record("step1", await step1_fallback(input))
    
    # Continue pipeline with degraded result
    try:
        state.record("step2", await step2(state.get("step1")))
    except Exception as e:
        await alert_oncall(state, e)
        raise
    
    return state.get("step2")
```

# CACHING FOR EXPENSIVE STEPS
```python
import hashlib, json
from functools import wraps

def cache_llm_step(ttl_seconds: int = 3600):
    """Cache deterministic LLM steps to avoid redundant API calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = hashlib.sha256(
                json.dumps({"args": str(args), "kwargs": str(kwargs)}).encode()
            ).hexdigest()
            
            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)
            await redis.setex(cache_key, ttl_seconds, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache_llm_step(ttl_seconds=86400)   # cache research step for 24h
async def research_topic(topic: str) -> str:
    return await llm(system="Research this topic...", user=topic)
```

# OBSERVABILITY
```python
# Every step should emit:
# 1. Input/output (for debugging)
# 2. Latency (for performance monitoring)
# 3. Token usage (for cost tracking)
# 4. Model used (for audit)

from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def traced_llm_step(step_name: str, prompt: str, **kwargs) -> str:
    with tracer.start_as_current_span(step_name) as span:
        start = time.time()
        response = await openai_client.chat.completions.create(**kwargs)
        
        span.set_attributes({
            "llm.step": step_name,
            "llm.model": kwargs.get("model"),
            "llm.tokens.input": response.usage.prompt_tokens,
            "llm.tokens.output": response.usage.completion_tokens,
            "llm.latency_ms": (time.time() - start) * 1000,
        })
        
        return response.choices[0].message.content

# Use Langfuse, LangSmith, or Helicone for LLM-specific tracing
```

# PROMPT CHAINING CHECKLIST
```
[ ] Each step has a single, clear responsibility
[ ] Intermediate outputs validated before passing to next step
[ ] Retry with backoff on transient errors (rate limits, timeouts)
[ ] State object logged end-to-end for debugging
[ ] Expensive deterministic steps are cached
[ ] Parallel steps use asyncio.gather (not sequential await)
[ ] Human checkpoints defined for high-stakes decisions
[ ] Token usage tracked per step and total per pipeline run
[ ] Pipeline recoverable from checkpoint (for long-running workflows)
[ ] Tested with adversarial inputs (empty output, wrong format, truncated response)
```
