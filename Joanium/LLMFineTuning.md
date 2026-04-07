---
name: LLM Fine-Tuning
trigger: fine-tune, fine tuning llm, finetune model, lora, qlora, rlhf, sft, supervised fine-tuning, dpo, model training, dataset curation, finetuning openai, custom model training, instruction tuning, model adaptation
description: Fine-tune large language models for specific tasks. Covers when to fine-tune vs prompt, dataset curation, SFT, LoRA/QLoRA, DPO, evaluation, and serving fine-tuned models. Avoids common pitfalls like overfitting and catastrophic forgetting.
---

# ROLE
You are an ML engineer who has fine-tuned models for production use cases. You know that most teams jump to fine-tuning too early, that data quality beats model size, and that evaluation must be set up before training starts — not after.

# WHEN TO FINE-TUNE VS ALTERNATIVES
```
Try these first (in order) before fine-tuning:

1. Prompt engineering       → Most problems solved here. Try few-shot, chain-of-thought.
2. RAG                      → If the problem is missing knowledge, add retrieval.
3. Prompt caching + examples → Cache system prompt with many examples (cheaper than FT).
4. Fine-tuning              → When style/format/domain consistency matters more than knowledge.

Fine-tune when you have ALL of:
  ✓ Clear performance ceiling with prompting (measured, not assumed)
  ✓ 500+ high-quality labeled examples (ideally 1000–10000+)
  ✓ Consistent, definable task (not "be smarter")
  ✓ Latency or cost driver (FT model can be smaller than prompted GPT-4)
  ✓ Eval benchmark you can measure before and after

DO NOT fine-tune when:
  ✗ You have < 100 examples
  ✗ The task changes frequently
  ✗ You want the model to "know more facts" — use RAG for that
  ✗ You haven't measured the prompting baseline
```

# DATASET CURATION — HIGHEST LEVERAGE WORK
```
Rule: 100 perfect examples > 10,000 noisy examples

Data quality checklist:
  [ ] Every example represents the EXACT behavior you want
  [ ] No inconsistencies (same input → same style/format of output)
  [ ] No hallucinations in the expected outputs
  [ ] Edge cases covered (not just easy examples)
  [ ] Distribution matches real production inputs

Data sources (in order of quality):
  1. Human-annotated from domain experts
  2. High-quality production outputs (reviewed and filtered)
  3. Synthetically generated, then human-reviewed
  4. GPT-4 generated (for cheaper models) — verify quality carefully

Dataset format (JSONL — one example per line):
  {"messages": [
    {"role": "system",    "content": "You are a legal contract reviewer..."},
    {"role": "user",      "content": "Review this clause: ..."},
    {"role": "assistant", "content": "Risk level: HIGH\nReason: This clause..."}
  ]}

Data split:
  Training:   80% (model learns from this)
  Validation: 10% (monitor for overfitting during training)
  Test:       10% (NEVER look at until final evaluation)
```

# SUPERVISED FINE-TUNING (SFT) — OPENAI API
```python
import openai

# 1. Upload training data
training_file = openai.files.create(
    file=open("train.jsonl", "rb"),
    purpose="fine-tune"
)

validation_file = openai.files.create(
    file=open("val.jsonl", "rb"),
    purpose="fine-tune"
)

# 2. Create fine-tuning job
job = openai.fine_tuning.jobs.create(
    training_file=training_file.id,
    validation_file=validation_file.id,
    model="gpt-4o-mini-2024-07-18",   # start with smaller model
    hyperparameters={
        "n_epochs": "auto",            # let OpenAI choose (usually 3-5)
        "batch_size": "auto",
        "learning_rate_multiplier": "auto"
    },
    suffix="my-task-v1"               # model name: gpt-4o-mini-...-my-task-v1
)

# 3. Monitor training
import time
while True:
    job = openai.fine_tuning.jobs.retrieve(job.id)
    print(f"Status: {job.status}")
    if job.status in ["succeeded", "failed"]:
        break
    time.sleep(60)

# 4. Use the fine-tuned model
response = openai.chat.completions.create(
    model=job.fine_tuned_model,   # e.g. "ft:gpt-4o-mini-...:my-task-v1"
    messages=[{"role": "user", "content": "..."}]
)
```

# LORA / QLORA — EFFICIENT FINE-TUNING FOR OPEN-SOURCE MODELS
```python
# LoRA: only train small adapter matrices, not full model weights
# QLoRA: quantize base model to 4-bit → fits large models on single GPU

from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer

# Load model in 4-bit (QLoRA)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Meta-Llama-3-8B-Instruct",
    quantization_config=bnb_config,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct")

# LoRA config — which layers to adapt
lora_config = LoraConfig(
    r=16,                    # rank — higher = more params, more capacity
    lora_alpha=32,           # scaling factor (alpha/r = effective LR multiplier)
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],   # attention layers
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# trainable params: 6,815,744 || all params: 8,036,925,440 || trainable%: 0.0848

# Train with SFTTrainer
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    max_seq_length=2048,
    dataset_text_field="text",
    args=TrainingArguments(
        output_dir="./output",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,     # effective batch = 4 * 4 = 16
        learning_rate=2e-4,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        evaluation_strategy="steps",
        eval_steps=50,
        save_steps=50,
        load_best_model_at_end=True,
        fp16=True,
        logging_steps=10,
    )
)
trainer.train()

# Save adapter only (small file, ~50MB vs 16GB full model)
model.save_pretrained("./adapter")
# Load later: model = PeftModel.from_pretrained(base_model, "./adapter")
```

# DPO — DIRECT PREFERENCE OPTIMIZATION
```python
# DPO: teach the model preferences without needing a separate reward model
# Better than RLHF for aligning tone, style, refusals

# Dataset format — pairs of chosen/rejected responses
dpo_dataset = [
    {
        "prompt":   "Summarize this legal document:",
        "chosen":   "This agreement establishes... [concise, accurate summary]",
        "rejected": "Sure! This document is about... [verbose, inaccurate]"
    }
]

from trl import DPOTrainer, DPOConfig

dpo_trainer = DPOTrainer(
    model=model,
    ref_model=None,      # None = use PEFT reference (memory efficient)
    args=DPOConfig(
        beta=0.1,        # KL divergence penalty — higher = stay closer to base model
        learning_rate=5e-7,
        num_train_epochs=1,
        per_device_train_batch_size=2,
    ),
    train_dataset=dpo_dataset,
    tokenizer=tokenizer,
)
dpo_trainer.train()
```

# HYPERPARAMETER GUIDE
```
Learning rate:
  SFT:  1e-5 to 5e-5 (too high = catastrophic forgetting, too low = no learning)
  DPO:  5e-7 to 1e-6 (very small — you're adjusting preferences, not teaching from scratch)

Epochs:
  Start with 3. Watch validation loss — stop when it plateaus or rises.
  Overfitting signs: training loss drops, validation loss rises

Batch size:
  Larger = more stable gradients, needs more memory
  Use gradient_accumulation_steps to simulate large batches on small GPU

LoRA rank (r):
  r=8:  very few params — good for style/format tasks
  r=16: balanced — good default
  r=64: larger capacity — for complex domain adaptation
  Higher r ≠ always better; can overfit with small data

Context length:
  Only as long as your data requires — longer = slower, more memory
  Pad/truncate consistently
```

# EVALUATION — SET UP BEFORE TRAINING
```python
# Never rely on training loss alone
# Define task-specific metrics before you start

# 1. Automated metrics
from rouge_score import rouge_scorer
scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
scores = scorer.score(reference, prediction)

# 2. LLM-as-judge (for quality, tone, format)
judge_prompt = """Rate this response on a scale of 1-5 for:
- Accuracy (does it correctly answer the question?)
- Format (does it follow the required output format?)
- Tone (is it appropriate for the domain?)
Reference: {reference}
Response: {response}
Return JSON: {"accuracy": N, "format": N, "tone": N}"""

# 3. Task-specific evals
# Classification → precision, recall, F1
# Extraction → exact match, partial match
# Generation → human preference, ROUGE, BLEU

# Track: before FT baseline, after FT, per epoch on val set
```

# CATASTROPHIC FORGETTING — AVOID IT
```
Problem: fine-tuning on narrow task degrades general capabilities
Signs:   model refuses reasonable requests, loses coherent language

Mitigations:
  Use LoRA (only trains adapters, base weights frozen)
  Mix general instruction data into training set (5-10% of examples)
  Use small learning rates and few epochs
  Monitor performance on held-out general benchmarks alongside task metrics
```

# PRODUCTION SERVING
```
OpenAI fine-tuned models:
  Same API, just swap model= to fine-tuned model ID
  No infrastructure needed

Open-source fine-tuned models:
  Merge adapter into base model: model.merge_and_unload() → save full model
  Serve with vLLM (fastest), Ollama (local), or TGI (Hugging Face)
  Quantize to int8/int4 for smaller footprint (slight quality tradeoff)

  vllm serve ./merged-model --dtype bfloat16 --max-model-len 4096
```

# FINE-TUNING CHECKLIST
```
[ ] Prompting baseline measured and documented
[ ] Dataset: 500+ examples, reviewed by domain expert
[ ] No label noise or inconsistencies in dataset
[ ] Eval benchmark defined BEFORE training starts
[ ] Validation split held out (never trained on)
[ ] Overfitting monitored during training (val loss curve)
[ ] General capability benchmarks run before and after
[ ] A/B test planned for production comparison
[ ] Model versioned and artifacts saved (weights, adapter, config)
[ ] Rollback plan if FT model underperforms in production
```
