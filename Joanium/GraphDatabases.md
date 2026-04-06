---
name: GraphDatabases
description: Design and query graph databases including Neo4j, Amazon Neptune, and ArangoDB. Use when the user asks about graph data modeling, Cypher queries, graph traversals, relationship-heavy data, recommendation engines, social networks, fraud detection, or knowledge graphs.
---

You are an expert in graph database design and development, specializing in Neo4j (Cypher), Amazon Neptune (Gremlin/SPARQL), ArangoDB (AQL), and graph data modeling for domains including social networks, recommendation engines, fraud detection, knowledge graphs, and supply chains.

The user provides a graph database task: designing a graph schema, writing Cypher/Gremlin queries, modeling relationships, building a recommendation engine, optimizing traversal performance, or migrating from relational to graph.

## When to Use a Graph Database

Graph databases outperform relational DBs when:

- **Relationships are first-class**: the connections between entities are as important as the entities themselves
- **Variable-depth traversals**: "find all friends of friends up to 3 hops" — trivial in graph, expensive JOINs in SQL
- **Highly connected data**: social networks, org charts, dependency graphs, knowledge bases
- **Pattern matching**: fraud rings, recommendation paths, network topology

Stick with relational when:

- Data is tabular with simple, predictable relationships
- You need complex aggregations over large flat datasets
- Your team has no graph expertise and the problem isn't inherently graph-shaped

## Graph Data Modeling

**Core Primitives**

- **Nodes**: entities (User, Product, Order, Concept)
- **Relationships**: typed, directional connections between nodes (`[:KNOWS]`, `[:PURCHASED]`, `[:LOCATED_IN]`)
- **Properties**: key-value pairs on both nodes and relationships
- **Labels**: node type categories; a node can have multiple labels

**Modeling Principles**

- Model **nouns as nodes**, **verbs as relationships**
- Put frequently-queried properties on the node; put relationship-specific data on the relationship
- Avoid storing arrays of IDs as node properties — make them actual relationships
- Use relationship properties for temporal data (`since`, `weight`, `createdAt`)

**Example: Social Network**

```cypher
// Nodes
(:User {id, name, email, joinedAt})
(:Post {id, content, createdAt})
(:Topic {name})
(:Location {city, country})

// Relationships
(:User)-[:KNOWS {since, strength}]->(:User)
(:User)-[:POSTED]->(:Post)
(:User)-[:LIVES_IN]->(:Location)
(:Post)-[:TAGGED_WITH]->(:Topic)
(:User)-[:INTERESTED_IN]->(:Topic)
(:User)-[:LIKED {at}]->(:Post)
```

**Anti-Patterns**

- ❌ Super-nodes: a node with millions of relationships (e.g., a "Twitter" node connected to all users) — paginate or partition
- ❌ Generic relationship types: `[:RELATED_TO]` — be specific (`[:PARENT_OF]`, `[:DEPENDS_ON]`)
- ❌ Duplicate relationships in both directions — use directionality and query bidirectionally
- ❌ Storing JSON blobs as properties — model sub-entities as nodes

## Cypher (Neo4j)

**Basic CRUD**

```cypher
// Create
CREATE (u:User {id: 'u1', name: 'Joel', email: 'joel@example.com', joinedAt: datetime()})

// Create relationship
MATCH (a:User {id: 'u1'}), (b:User {id: 'u2'})
CREATE (a)-[:KNOWS {since: date('2024-01-01'), strength: 0.8}]->(b)

// Read — find user and their friends
MATCH (u:User {id: 'u1'})-[:KNOWS]->(friend:User)
RETURN u.name AS user, collect(friend.name) AS friends

// Update
MATCH (u:User {id: 'u1'})
SET u.lastActive = datetime(), u.postCount = u.postCount + 1

// Delete node and all its relationships
MATCH (u:User {id: 'u1'})
DETACH DELETE u
```

**Pattern Matching**

```cypher
// Variable-length paths — friends up to 3 hops away
MATCH (start:User {id: 'u1'})-[:KNOWS*1..3]-(person:User)
WHERE person.id <> 'u1'
RETURN DISTINCT person.name, person.id

// Shortest path
MATCH (a:User {id: 'u1'}), (b:User {id: 'u99'})
CALL apoc.algo.dijkstra(a, b, 'KNOWS', 'strength') YIELD path, weight
RETURN path, weight

// Optional match (like LEFT JOIN)
MATCH (u:User {id: 'u1'})
OPTIONAL MATCH (u)-[:POSTED]->(p:Post)
RETURN u.name, count(p) AS postCount
```

**Aggregations**

```cypher
// Top 10 most connected users
MATCH (u:User)-[:KNOWS]-()
RETURN u.name, count(*) AS connections
ORDER BY connections DESC LIMIT 10

// Common connections between two users
MATCH (a:User {id: 'u1'})-[:KNOWS]->(common)<-[:KNOWS]-(b:User {id: 'u2'})
RETURN common.name

// Users who liked posts tagged with a topic a user is interested in
MATCH (u:User {id: 'u1'})-[:INTERESTED_IN]->(t:Topic)<-[:TAGGED_WITH]-(p:Post)
WHERE NOT (u)-[:LIKED]->(p)
WITH p, count(t) AS relevance
ORDER BY relevance DESC
RETURN p.id, p.content LIMIT 10
```

**Recommendation Queries**

```cypher
// Collaborative filtering: "Users like you also liked"
MATCH (me:User {id: $userId})-[:LIKED]->(p:Post)<-[:LIKED]-(similar:User)
WHERE similar.id <> $userId
WITH similar, count(p) AS commonLikes
ORDER BY commonLikes DESC LIMIT 10
MATCH (similar)-[:LIKED]->(rec:Post)
WHERE NOT (me)-[:LIKED]->(rec)
RETURN rec, count(*) AS score
ORDER BY score DESC LIMIT 20

// Content-based: recommend based on topics of interest
MATCH (me:User {id: $userId})-[:INTERESTED_IN]->(topic:Topic)
MATCH (topic)<-[:TAGGED_WITH]-(post:Post)
WHERE NOT (me)-[:LIKED]->(post)
  AND NOT (me)-[:POSTED]->(post)
RETURN post, count(topic) AS topicMatch
ORDER BY topicMatch DESC LIMIT 20
```

**Fraud Detection Pattern**

```cypher
// Find users sharing device fingerprints (potential fraud ring)
MATCH (u1:User)-[:USED_DEVICE]->(d:Device)<-[:USED_DEVICE]-(u2:User)
WHERE u1.id <> u2.id
WITH u1, u2, d, count(d) AS sharedDevices
WHERE sharedDevices >= 2
RETURN u1.id, u2.id, collect(d.fingerprint) AS devices

// Ring detection — circular transaction chains
MATCH path = (a:Account)-[:SENT_TO*3..6]->(a)
WHERE all(r IN relationships(path) WHERE r.amount > 1000)
RETURN path, length(path) AS ringSize
ORDER BY ringSize
```

## Performance Optimization

**Indexes**

```cypher
// Create indexes for frequently queried properties
CREATE INDEX user_id FOR (u:User) ON (u.id)
CREATE INDEX user_email FOR (u:User) ON (u.email)

// Composite index
CREATE INDEX post_topic_date FOR (p:Post) ON (p.topicId, p.createdAt)

// Full-text index (for text search)
CALL db.index.fulltext.createNodeIndex('postSearch', ['Post'], ['content', 'title'])
CALL db.index.fulltext.queryNodes('postSearch', 'machine learning') YIELD node, score
RETURN node.title, score ORDER BY score DESC
```

**Query Optimization**

- Always start a MATCH from the most selective node (smallest set)
- Use `PROFILE` or `EXPLAIN` to inspect query plans
- Limit variable-length paths: `[:KNOWS*1..4]` not `[:KNOWS*]`
- Use `WITH` to filter early and reduce cardinality mid-query
- Avoid `OPTIONAL MATCH` inside loops — rewrite as separate queries

**apoc (Neo4j Procedures)**

```cypher
// Parallel relationship creation
CALL apoc.periodic.iterate(
  'MATCH (a:User) RETURN a',
  'MATCH (b:User) WHERE b.city = a.city AND b.id <> a.id
   MERGE (a)-[:SAME_CITY]->(b)',
  {batchSize: 1000, parallel: true}
)

// Graph algorithms (GDS library)
CALL gds.pageRank.stream('myGraph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS name, score
ORDER BY score DESC LIMIT 10
```

## Gremlin (Amazon Neptune, TinkerPop)

```groovy
// Add vertex
g.addV('User').property('id', 'u1').property('name', 'Joel').next()

// Add edge
g.V().has('User', 'id', 'u1').as('a')
 .V().has('User', 'id', 'u2').as('b')
 .addE('KNOWS').from('a').to('b').property('since', '2024').next()

// Traverse — 2-hop friends
g.V().has('User', 'id', 'u1').out('KNOWS').out('KNOWS')
 .where(neq('start')).by('id').dedup().valueMap('name').toList()

// Recommendation
g.V().has('User', 'id', 'u1').out('LIKED').in('LIKED')
 .where(neq('me')).out('LIKED')
 .where(__.not(__.in('LIKED').has('User', 'id', 'u1')))
 .groupCount().order(local).by(values, desc).limit(local, 10)
```

## Schema Evolution

- Neo4j is schema-optional: add labels, properties, relationships without migrations
- Track schema versions with a `:SchemaVersion` node
- Use `MERGE` instead of `CREATE` for idempotent upserts:
  ```cypher
  MERGE (u:User {id: $id})
  ON CREATE SET u.createdAt = datetime(), u.name = $name
  ON MATCH SET u.updatedAt = datetime()
  ```
- Backfill new relationships in batches with `apoc.periodic.iterate`
