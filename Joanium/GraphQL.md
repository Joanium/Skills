---
name: GraphQL
trigger: graphql, GraphQL, gql, query, mutation, subscription, resolver, schema, type, SDL, Apollo, relay, dataloader, N+1, fragment, variable, directive, introspection, codegen, federation, GraphQL server, GraphQL client
description: Design and implement GraphQL APIs. Covers schema design, resolvers, mutations, subscriptions, DataLoader for N+1 prevention, authentication, and client patterns.
---

# ROLE
You are a GraphQL API engineer. You design clean, consistent schemas, write efficient resolvers, prevent N+1 queries, and choose the right patterns for complex data requirements. You know GraphQL's strengths — flexible querying, strong typing, self-documentation — and its pitfalls.

# CORE PRINCIPLES
```
SCHEMA IS THE CONTRACT — design it collaboratively with frontend; changes are breaking
THINK IN GRAPHS — model your domain as nodes and edges, not endpoints
RESOLVE LAZILY — only compute what was requested
DATALOADER PREVENTS N+1 — never query per-item in resolvers; always batch
MUTATIONS RETURN THE MUTATED TYPE — not just success/failure
ERRORS HAVE A SCHEMA TOO — union types for expected errors, errors[] for validation
AUTHORIZATION IN RESOLVERS, NOT TYPES — field-level access control
```

# SCHEMA DESIGN

## SDL Type Definitions
```graphql
# Scalar types: String, Int, Float, Boolean, ID (plus custom scalars)
scalar DateTime
scalar JSON
scalar URL

# Object types
type User {
  id: ID!                     # ! = non-null (required)
  email: String!
  name: String!
  role: UserRole!
  posts(
    first: Int = 10           # field arguments with defaults
    after: String             # cursor for pagination
    status: PostStatus
  ): PostConnection!
  createdAt: DateTime!
  updatedAt: DateTime!
}

# Enum
enum UserRole {
  USER
  ADMIN
  MODERATOR
}

enum PostStatus {
  DRAFT
  PUBLISHED
  ARCHIVED
}

# Interface — common fields shared by multiple types
interface Node {
  id: ID!
}

interface Timestamped {
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Post implements Node & Timestamped {
  id: ID!
  title: String!
  body: String!
  status: PostStatus!
  author: User!
  tags: [String!]!              # non-null list of non-null strings
  viewCount: Int!
  createdAt: DateTime!
  updatedAt: DateTime!
}

# Union — a field that can be one of several types
union SearchResult = User | Post | Comment

# Input types — for mutations and complex arguments
input CreatePostInput {
  title: String!
  body: String!
  tags: [String!]
  status: PostStatus = DRAFT
}

input UpdatePostInput {
  title: String
  body: String
  tags: [String!]
  status: PostStatus
}
```

## Pagination — Cursor-Based (Relay Spec)
```graphql
# Connection pattern — standard for paginated lists
type PostConnection {
  edges: [PostEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type PostEdge {
  node: Post!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

# Root query using connection
type Query {
  posts(
    first: Int
    after: String
    last: Int
    before: String
    filter: PostFilter
    orderBy: PostOrderBy
  ): PostConnection!
}
```

## Mutations with Error Unions
```graphql
# Explicit error types (better than generic errors)
type ValidationError {
  field: String!
  message: String!
}

type AuthError {
  message: String!
  code: AuthErrorCode!
}

enum AuthErrorCode {
  UNAUTHENTICATED
  UNAUTHORIZED
}

type NotFoundError {
  message: String!
  id: ID!
}

# Mutation result as union
union CreatePostResult = Post | ValidationError | AuthError

type Mutation {
  createPost(input: CreatePostInput!): CreatePostResult!
  updatePost(id: ID!, input: UpdatePostInput!): UpdatePostResult!
  deletePost(id: ID!): DeletePostResult!
  publishPost(id: ID!): PublishPostResult!
}

# Clients can use inline fragments to handle each case:
# mutation {
#   createPost(input: $input) {
#     ... on Post { id title }
#     ... on ValidationError { field message }
#     ... on AuthError { message code }
#   }
# }
```

# RESOLVERS

## Resolver Structure (Node.js / Apollo Server)
```typescript
import { Resolvers } from "./generated/types";   // codegen types

export const resolvers: Resolvers = {
  Query: {
    // Root query resolver
    user: async (_, { id }, context) => {
      if (!context.user) throw new AuthenticationError("Not authenticated");
      return context.loaders.user.load(id);   // DataLoader for batching
    },

    posts: async (_, args, context) => {
      const { first = 10, after, filter } = args;
      return context.services.post.paginate({ first, after, filter });
    },

    me: async (_, __, context) => {
      if (!context.user) throw new AuthenticationError("Not authenticated");
      return context.user;
    },
  },

  Mutation: {
    createPost: async (_, { input }, context) => {
      if (!context.user) return { __typename: "AuthError", message: "Not authenticated", code: "UNAUTHENTICATED" };

      const validation = validateCreatePost(input);
      if (validation.errors.length) {
        return { __typename: "ValidationError", ...validation.errors[0] };
      }

      const post = await context.services.post.create({
        ...input,
        authorId: context.user.id,
      });
      return { __typename: "Post", ...post };
    },
  },

  // Field resolvers — run for EACH instance of that type
  User: {
    posts: async (parent, args, context) => {
      // parent = the User object; DON'T query DB here without DataLoader
      return context.loaders.postsByUser.load(parent.id);
    },
    role: (parent) => parent.role.toUpperCase(),   // transform DB value to enum
  },

  // Union/Interface type resolver
  SearchResult: {
    __resolveType(obj) {
      if (obj.email) return "User";
      if (obj.title) return "Post";
      return null;
    },
  },
};
```

## DataLoader — Preventing N+1 Queries
```typescript
import DataLoader from "dataloader";

// WITHOUT DataLoader: 1 query for users list + 1 query per user's posts = N+1
// WITH DataLoader: 1 query for users list + 1 batched query for ALL posts

// Create loaders (one per request — do NOT share across requests)
function createLoaders(db: Database) {
  return {
    // Batch: receive array of user IDs, return array of users
    user: new DataLoader<string, User>(async (ids) => {
      const users = await db.users.findByIds([...ids]);
      const map = new Map(users.map(u => [u.id, u]));
      return ids.map(id => map.get(id) ?? new Error(`User ${id} not found`));
    }),

    // Posts by user — batched lookup
    postsByUser: new DataLoader<string, Post[]>(async (userIds) => {
      const posts = await db.posts.findByUserIds([...userIds]);
      const grouped = new Map<string, Post[]>();
      for (const post of posts) {
        const list = grouped.get(post.authorId) ?? [];
        list.push(post);
        grouped.set(post.authorId, list);
      }
      return userIds.map(id => grouped.get(id) ?? []);
    }),
  };
}

// In Apollo Server context — loaders created fresh per request
const server = new ApolloServer({
  typeDefs,
  resolvers,
  context: ({ req }) => ({
    user: getUserFromRequest(req),
    loaders: createLoaders(db),     // new loaders per request!
    services: createServices(db),
  }),
});
```

# CLIENT QUERIES

## Query with Fragments and Variables
```graphql
# Fragment — reusable field selection
fragment PostFields on Post {
  id
  title
  status
  viewCount
  createdAt
  author {
    id
    name
  }
}

fragment PageInfoFields on PageInfo {
  hasNextPage
  endCursor
}

# Query using fragments and variables
query GetPublishedPosts($first: Int = 10, $after: String) {
  posts(first: $first, after: $after, filter: { status: PUBLISHED }) {
    edges {
      node {
        ...PostFields
        tags
      }
    }
    pageInfo {
      ...PageInfoFields
    }
    totalCount
  }
}

# Mutation
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on Post {
      id
      title
      status
    }
    ... on ValidationError {
      field
      message
    }
    ... on AuthError {
      message
      code
    }
  }
}
```

## Apollo Client (React)
```tsx
import { useQuery, useMutation } from "@apollo/client";

function PostList() {
  const { data, loading, error, fetchMore } = useQuery(GET_POSTS, {
    variables: { first: 10 },
    notifyOnNetworkStatusChange: true,
  });

  const loadMore = () => {
    fetchMore({
      variables: { after: data?.posts.pageInfo.endCursor },
      updateQuery: (prev, { fetchMoreResult }) => ({
        posts: {
          ...fetchMoreResult.posts,
          edges: [...prev.posts.edges, ...fetchMoreResult.posts.edges],
        },
      }),
    });
  };

  if (loading && !data) return <Spinner />;
  if (error) return <Error message={error.message} />;

  return (
    <>
      {data.posts.edges.map(({ node }) => <PostCard key={node.id} post={node} />)}
      {data.posts.pageInfo.hasNextPage && (
        <button onClick={loadMore} disabled={loading}>Load more</button>
      )}
    </>
  );
}

function CreatePostForm() {
  const [createPost, { loading }] = useMutation(CREATE_POST, {
    update(cache, { data: { createPost } }) {
      if (createPost.__typename !== "Post") return;
      // Update Apollo cache to include new post
      cache.modify({
        fields: {
          posts(existing) {
            const newRef = cache.writeFragment({ data: createPost, fragment: POST_FIELDS });
            return { ...existing, edges: [{ node: newRef }, ...existing.edges] };
          },
        },
      });
    },
  });
}
```

# QUICK WINS CHECKLIST
```
Schema:
[ ] All fields have types (no implicit any)
[ ] Non-null (!) on all required fields
[ ] Input types used for mutation arguments
[ ] Error types in union returns (not just generic errors)
[ ] Connection pattern for all paginated lists
[ ] Custom scalars for DateTime, URL, etc.

Resolvers:
[ ] DataLoader used for all field resolvers that hit the database
[ ] Authorization checked in resolvers (not schema types)
[ ] N+1 verified: no DB queries inside loops
[ ] Context contains user auth state, loaders, services

Performance:
[ ] Query complexity limiting configured (prevent deeply nested queries)
[ ] Query depth limiting configured
[ ] Persisted queries for production clients
[ ] Introspection disabled in production

Tooling:
[ ] GraphQL Code Generator set up (types from schema)
[ ] Schema linting (graphql-eslint)
[ ] Apollo Studio or GraphiQL for developer exploration
[ ] Schema registry for federation/versioning
```
