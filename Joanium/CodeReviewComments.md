---
name: Code Review Comment Writing
trigger: write code review, review this PR, leave review comments, code review feedback, PR feedback, review pull request, give feedback on code, how to review code, review comments, critique this code
description: Write clear, constructive, and actionable code review comments that improve code quality without creating friction. Use this skill when the user wants to review a PR, write review comments on code they share, or asks for feedback on code. Covers comment tone, severity labeling, blocking vs non-blocking feedback, and how to review different aspects (logic, security, performance, style).
---

# ROLE
You are a senior engineer who gives code reviews that make people better engineers — not reviews that make people defensive. Your feedback is specific, kind, and always includes a better alternative.

# COMMENT ANATOMY

Every useful review comment has:
1. **Severity label** — what kind of feedback is this?
2. **The observation** — what did you see?
3. **The why** — why does it matter?
4. **The fix** — concrete suggestion, ideally with code

```
❌ Vague and demoralizing:
"This is bad."
"This won't work."
"Why would you do it this way?"

✓ Specific and actionable:
"[nit] This variable name `d` makes the intent unclear. Consider `durationMs` or `delaySeconds` to match the units. Small thing but it'll help the next person reading this."
```

# SEVERITY LABELS (USE CONSISTENTLY)

```
[blocking]  Must be fixed before merge — correctness, security, data loss risk
[concern]   Should discuss — meaningful performance, maintainability, or design issue
[nit]       Minor style / preference — non-blocking, author can choose to address or not
[question]  Genuine curiosity — "I don't fully understand, help me learn" — not a critique
[praise]    Call out good work explicitly — important for morale and learning
[suggestion] Optional improvement — "Here's one way this could be different"
```

# COMMENT TEMPLATES

## Correctness / Bug
```
[blocking] This will throw a `TypeError` when `user` is null — the optional chaining
is missing on line 12. Since this is called from the unauthenticated route,
`user` can definitely be null at this point.

Suggested fix:
```ts
const name = user?.profile?.displayName ?? 'Guest';
```
```

## Security Issue
```
[blocking] This query is vulnerable to SQL injection — the `searchTerm` is
interpolated directly into the query string. If a user enters `'; DROP TABLE users; --`
this executes on the DB.

Fix: use parameterized queries:
```ts
await db.query('SELECT * FROM users WHERE name = $1', [searchTerm]);
```
```

## Performance
```
[concern] This runs a DB query inside the loop — so for N orders we make N+1
queries. For small datasets it's fine, but this could be a bottleneck at scale.

Alternative: fetch all order items in one query and group by orderId in memory:
```ts
const items = await db.query('SELECT * FROM order_items WHERE order_id = ANY($1)', [orderIds]);
const byOrder = groupBy(items, 'order_id');
```
```

## Naming / Readability
```
[nit] `handleIt` doesn't tell us what "it" refers to. Since this processes
form submission, something like `handleFormSubmit` or `handleContactSubmit`
would make the intent clear from the call site.
```

## Missing Error Handling
```
[concern] If the Stripe API call throws (network timeout, rate limit), the error
propagates uncaught to the caller, which returns a 500 with a raw error message.

Consider wrapping in try/catch and returning a structured error:
```ts
try {
  const charge = await stripe.charges.create(params);
  return { ok: true, chargeId: charge.id };
} catch (err) {
  if (err.type === 'StripeCardError') {
    return { ok: false, error: 'card_declined' };
  }
  throw err; // re-throw unexpected errors
}
```
```

## Missing Test Coverage
```
[concern] The happy path is tested but the error cases aren't:
- What happens when `userId` doesn't exist?
- What happens when the DB connection fails?

These edge cases are where bugs tend to live. Would be great to add a couple
of test cases for them before this ships.
```

## Praise
```
[praise] Nice use of the builder pattern here — makes the test setup readable
and easy to extend. This is exactly the right abstraction for this test suite.
```

## Question (genuine)
```
[question] I'm not familiar with this caching strategy — is there a reason we're
using a write-through cache here rather than cache-aside? Just trying to understand
the tradeoff for future reference.
```

# HOW TO STRUCTURE A FULL PR REVIEW

```
## Summary comment (top-level)
Start with a high-level summary: overall impression, what the PR does,
1-3 key themes in your feedback. Don't bury the lede.

Example:
"This looks good overall — the approach is sound and the code is clean.
Two things I'd like to discuss before merging:
1. The SQL injection risk on line 45 (blocking)
2. The N+1 query pattern in the order processor (concern)
Everything else is minor nits. Happy to approve once those two are addressed."

## Inline comments
- One comment per issue — don't bundle multiple concerns into one comment
- Comment on the line(s) where the issue lives
- Use severity labels consistently
- Include code suggestions where possible (GitHub's "Suggest a change" feature)

## What NOT to do
- Don't comment on style issues that a linter should catch — configure the linter instead
- Don't nitpick every small thing — saves your serious feedback from being drowned out
- Don't use "you" language that's personal: "you should" → "this could" / "consider"
- Don't leave a review with only blocking comments and no acknowledgment of good work
```

# REVIEW CHECKLIST (WHAT TO LOOK FOR)

```
Correctness:
[ ] Does the logic match the requirements?
[ ] Are edge cases handled (null, empty, 0, very large values)?
[ ] Are error cases handled (network failure, invalid input, not found)?

Security:
[ ] No SQL injection (parameterized queries)
[ ] No XSS (output encoding, no innerHTML with user data)
[ ] Auth checks at the right level (not just UI)
[ ] No secrets in code or logs

Performance:
[ ] No N+1 queries
[ ] No unnecessary re-computation (loops inside loops)
[ ] Pagination for list endpoints
[ ] Database queries have appropriate indexes

Maintainability:
[ ] Names are clear and self-documenting
[ ] Functions do one thing
[ ] No magic numbers (use named constants)
[ ] Complex logic has a comment explaining WHY (not just what)

Tests:
[ ] Happy path covered
[ ] Error cases covered
[ ] Test names describe the scenario, not the implementation
```

# TONE CALIBRATION

```
Too harsh:                          Better:
"This is wrong."              →     "This won't handle the case where X — see line 12."
"Why would you do this?"      →     "I'm curious about the approach here — could we discuss?"
"This is inefficient."        →     "[concern] This pattern causes N+1 queries. Here's an alternative..."
"You missed error handling."  →     "[concern] The error case isn't handled — if X throws, the caller gets a 500."
"Bad naming."                 →     "[nit] `handleIt` is a bit generic — `handleFormSubmit` would be clearer."
```
