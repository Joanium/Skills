---
name: MongoDB
trigger: mongodb, mongo, mongoose, document database, NoSQL, collection, document, BSON, ObjectId, aggregation pipeline, index, replica set, sharding, atlas, mongosh, find, insertOne, updateOne, deleteOne, $match, $group, $lookup, $project, schema design, embedding vs referencing, TTL index, MongoDB atlas
description: Design MongoDB schemas, write efficient queries and aggregation pipelines, create proper indexes, and operate MongoDB in production.
---

# ROLE
You are a MongoDB database engineer. You design schemas optimized for query patterns (not normalized theory), write efficient aggregation pipelines, and apply the right indexing strategy. You know MongoDB's sweet spots — flexible schemas, horizontal scaling, document-oriented data — and when it's the wrong tool.

# CORE PRINCIPLES
```
DESIGN FOR YOUR QUERIES — embed what you read together; reference what you update independently
EMBED BY DEFAULT — referencing adds round-trips; embedding is faster
DOCUMENT SIZE LIMIT IS 16MB — very large docs or arrays should be references
INDEX EVERY QUERY FIELD — MongoDB won't warn you about full collection scans
AGGREGATION PIPELINES ARE POWERFUL — master them; $lookup replaces many JOINs
SCHEMA VALIDATION PREVENTS BAD DATA — use JSON Schema in production
ATLAS FOR PRODUCTION — managed backups, scaling, monitoring out of the box
```

# SCHEMA DESIGN

## Embedding vs Referencing
```javascript
// EMBED when:
// - Data is read together
// - Child data is owned by parent (1-to-few relationship)
// - Child data doesn't need to be queried independently
// - Array won't grow unboundedly

// Blog post with embedded comments (comments owned by post, < 100 expected)
{
  _id: ObjectId("..."),
  title: "MongoDB Schema Design",
  author: { name: "Alice", email: "alice@example.com" },  // embed author snapshot
  tags: ["mongodb", "nosql"],
  comments: [
    { _id: ObjectId("..."), text: "Great post!", user: "bob", createdAt: ISODate("...") }
  ],
  createdAt: ISODate("2024-01-15T10:00:00Z"),
  updatedAt: ISODate("2024-01-15T10:00:00Z")
}

// REFERENCE when:
// - Data is updated independently
// - Many-to-many relationships
// - Large or unbounded arrays
// - Data is shared across many documents

// Order references product (products updated independently, shared across orders)
{
  _id: ObjectId("..."),
  userId: ObjectId("..."),          // reference to users collection
  items: [
    {
      productId: ObjectId("..."),   // reference to products collection
      quantity: 2,
      priceAtOrder: 29.99           // snapshot of price (important: don't reference price)
    }
  ],
  status: "pending",
  total: 59.98,
  createdAt: ISODate("...")
}
```

## Schema Validation
```javascript
// Apply JSON Schema validation to enforce data quality
db.createCollection("users", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["email", "name", "role", "createdAt"],
      properties: {
        email: {
          bsonType: "string",
          pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
          description: "Must be a valid email"
        },
        name: {
          bsonType: "string",
          minLength: 2,
          maxLength: 100
        },
        role: {
          bsonType: "string",
          enum: ["user", "admin", "moderator"],
          description: "Must be one of user, admin, moderator"
        },
        age: {
          bsonType: "int",
          minimum: 0,
          maximum: 150
        },
        createdAt: { bsonType: "date" }
      }
    }
  },
  validationLevel: "strict",        // "strict" (default) or "moderate"
  validationAction: "error"         // "error" (default) or "warn"
});
```

# CRUD OPERATIONS

## Queries
```javascript
// Find by field
db.users.findOne({ email: "alice@example.com" })
db.users.find({ role: "admin" }).limit(10)

// Comparison operators
db.products.find({ price: { $gt: 10, $lte: 100 } })
db.users.find({ age: { $in: [25, 30, 35] } })
db.users.find({ role: { $ne: "admin" } })
db.users.find({ deletedAt: { $exists: false } })     // field doesn't exist
db.users.find({ email: { $regex: /gmail\.com$/i } }) // case-insensitive regex

// Logical operators
db.products.find({
  $and: [
    { price: { $lt: 50 } },
    { $or: [{ category: "books" }, { category: "electronics" }] }
  ]
})

// Nested fields and arrays
db.orders.find({ "address.city": "San Francisco" })       // dot notation
db.posts.find({ tags: "mongodb" })                        // array contains value
db.posts.find({ tags: { $all: ["mongodb", "nosql"] } })   // array contains all
db.posts.find({ tags: { $size: 3 } })                     // array has exactly 3 elements

// Projection — select/exclude fields
db.users.find({ role: "admin" }, { name: 1, email: 1 })           // include only
db.users.find({ role: "admin" }, { password: 0, __v: 0 })         // exclude only

// Sort, skip, limit (pagination)
db.posts.find({ status: "published" })
  .sort({ createdAt: -1 })
  .skip(20)
  .limit(10)
```

## Writes
```javascript
// Insert
db.users.insertOne({
  email: "alice@example.com",
  name: "Alice",
  role: "user",
  createdAt: new Date()
})

db.users.insertMany([...])

// Update
// updateOne: update first matching document
db.users.updateOne(
  { email: "alice@example.com" },
  {
    $set: { name: "Alice Smith", updatedAt: new Date() },
    $inc: { loginCount: 1 },       // increment by 1
    $push: { tags: "vip" },        // add to array
    $unset: { tempToken: "" }      // remove field
  }
)

// upsert: insert if not found
db.products.updateOne(
  { sku: "ABC123" },
  { $set: { price: 29.99, stock: 100 } },
  { upsert: true }
)

// findOneAndUpdate: returns document (before or after update)
const updated = db.orders.findOneAndUpdate(
  { _id: orderId, status: "pending" },
  { $set: { status: "processing" } },
  { returnDocument: "after" }
)

// Delete
db.users.deleteOne({ _id: userId })
db.sessions.deleteMany({ expiresAt: { $lt: new Date() } })
```

# AGGREGATION PIPELINE

## Common Pipeline Stages
```javascript
// Example: get top 5 authors by total post views in the last 30 days
db.posts.aggregate([
  // Stage 1: $match — filter early to reduce documents
  {
    $match: {
      status: "published",
      createdAt: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) }
    }
  },

  // Stage 2: $group — aggregate
  {
    $group: {
      _id: "$authorId",
      totalViews: { $sum: "$viewCount" },
      postCount: { $sum: 1 },
      avgViews: { $avg: "$viewCount" }
    }
  },

  // Stage 3: $lookup — JOIN with authors collection
  {
    $lookup: {
      from: "users",
      localField: "_id",
      foreignField: "_id",
      as: "author"
    }
  },

  // Stage 4: $unwind — flatten the array from $lookup
  { $unwind: "$author" },

  // Stage 5: $project — shape the output
  {
    $project: {
      _id: 0,
      authorName: "$author.name",
      authorEmail: "$author.email",
      totalViews: 1,
      postCount: 1,
      avgViews: { $round: ["$avgViews", 0] }
    }
  },

  // Stage 6: $sort and $limit — top 5
  { $sort: { totalViews: -1 } },
  { $limit: 5 }
])
```

## Useful Aggregation Patterns
```javascript
// Bucket data into ranges
db.orders.aggregate([
  {
    $bucket: {
      groupBy: "$total",
      boundaries: [0, 25, 50, 100, 200, Infinity],
      default: "Other",
      output: { count: { $sum: 1 }, revenue: { $sum: "$total" } }
    }
  }
])

// Add fields computed from existing data
{
  $addFields: {
    fullName: { $concat: ["$firstName", " ", "$lastName"] },
    isHighValue: { $gt: ["$total", 500] },
    year: { $year: "$createdAt" }
  }
}

// $facet: multiple pipelines on same input (for faceted search)
{
  $facet: {
    byCategory: [{ $group: { _id: "$category", count: { $sum: 1 } } }],
    byPriceRange: [{ $bucket: { groupBy: "$price", ... } }],
    total: [{ $count: "count" }]
  }
}
```

# INDEXES

```javascript
// Single field
db.users.createIndex({ email: 1 }, { unique: true })
db.posts.createIndex({ status: 1 })

// Compound index — field order matters; matches queries on prefix fields
db.posts.createIndex({ status: 1, createdAt: -1 })
// Supports: {status}, {status, createdAt} — NOT {createdAt} alone

// Text search index
db.articles.createIndex({ title: "text", body: "text" }, { weights: { title: 3, body: 1 } })
db.articles.find({ $text: { $search: "mongodb aggregation" } })

// TTL index — auto-delete documents after a time
db.sessions.createIndex({ expiresAt: 1 }, { expireAfterSeconds: 0 })
// MongoDB deletes documents where expiresAt < now

// Partial index — only index documents matching a filter
db.users.createIndex(
  { email: 1 },
  { partialFilterExpression: { role: "admin" } }
)

// Explain — analyze query execution
db.posts.find({ status: "published" }).explain("executionStats")
// Look for: COLLSCAN (bad) vs IXSCAN (good)
// Look for: "nReturned" vs "totalDocsExamined" — high ratio = good index

// List and drop indexes
db.users.getIndexes()
db.users.dropIndex("email_1")
```

# QUICK WINS CHECKLIST
```
Schema:
[ ] Document structure designed for read patterns (embed vs reference decision made)
[ ] Schema validation applied to collections with required fields
[ ] Timestamps (createdAt, updatedAt) on all documents
[ ] Sensitive fields excluded from default projections

Queries:
[ ] .explain("executionStats") run on slow queries — no COLLSCAN on large collections
[ ] Queries filter early ($match as first stage in aggregation)
[ ] No $where (runs JS, slow) — use query operators instead
[ ] Projections used to return only needed fields

Indexes:
[ ] Unique index on email and other natural unique keys
[ ] Compound indexes match the most common query patterns
[ ] TTL index on ephemeral collections (sessions, tokens, logs)
[ ] db.collection.getIndexes() reviewed — no duplicate or unused indexes

Production:
[ ] Replica set configured (never single node in production)
[ ] Connection pool sized appropriately (default 100)
[ ] Slow query log enabled (slowms threshold set)
[ ] Regular backups tested and verified
[ ] Atlas or equivalent managed service used for operations
```
