---
name: Command R / R+ (Cohere) Prompting
trigger: cohere prompting, command r, command r plus, cohere rag, cohere tips, cohere instructions
description: Best practices for prompting Cohere's Command R and Command R+ models. Use when building RAG pipelines, enterprise document search, citation-heavy workflows, or multi-step tool use with grounded retrieval.
---

# ROLE
You are a Cohere Command R prompt engineer. Your goal is to leverage Command R+'s RAG-native design, citation engine, and enterprise tool use for reliable, grounded document workflows.

# MODEL PERSONALITY
```
Command R/R+ is:
- Built natively for RAG (Retrieval Augmented Generation)
- Designed for enterprise: document grounding, citations, compliance
- Strong at multi-step tool use and agent workflows
- RAG mode returns exact citation spans from source documents
- Not primarily a creative model — best at structured, grounded tasks
- R+: more powerful, better reasoning, costlier
- R: faster, cheaper, still excellent at retrieval tasks
```

# CORE API PATTERN
```python
import cohere

co = cohere.Client(api_key="your_key")

response = co.chat(
    model="command-r-plus-08-2024",
    message="Summarize the key risks from these filings.",
    documents=[
        {"title": "Q3 Filing", "snippet": "... risk factors text ..."},
        {"title": "Annual Report", "snippet": "... risk factors text ..."}
    ],
    citation_quality="accurate"  # or "fast"
)

# Access grounded citations:
for citation in response.citations:
    print(citation.text, citation.document_ids)
```

# RAG DOCUMENT FORMAT
```
Documents passed to Command R+ should be structured:

documents = [
    {
        "id": "doc_001",           # Unique ID for citation tracking
        "title": "Filing Q3 2024", # Used in citations
        "snippet": "...",          # The actual text chunk
        "url": "https://..."       # Optional, for source linking
    }
]

Best practices:
- Chunk documents to 300-500 tokens per snippet
- Use meaningful titles — they appear in citations
- Keep snippets focused on a single topic/section
- IDs must be unique — used to trace citation provenance
```

# CITATION ENGINE
```
Command R+ returns structured citations automatically.
Parse them to build grounded, verifiable responses:

response.text          # Full answer with inline markers
response.citations     # List of citation objects
  .text                # The quoted span
  .start/end           # Position in response text
  .document_ids        # Which doc(s) it comes from

Use case: Legal, compliance, financial reporting, medical — anywhere you need traceability.

citation_quality options:
"accurate" → full reranking, highest precision (slower)
"fast"     → lighter pass, good for high-volume pipelines
```

# TOOL USE (AGENTIC MODE)
```python
tools = [
    {
        "name": "database_query",
        "description": "Query the internal analytics database",
        "parameter_definitions": {
            "sql": {
                "description": "SQL query to execute",
                "type": "str",
                "required": True
            },
            "database": {
                "description": "Target database name",
                "type": "str",
                "required": True
            }
        }
    }
]

response = co.chat(
    model="command-r-plus-08-2024",
    message="What were our top 5 revenue streams last quarter?",
    tools=tools
)

# Check for tool calls:
if response.tool_calls:
    for tc in response.tool_calls:
        result = execute_tool(tc.name, tc.parameters)
        # Re-inject result as tool_results in next call
```

# PREAMBLE (SYSTEM PROMPT)
```
Cohere calls the system prompt a "preamble":

response = co.chat(
    model="command-r-plus-08-2024",
    preamble="You are an enterprise compliance assistant. Always cite your sources. If information is not in the provided documents, say 'Not found in documents'.",
    message=user_query,
    documents=docs
)

Preamble tips:
- Keep it under 200 tokens for best instruction following
- Explicitly tell it to use documents: "Answer only from the provided documents"
- Set citation behavior: "Always include citation references"
- Define fallback: "If unsure, say 'insufficient information'"
```

# CONVERSATION MEMORY
```
Command R+ maintains multi-turn context via chat_history:

chat_history = [
    {"role": "USER", "message": "What is our refund policy?"},
    {"role": "CHATBOT", "message": "Based on doc_002, your refund policy..."}
]

response = co.chat(
    model="command-r-plus-08-2024",
    chat_history=chat_history,
    message="Does that apply to digital products too?",
    documents=docs
)

Always re-inject chat_history — the API is stateless.
```

# ANTI-PATTERNS
```
AVOID:
- Sending large documents as single snippets — chunk them
- Using Command R for creative tasks — it's built for grounding
- Ignoring citation objects — they're the model's primary value-add
- Empty or duplicate document IDs — breaks citation tracking
- Relying on model knowledge without documents for factual tasks

FIX:
- Chunk to 300-500 token snippets
- Use Command R for RAG; use other models for pure generation
- Always parse and surface citations to end users
- Validate document structure before sending
```

# REVIEW CHECKLIST
```
[ ] Documents structured with id, title, snippet
[ ] Chunks are 300-500 tokens each
[ ] citation_quality set to "accurate" for compliance tasks
[ ] Preamble instructs model to use documents
[ ] Fallback behavior defined ("say X if not found")
[ ] Tool schemas use Cohere format (parameter_definitions)
[ ] chat_history re-injected for multi-turn sessions
[ ] Citation objects parsed and surfaced in UI
```
