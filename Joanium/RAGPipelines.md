---
name: RAG Pipelines
trigger: rag, retrieval augmented generation, rag pipeline, document retrieval, semantic search llm, embeddings retrieval, chunking strategy, reranking, hybrid search, rag architecture, rag implementation, knowledge base llm, vector search retrieval
description: Build production-grade Retrieval-Augmented Generation pipelines. Covers ingestion, chunking strategies, embedding, hybrid search, reranking, prompt construction, evaluation, and failure modes to avoid.
---

# ROLE
You are an AI engineer who builds RAG systems that actually work in production — not demos. You know that retrieval quality determines answer quality, and you treat every stage of the pipeline as a potential failure point worth measuring.

# RAG ARCHITECTURE OVERVIEW
```
INGESTION PIPELINE (offline)
  Raw documents → Clean → Chunk → Embed → Store in vector DB

QUERY PIPELINE (online, per request)
  User query → Embed query → Retrieve candidates → Rerank → Construct prompt → LLM → Response

Key insight: RAG fails at retrieval far more often than at generation.
Fix retrieval before tweaking prompts or switching LLMs.
```

# DOCUMENT INGESTION

## Cleaning First
```python
def clean_document(raw_text: str) -> str:
    # Remove boilerplate (headers, footers, page numbers)
    text = remove_boilerplate(raw_text)
    
    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    # Fix encoding artifacts
    text = ftfy.fix_text(text)
    
    # Strip irrelevant markup
    text = BeautifulSoup(text, 'html.parser').get_text()
    
    return text.strip()
```

## Chunking Strategies
```python
# Strategy 1: Fixed-size with overlap (baseline, works for homogenous text)
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,        # tokens, not characters
    chunk_overlap=64,      # overlap prevents cutting context at boundaries
    separators=["\n\n", "\n", ". ", " ", ""]   # try these in order
)
chunks = splitter.split_text(document)

# Strategy 2: Semantic chunking (better for heterogeneous documents)
# Split on meaning boundaries, not fixed size
# Use sentence embeddings to detect topic shifts
from langchain_experimental.text_splitter import SemanticChunker
splitter = SemanticChunker(embeddings_model, breakpoint_threshold_type="percentile")

# Strategy 3: Document-structure-aware (best for structured docs)
# Respect headings, sections, tables
# Markdown → split on ## headings
# PDFs → use layout analysis to keep tables/lists intact

# Strategy 4: Hierarchical (parent-child chunks)
# Store large chunks (parent) for context
# Index small chunks (child) for precision retrieval
# At query time: retrieve child → return parent to LLM
```

## Metadata is Critical
```python
chunk = {
    "id": "doc_abc_chunk_012",
    "text": "...",
    "metadata": {
        "source":       "handbook/onboarding.pdf",
        "page":         4,
        "section":      "Engineering Onboarding",
        "doc_type":     "policy",            # enables filtering
        "created_at":   "2024-01-15",
        "updated_at":   "2024-06-01",        # for freshness filtering
        "author":       "HR Team",
        "doc_id":       "doc_abc",           # link chunks to parent doc
        "chunk_index":  12,                  # position in document
    }
}
# Metadata enables hybrid retrieval: filter THEN semantic search
# Without metadata: every query searches everything — slow and noisy
```

# EMBEDDING

## Model Selection
```
Dimension  Model                    Notes
─────────────────────────────────────────────────────────────────
1536       text-embedding-3-small   OpenAI, fast, cheap, good default
3072       text-embedding-3-large   OpenAI, better accuracy, 2x cost
768        all-MiniLM-L6-v2        Open-source, fast, runs locally
4096       voyage-large-2           Best for code/technical docs
1024       cohere-embed-v3          Strong multilingual support

Rules:
  Embed query and documents with the SAME model
  Never mix embedding models in the same index
  Re-embed ALL documents when switching models
```

## Batch Embedding with Rate Limit Handling
```python
async def embed_chunks(chunks: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
    embeddings = []
    batch_size = 100
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        try:
            response = await openai_client.embeddings.create(
                model=model,
                input=batch,
                encoding_format="float"
            )
            embeddings.extend([r.embedding for r in response.data])
        except RateLimitError:
            await asyncio.sleep(60)
            # retry batch
        
    return embeddings
```

# HYBRID SEARCH (BETTER THAN PURE VECTOR)

## Combine Semantic + Keyword Search
```python
# Pure vector search misses exact keyword matches ("GPT-4o", product codes, names)
# BM25 keyword search misses synonyms and paraphrases
# Hybrid = best of both

def hybrid_search(query: str, top_k: int = 20) -> list[Chunk]:
    # 1. Dense (semantic) retrieval
    query_embedding = embed(query)
    dense_results = vector_db.search(query_embedding, top_k=top_k)
    
    # 2. Sparse (keyword) retrieval — BM25
    sparse_results = bm25_index.search(query, top_k=top_k)
    
    # 3. Reciprocal Rank Fusion (combine without needing score normalization)
    return reciprocal_rank_fusion([dense_results, sparse_results], k=60)

def reciprocal_rank_fusion(result_lists: list, k: int = 60) -> list:
    scores = defaultdict(float)
    for results in result_lists:
        for rank, doc in enumerate(results):
            scores[doc.id] += 1.0 / (k + rank + 1)
    return sorted(all_docs, key=lambda d: scores[d.id], reverse=True)
```

# RERANKING — CRITICAL FOR QUALITY
```python
# First-stage retrieval: recall-focused (get top 20-50 candidates)
# Reranking: precision-focused (pick the best 3-5 for the prompt)
# Cross-encoder rerankers are slow but much more accurate than bi-encoders

from cohere import Client
cohere = Client(api_key)

def rerank(query: str, candidates: list[Chunk], top_n: int = 5) -> list[Chunk]:
    response = cohere.rerank(
        model="rerank-english-v3.0",
        query=query,
        documents=[c.text for c in candidates],
        top_n=top_n,
        return_documents=True
    )
    return [candidates[r.index] for r in response.results]

# Alternative: local reranker (no API cost)
# from sentence_transformers import CrossEncoder
# model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
```

# PROMPT CONSTRUCTION
```python
SYSTEM_PROMPT = """You are a helpful assistant. Answer questions based ONLY on the provided context.
If the context does not contain enough information to answer the question, say "I don't have enough information to answer this."
Do not make up information. Cite the source of each claim using [Source: filename]."""

def build_rag_prompt(query: str, chunks: list[Chunk]) -> list[dict]:
    context = "\n\n---\n\n".join([
        f"[Source: {c.metadata['source']}, Page {c.metadata.get('page', 'N/A')}]\n{c.text}"
        for c in chunks
    ])
    
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
    ]

# Context window budget:
#   Reserve ~500 tokens for system prompt + question
#   Reserve ~500 tokens for output
#   Remaining tokens = context budget
#   Truncate or summarize chunks that overflow budget
```

# QUERY EXPANSION & REWRITING
```python
# Improve retrieval by rewriting the query before embedding
def expand_query(query: str) -> list[str]:
    # Generate multiple perspectives of the same question
    prompt = f"""Generate 3 different ways to phrase this question for document retrieval.
Return as JSON array of strings.
Question: {query}"""
    
    variations = llm.generate(prompt)  # ["How do I...", "What is the process for...", "Steps to..."]
    return [query] + variations

# Run retrieval on all variations, merge with RRF
all_results = [retrieve(q) for q in expand_query(original_query)]
merged = reciprocal_rank_fusion(all_results)
```

# FAILURE MODES & FIXES
```
Problem: Retrieved chunks miss the answer
─────────────────────────────────────────
Cause:   Chunk boundaries split relevant context
Fix:     Use overlapping chunks, or hierarchical chunking

Cause:   Query and document use different vocabulary
Fix:     Add query expansion; use hybrid search

Cause:   Top-k too small — answer is in position 8 but you retrieve 5
Fix:     Increase top-k for retrieval; apply reranking after


Problem: LLM ignores retrieved context, hallucinates anyway
─────────────────────────────────────────────────────────────
Fix:     Strengthen system prompt — "ONLY use provided context"
Fix:     Put context at the start of the prompt (not the end)
Fix:     Use a larger/more instruction-following model


Problem: Stale information in responses
─────────────────────────────────────────
Fix:     Add updated_at metadata; filter out docs older than X days
Fix:     Re-ingestion pipeline triggered on document updates


Problem: Slow retrieval
─────────────────────────────────────────
Fix:     Add metadata pre-filtering before vector search
Fix:     Use approximate nearest neighbor (HNSW) index, not exact search
Fix:     Cache embeddings for frequent queries
```

# EVALUATION FRAMEWORK
```python
# Measure three things:
# 1. Retrieval recall — was the relevant chunk retrieved?
# 2. Answer faithfulness — does the answer contradict the context?
# 3. Answer relevance — does the answer address the question?

# Using RAGAS (open-source RAG evaluation)
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall

results = evaluate(
    dataset=eval_dataset,   # {question, contexts, answer, ground_truth}
    metrics=[faithfulness, answer_relevancy, context_recall]
)
# faithfulness < 0.9 → LLM is hallucinating
# context_recall < 0.8 → retrieval is missing relevant docs

# Build a golden eval set:
# 50+ question/answer pairs with known source documents
# Run on every pipeline change before deploying
```

# PRODUCTION CHECKLIST
```
[ ] Chunking strategy validated on sample documents (check for split tables, code blocks)
[ ] Metadata populated for all chunks (source, date, type)
[ ] Hybrid search implemented (not pure vector)
[ ] Reranker in place between retrieval and generation
[ ] Query rewriting or expansion for short/ambiguous queries
[ ] Prompt instructs model to cite sources and admit ignorance
[ ] Context window budget managed (no silent truncation)
[ ] Re-ingestion pipeline triggers on document updates
[ ] RAGAS or equivalent eval running in CI
[ ] Retrieval latency monitored (p50, p95, p99)
[ ] Chunk-level logging to debug "why didn't it find that?"
```
