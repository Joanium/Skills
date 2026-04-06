---
name: NLPTextProcessing
description: Build natural language processing pipelines for text classification, named entity recognition, sentiment analysis, summarization, embeddings, search, and text generation. Use when the user asks about tokenization, transformers, spaCy, Hugging Face, semantic search, text preprocessing, or building NLP-powered features.
---

You are an expert in natural language processing and text engineering, covering classical NLP with spaCy/NLTK, transformer-based models via Hugging Face, embedding generation, semantic search, and building production NLP pipelines.

The user provides an NLP task: building a text classifier, extracting entities, generating embeddings, building a semantic search system, fine-tuning a language model, or preprocessing text for downstream use.

## NLP Task Map

Choose the right approach for the task:

| Task                     | Classical Approach  | Transformer Approach                   |
| ------------------------ | ------------------- | -------------------------------------- |
| Text classification      | TF-IDF + LogReg/SVM | `text-classification` pipeline         |
| Named Entity Recognition | spaCy `ner`         | `token-classification` pipeline        |
| Sentiment analysis       | VADER, TextBlob     | `sentiment-analysis` pipeline          |
| Summarization            | TextRank, Gensim    | `summarization` pipeline               |
| Translation              | Moses, MarianMT     | `translation` pipeline                 |
| Question answering       | TF-IDF retrieval    | `question-answering` pipeline          |
| Semantic similarity      | Word2Vec, GloVe     | Sentence Transformers                  |
| Text generation          | N-gram LM           | `text-generation` pipeline (GPT-style) |

## Text Preprocessing

```python
import re
import unicodedata
from typing import List

def clean_text(text: str) -> str:
    # Normalize unicode (e.g., é → e)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    # Lowercase
    text = text.lower()
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # Remove email addresses
    text = re.sub(r'\S+@\S+\.\S+', '', text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove special characters (keep alphanumeric + spaces)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Preserve more punctuation for sentence-level tasks
def light_clean(text: str) -> str:
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text
```

**spaCy Pipeline**

```python
import spacy
nlp = spacy.load("en_core_web_sm")  # or en_core_web_lg for better accuracy

def process_text(text: str):
    doc = nlp(text)

    # Tokenization
    tokens = [token.text for token in doc]

    # Lemmatization (normalize word forms)
    lemmas = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]

    # Named Entity Recognition
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    # Labels: PERSON, ORG, GPE, DATE, MONEY, PRODUCT, etc.

    # Dependency parsing
    for token in doc:
        print(f"{token.text} → {token.dep_} → {token.head.text}")

    # Sentences
    sentences = [sent.text for sent in doc.sents]

    return {"tokens": tokens, "lemmas": lemmas, "entities": entities, "sentences": sentences}
```

## Hugging Face Transformers

**Quick Inference with Pipelines**

```python
from transformers import pipeline

# Sentiment analysis
classifier = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
result = classifier("This product is absolutely fantastic!")
# [{'label': 'POSITIVE', 'score': 0.9998}]

# Named Entity Recognition
ner = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english",
               aggregation_strategy="simple")
ner("Joel works at Anthropic in San Francisco")
# [{'word': 'Joel', 'entity_group': 'PER', 'score': 0.999},
#  {'word': 'Anthropic', 'entity_group': 'ORG', 'score': 0.997}, ...]

# Summarization
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
summary = summarizer(long_text, max_length=130, min_length=30, do_sample=False)

# Zero-shot classification (no fine-tuning needed)
zsc = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
result = zsc(
    "The new iPhone has an amazing camera with improved low-light performance",
    candidate_labels=["technology", "sports", "politics", "food"],
)
# labels=['technology', 'food', 'sports', 'politics'], scores=[0.94, 0.03, 0.02, 0.01]

# Question Answering
qa = pipeline("question-answering", model="deepset/roberta-base-squad2")
qa(question="Who founded Anthropic?", context="Anthropic was founded by Dario Amodei...")
```

**Text Classification with Fine-Tuning**

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset

# Prepare dataset
data = Dataset.from_dict({"text": texts, "label": labels})
data = data.train_test_split(test_size=0.2)

# Tokenize
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

def tokenize(batch):
    return tokenizer(batch["text"], truncation=True, max_length=512, padding="max_length")

data = data.map(tokenize, batched=True)

# Model
model = AutoModelForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=len(label2id),
    id2label=id2label,
    label2id=label2id,
)

# Training
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    learning_rate=2e-5,
    warmup_ratio=0.1,
    weight_decay=0.01,
    fp16=True,  # GPU half precision for speed
    report_to="mlflow",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=data["train"],
    eval_dataset=data["test"],
    compute_metrics=compute_metrics,
)

trainer.train()
trainer.save_model("./fine-tuned-classifier")
```

## Embeddings & Semantic Search

**Sentence Transformers**

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast, good quality, 384-dim
# Alternatives: 'all-mpnet-base-v2' (better, slower), 'BAAI/bge-large-en-v1.5' (best)

# Generate embeddings
sentences = ["How do I reset my password?", "I forgot my login credentials", "What's the weather?"]
embeddings = model.encode(sentences, normalize_embeddings=True)  # shape: (3, 384)

# Cosine similarity (dot product works because normalized)
similarity_matrix = embeddings @ embeddings.T
# sentences[0] and [1] will have high similarity (~0.85)
# sentences[2] will have low similarity with both (~0.1)
```

**Semantic Search with FAISS**

```python
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
documents = load_documents()  # List of strings

# Build index
embeddings = model.encode(documents, normalize_embeddings=True, show_progress_bar=True)
embeddings = np.array(embeddings, dtype=np.float32)

index = faiss.IndexFlatIP(embeddings.shape[1])  # Inner product = cosine for normalized vecs
index.add(embeddings)
faiss.write_index(index, "search.index")

# Search
def search(query: str, top_k: int = 5):
    query_embedding = model.encode([query], normalize_embeddings=True)
    scores, indices = index.search(np.array(query_embedding, dtype=np.float32), top_k)
    return [(documents[i], float(scores[0][j])) for j, i in enumerate(indices[0])]

results = search("How do I cancel my subscription?")
```

**Vector Database (Chroma)**

```python
import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}
)

# Add documents
collection.add(
    ids=[f"doc_{i}" for i in range(len(documents))],
    documents=documents,
    metadatas=[{"source": "faq", "category": cats[i]} for i in range(len(documents))],
)

# Query
results = collection.query(
    query_texts=["How do I cancel my subscription?"],
    n_results=5,
    where={"category": "billing"},  # Metadata filter
)
```

## Text Generation & LLM Integration

**Streaming Generation**

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, TextStreamer

model_name = "mistralai/Mistral-7B-Instruct-v0.2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto")

messages = [
    {"role": "user", "content": "Explain gradient descent in simple terms."}
]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

streamer = TextStreamer(tokenizer, skip_special_tokens=True)
with torch.no_grad():
    model.generate(**inputs, max_new_tokens=512, temperature=0.7, do_sample=True, streamer=streamer)
```

## Evaluation

```python
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns

# Classification metrics
print(classification_report(y_true, y_pred, target_names=label_names))
# Per-class precision, recall, F1

# Confusion matrix
cm = confusion_matrix(y_true, y_pred)
sns.heatmap(cm, annot=True, fmt='d', xticklabels=label_names, yticklabels=label_names)

# NER evaluation (seqeval)
from seqeval.metrics import classification_report as ner_report
print(ner_report(true_sequences, pred_sequences))

# Summarization (ROUGE)
from rouge_score import rouge_scorer
scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'])
scores = scorer.score(reference, hypothesis)
```

## Production Considerations

- **Batch inference**: process multiple texts together for GPU efficiency; use `model.encode(batch_size=64)`
- **Quantization**: 4-bit with `bitsandbytes` reduces VRAM by 4x with minimal quality loss
- **ONNX export**: faster CPU inference for smaller models; use `optimum` library
- **Model caching**: load model once at startup; never reload per request
- **Input length**: chunk long documents with overlap (e.g., 512 tokens, 50 token overlap)
- **Async serving**: use `asyncio` + thread pool for CPU-bound inference; `ray serve` for distributed
