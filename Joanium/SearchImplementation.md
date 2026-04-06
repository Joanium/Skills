---
name: Search Implementation
trigger: full-text search, search implementation, Elasticsearch, Algolia, Meilisearch, PostgreSQL full text search, search index, fuzzy search, autocomplete, search ranking, search filters, vector search, semantic search, tsvector, search relevance
description: Build fast, relevant search experiences. Covers PostgreSQL full-text search (tsvector), Elasticsearch/OpenSearch, Meilisearch, Algolia, autocomplete, fuzzy matching, faceted filters, and vector/semantic search with embeddings.
---

# ROLE
You are a search engineer. Your job is to build search that returns relevant results fast. The best search engine is often the simplest one — don't reach for Elasticsearch when PostgreSQL full-text search does the job.

# CHOOSE THE RIGHT TOOL
```
PostgreSQL FTS (tsvector):
  ✓ Already in your stack — no new infra
  ✓ ACID — search results consistent with writes
  ✓ Up to ~1M rows at acceptable performance
  ✗ Limited ranking; no typo tolerance; no facets out of the box
  → Use when: small/medium dataset, search is secondary feature

Meilisearch (self-hosted):
  ✓ Typo tolerance, facets, relevance tuning
  ✓ Extremely fast, simple to run
  ✓ Open source, free to self-host
  → Use when: dedicated search needed, don't want vendor lock-in

Elasticsearch / OpenSearch:
  ✓ Full-featured: aggregations, geo, analytics
  ✓ Scales to billions of documents
  ✗ Complex to operate, high resource usage
  → Use when: large scale, complex facets, log analytics

Algolia (SaaS):
  ✓ Best developer experience, instant results
  ✓ Managed — no ops overhead
  ✗ Expensive at scale
  → Use when: need best UX fast, budget allows

Vector Search (pgvector, Qdrant, Pinecone):
  ✓ Semantic search — finds meaning, not just keywords
  ✓ "Products similar to this one"
  → Use for: AI-powered search, recommendations, semantic matching
```

# POSTGRESQL FULL-TEXT SEARCH

## Setup — tsvector Column
```sql
-- Add a generated tsvector column for fast indexing
ALTER TABLE products
ADD COLUMN search_vector tsvector
GENERATED ALWAYS AS (
  to_tsvector('english',
    coalesce(name, '') || ' ' ||
    coalesce(description, '') || ' ' ||
    coalesce(brand, '') || ' ' ||
    coalesce(category, '')
  )
) STORED;

-- GIN index — fast full-text lookup
CREATE INDEX idx_products_search ON products USING GIN (search_vector);

-- For simple single-column use:
CREATE INDEX idx_posts_title ON posts USING GIN (to_tsvector('english', title));
```

## Queries
```sql
-- Basic search
SELECT id, name, brand
FROM products
WHERE search_vector @@ plainto_tsquery('english', 'wireless headphones')
ORDER BY ts_rank(search_vector, plainto_tsquery('english', 'wireless headphones')) DESC
LIMIT 20;

-- Phrase search (words adjacent in order)
SELECT * FROM products
WHERE search_vector @@ phraseto_tsquery('english', 'noise cancelling')

-- Advanced: OR, AND, NOT, prefix
SELECT * FROM products
WHERE search_vector @@ to_tsquery('english', 'bluetooth & (headphones | earbuds) & !wired')

-- Prefix search (for autocomplete)
SELECT * FROM products
WHERE search_vector @@ to_tsquery('english', 'wire:*')  -- matches "wireless", "wired", etc.

-- Highlighted excerpts
SELECT
  name,
  ts_headline('english', description,
    plainto_tsquery('english', 'wireless headphones'),
    'StartSel=<mark>, StopSel=</mark>, MaxWords=30'
  ) AS excerpt
FROM products
WHERE search_vector @@ plainto_tsquery('english', 'wireless headphones')
```

## TypeScript + Node.js
```typescript
async function searchProducts(query: string, filters?: { minPrice?: number; category?: string }) {
  const tsQuery = query.split(/\s+/).filter(Boolean).map(w => `${w}:*`).join(' & ')
  // "wireless head" → "wireless:* & head:*" (prefix match on each word)

  let sql = `
    SELECT
      id, name, brand, price, category,
      ts_rank(search_vector, to_tsquery('english', $1)) AS rank
    FROM products
    WHERE search_vector @@ to_tsquery('english', $1)
  `
  const params: any[] = [tsQuery]

  if (filters?.minPrice) {
    params.push(filters.minPrice)
    sql += ` AND price >= $${params.length}`
  }
  if (filters?.category) {
    params.push(filters.category)
    sql += ` AND category = $${params.length}`
  }

  sql += ` ORDER BY rank DESC, name ASC LIMIT 20`

  return db.query(sql, params)
}
```

# MEILISEARCH — FULL-FEATURED SELF-HOSTED

## Index Setup
```typescript
import { MeiliSearch } from 'meilisearch'

const client = new MeiliSearch({ host: 'http://localhost:7700', apiKey: process.env.MEILI_KEY! })
const index = client.index('products')

// Configure index settings
await index.updateSettings({
  searchableAttributes: ['name', 'brand', 'description', 'tags'],  // in priority order
  filterableAttributes: ['category', 'brand', 'inStock', 'price'], // for facets/filters
  sortableAttributes: ['price', 'rating', 'createdAt'],
  rankingRules: [
    'words',       // number of query words found
    'typo',        // fewer typos = higher rank
    'proximity',   // query words close together = higher rank
    'attribute',   // earlier in searchableAttributes = higher rank
    'sort',
    'exactness',
  ],
  typoTolerance: {
    enabled: true,
    minWordSizeForTypos: { oneTypo: 5, twoTypos: 9 }
  },
  pagination: { maxTotalHits: 1000 }
})
```

## Indexing Data
```typescript
// Bulk index — Meilisearch handles batching internally
async function indexProducts(products: Product[]) {
  const documents = products.map(p => ({
    id: p.id,
    name: p.name,
    brand: p.brand,
    description: p.description,
    category: p.category,
    price: p.price,
    rating: p.rating,
    inStock: p.inventoryCount > 0,
    tags: p.tags,
  }))

  const task = await index.addDocuments(documents, { primaryKey: 'id' })
  await client.waitForTask(task.taskUid)   // await indexing completion
  console.log(`Indexed ${documents.length} products`)
}

// Keep index in sync — call after DB writes
async function onProductUpdated(product: Product) {
  await index.updateDocuments([product])
}

async function onProductDeleted(productId: string) {
  await index.deleteDocument(productId)
}
```

## Search with Filters and Facets
```typescript
async function search(query: string, options: SearchOptions) {
  const result = await index.search(query, {
    limit: 20,
    offset: (options.page - 1) * 20,

    // Faceted filter
    filter: [
      options.category ? `category = "${options.category}"` : null,
      options.brand    ? `brand IN ["${options.brand.join('","')}"]` : null,
      options.maxPrice ? `price < ${options.maxPrice}` : null,
      'inStock = true',
    ].filter(Boolean).join(' AND '),

    // Sort
    sort: options.sort === 'price-asc' ? ['price:asc'] :
          options.sort === 'rating' ? ['rating:desc'] : [],

    // Facets for filtering UI
    facets: ['category', 'brand'],

    // Highlight matches
    highlightPreTag: '<mark>',
    highlightPostTag: '</mark>',
    attributesToHighlight: ['name', 'description'],
  })

  return {
    hits: result.hits,
    total: result.estimatedTotalHits,
    facets: result.facetDistribution,   // { category: { Electronics: 45, ... }, ... }
  }
}
```

# ELASTICSEARCH — LARGE-SCALE SEARCH

## Index Mapping
```typescript
import { Client } from '@elastic/elasticsearch'
const es = new Client({ node: process.env.ES_URL! })

await es.indices.create({
  index: 'products',
  body: {
    settings: {
      analysis: {
        analyzer: {
          product_analyzer: {
            type: 'custom',
            tokenizer: 'standard',
            filter: ['lowercase', 'stop', 'snowball']   // stemming
          }
        }
      }
    },
    mappings: {
      properties: {
        name:        { type: 'text', analyzer: 'product_analyzer', boost: 3 },
        brand:       { type: 'text', boost: 2, fields: { keyword: { type: 'keyword' } } },
        description: { type: 'text', analyzer: 'product_analyzer' },
        category:    { type: 'keyword' },   // exact match for filters
        price:       { type: 'float' },
        rating:      { type: 'float' },
        tags:        { type: 'keyword' },
        inStock:     { type: 'boolean' },
        createdAt:   { type: 'date' },
      }
    }
  }
})
```

## Search Query
```typescript
async function esSearch(query: string, filters: SearchFilters) {
  const { hits } = await es.search({
    index: 'products',
    body: {
      query: {
        bool: {
          must: [
            {
              multi_match: {
                query,
                fields: ['name^3', 'brand^2', 'description', 'tags'],
                fuzziness: 'AUTO',
                type: 'best_fields',
              }
            }
          ],
          filter: [
            filters.category && { term: { category: filters.category } },
            filters.inStock && { term: { inStock: true } },
            filters.maxPrice && { range: { price: { lte: filters.maxPrice } } },
          ].filter(Boolean)
        }
      },
      // Facet aggregations
      aggs: {
        categories: { terms: { field: 'category', size: 20 } },
        brands:     { terms: { field: 'brand.keyword', size: 20 } },
        priceRange: { stats: { field: 'price' } },
      },
      highlight: {
        fields: { name: {}, description: { fragment_size: 150 } }
      },
      from: filters.page * 20,
      size: 20,
    }
  })

  return hits
}
```

# AUTOCOMPLETE / TYPEAHEAD
```typescript
// Debounced search on frontend
function useAutocomplete(query: string, delay = 200) {
  const [suggestions, setSuggestions] = useState<string[]>([])
  const debouncedQuery = useDebounce(query, delay)

  useEffect(() => {
    if (debouncedQuery.length < 2) return setSuggestions([])

    fetch(`/api/search/autocomplete?q=${encodeURIComponent(debouncedQuery)}`)
      .then(r => r.json())
      .then(data => setSuggestions(data.suggestions))
  }, [debouncedQuery])

  return suggestions
}

// Server — autocomplete endpoint using PostgreSQL prefix search
app.get('/api/search/autocomplete', async (req, res) => {
  const q = (req.query.q as string)?.trim()
  if (!q || q.length < 2) return res.json({ suggestions: [] })

  const tsQuery = q.split(/\s+/).map(w => `${w}:*`).join(' & ')

  const results = await db.query(`
    SELECT DISTINCT name
    FROM products
    WHERE to_tsvector('english', name) @@ to_tsquery('english', $1)
    ORDER BY ts_rank(to_tsvector('english', name), to_tsquery('english', $1)) DESC
    LIMIT 8
  `, [tsQuery])

  res.json({ suggestions: results.rows.map(r => r.name) })
})
```

# VECTOR / SEMANTIC SEARCH
```typescript
// Find semantically similar products (not just keyword matches)
// "Show me something for listening to music on a run" → finds wireless sports earbuds

import OpenAI from 'openai'
const openai = new OpenAI()

// 1. At index time: generate and store embeddings
async function embedProduct(product: Product): Promise<number[]> {
  const input = `${product.name} ${product.brand} ${product.description}`
  const { data } = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input
  })
  return data[0].embedding   // 1536-dimensional vector
}

// Store in pgvector
// CREATE EXTENSION vector;
// ALTER TABLE products ADD COLUMN embedding vector(1536);
// CREATE INDEX ON products USING ivfflat (embedding vector_cosine_ops);

// 2. At search time: embed the query, find nearest neighbors
async function semanticSearch(query: string, limit = 10) {
  const queryEmbedding = await embedQuery(query)

  return db.query(`
    SELECT id, name, brand, price,
           1 - (embedding <=> $1::vector) AS similarity
    FROM products
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> $1::vector
    LIMIT $2
  `, [JSON.stringify(queryEmbedding), limit])
}

// 3. Hybrid search: combine keyword + semantic scores
async function hybridSearch(query: string) {
  const [keywordResults, semanticResults] = await Promise.all([
    searchProducts(query),
    semanticSearch(query)
  ])

  // RRF (Reciprocal Rank Fusion) to merge results
  const scores = new Map<string, number>()
  const k = 60  // RRF constant

  keywordResults.forEach((r, i) => {
    scores.set(r.id, (scores.get(r.id) ?? 0) + 1 / (k + i + 1))
  })
  semanticResults.forEach((r, i) => {
    scores.set(r.id, (scores.get(r.id) ?? 0) + 1 / (k + i + 1))
  })

  return [...scores.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 20)
    .map(([id]) => id)
}
```
