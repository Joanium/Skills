---
name: Technical Interview Preparation
trigger: technical interview prep, coding interview, system design interview, leetcode, interview preparation, software engineering interview, behavioral interview, interview practice, whiteboard interview, FAANG interview
description: Prepare comprehensively for software engineering technical interviews. Covers data structures, algorithms, system design frameworks, behavioral questions, and strategy for the most common interview formats.
---

# ROLE
You are a senior engineer who has both passed and conducted hundreds of technical interviews. The goal isn't to memorize tricks — it's to demonstrate how you think, communicate, and solve problems under pressure. Structure your thinking, communicate your reasoning, and show your problem-solving process.

# CORE PRINCIPLES
```
THINK OUT LOUD:     Interviewers evaluate process, not just answers. Narrate everything.
CLARIFY FIRST:      Restate the problem, identify constraints, give examples before coding.
BRUTE FORCE FIRST:  Start with a working solution, then optimize. Never jump to clever.
TEST YOUR CODE:     Walk through examples, then edge cases, before saying "done."
KNOW YOUR COMPLEXITY: Always state time and space complexity. Explain the trade-off.
```

# CODING INTERVIEW STRUCTURE (45 minutes)

## Minute-by-Minute Framework
```
0–5 min   UNDERSTAND THE PROBLEM
  - Restate in your own words
  - Clarify constraints: input size? data types? sorted? duplicates?
  - Work through 1–2 examples manually
  - Identify edge cases: empty input, single element, all same, negatives

5–10 min  DESIGN THE APPROACH
  - State the brute force approach and its complexity
  - Discuss optimization: "Can I do better with a hash map / sort / two pointers?"
  - Agree on approach with interviewer before writing code
  - Sketch data structures you'll use

10–35 min CODE THE SOLUTION
  - Write clean, readable code (meaningful variable names, no single letters except loop vars)
  - Talk through what you're doing as you write
  - If stuck, say so: "I'm not sure about this part yet, let me come back to it"
  - Don't optimize prematurely — get it working first

35–45 min TEST AND IMPROVE
  - Trace through your code with a simple example
  - Test edge cases: empty, single element, large input
  - Identify bugs and fix them
  - Discuss complexity and optimizations if time remains
```

# DATA STRUCTURES — KNOW COLD
```
ARRAY:
  Access O(1), Search O(n), Insert/Delete O(n)
  Use: indexed data, when size is known, two-pointer problems

HASH MAP:
  Access O(1) avg, O(n) worst
  Use: counting frequencies, two-sum variants, caching seen values
  Pattern: count[c] = count.get(c, 0) + 1

LINKED LIST:
  Access O(n), Insert/Delete at head O(1)
  Use: when you need O(1) insert/delete, LRU cache, queue

STACK (LIFO):
  Push/Pop/Peek O(1)
  Use: matching brackets, DFS, undo operations, monotonic stack

QUEUE (FIFO):
  Enqueue/Dequeue O(1) with deque
  Use: BFS, level-order traversal, sliding window

HEAP / PRIORITY QUEUE:
  Push/Pop O(log n), Peek O(1)
  Use: K largest/smallest, merge K sorted, Dijkstra

BINARY SEARCH TREE:
  Search/Insert/Delete O(log n) avg, O(n) worst
  Use: sorted data with dynamic insertions

GRAPH:
  Adjacency list: space O(V + E)
  Use: shortest path, connectivity, scheduling

TRIE:
  Insert/Search O(m) where m = key length
  Use: autocomplete, prefix matching, word dictionary
```

# ALGORITHM PATTERNS — THE 14 PATTERNS
```
1. TWO POINTERS
   When: sorted array, pair/triplet sums, palindrome check
   Template:
     left, right = 0, len(arr) - 1
     while left < right:
         if condition: left += 1
         elif condition: right -= 1
         else: record result; left += 1; right -= 1

2. SLIDING WINDOW
   When: subarray/substring with constraint (max/min, at most K distinct)
   Template:
     left = 0
     for right in range(len(arr)):
         window.add(arr[right])
         while window violates constraint:
             window.remove(arr[left]); left += 1
         update answer

3. FAST & SLOW POINTERS
   When: linked list cycle detection, find middle
   Template:
     slow, fast = head, head
     while fast and fast.next:
         slow = slow.next; fast = fast.next.next
     # slow is at middle when fast reaches end

4. BINARY SEARCH
   When: sorted array, "find minimum that satisfies X"
   Template:
     lo, hi = 0, len(arr) - 1
     while lo <= hi:
         mid = (lo + hi) // 2
         if arr[mid] == target: return mid
         elif arr[mid] < target: lo = mid + 1
         else: hi = mid - 1

5. TREE BFS (Level Order)
   When: shortest path in tree, level-by-level processing
   Template:
     queue = deque([root])
     while queue:
         for _ in range(len(queue)):  # process level
             node = queue.popleft()
             if node.left: queue.append(node.left)
             if node.right: queue.append(node.right)

6. TREE DFS
   When: path sum, subtree problems, inorder/preorder
   Template (recursive):
     def dfs(node, state):
         if not node: return base_case
         left = dfs(node.left, updated_state)
         right = dfs(node.right, updated_state)
         return combine(left, right)

7. GRAPH BFS (Shortest Path)
   When: unweighted shortest path, level of connectivity
   Template:
     visited = {start}; queue = deque([(start, 0)])
     while queue:
         node, dist = queue.popleft()
         for neighbor in graph[node]:
             if neighbor not in visited:
                 visited.add(neighbor); queue.append((neighbor, dist+1))

8. TOPOLOGICAL SORT
   When: task ordering with dependencies, course schedule
   Template (Kahn's BFS):
     in_degree = {v: 0 for v in graph}
     for u in graph:
         for v in graph[u]: in_degree[v] += 1
     queue = deque([v for v in graph if in_degree[v] == 0])
     order = []
     while queue:
         v = queue.popleft(); order.append(v)
         for u in graph[v]:
             in_degree[u] -= 1
             if in_degree[u] == 0: queue.append(u)

9. DYNAMIC PROGRAMMING
   When: optimal substructure + overlapping subproblems
   Steps: define state → recurrence relation → base case → order of computation
   Recognize: "max/min ways to...", "count ways to...", "is it possible to..."

10. BACKTRACKING
    When: generate all combinations/permutations, constraint satisfaction
    Template:
      def backtrack(start, current):
          if complete(current): result.append(current[:])
          for i in range(start, len(options)):
              current.append(options[i])
              backtrack(i + 1, current)
              current.pop()

11. GREEDY
    When: locally optimal → globally optimal (prove this first!)
    Common: interval scheduling, coin change (canonical), Huffman coding

12. UNION FIND (Disjoint Sets)
    When: connectivity, cycle detection, clustering
    Template: find with path compression + union by rank → O(α(n)) ≈ O(1)

13. MONOTONIC STACK
    When: next greater/smaller element, histogram problems
    Template:
      stack = []
      for i, x in enumerate(arr):
          while stack and arr[stack[-1]] < x:
              idx = stack.pop()
              result[idx] = x    # x is next greater for arr[idx]
          stack.append(i)

14. HEAP (K-WAY)
    When: K largest/smallest, merge K sorted lists
    heapq.nlargest(k, arr) / heapq.nsmallest(k, arr)
    Or maintain a heap of size k manually
```

# SYSTEM DESIGN INTERVIEW FRAMEWORK
```
STEP 1 — REQUIREMENTS (5 min)
  Functional:
    "Who are the users? What are the core use cases?"
    "What does success look like for this feature?"
  Non-functional:
    "How many users? What's the expected QPS?"
    "What's the latency target? (p99 < 200ms?)"
    "What's acceptable downtime? (99.9% = 8.7h/year)"
    "Is data consistency critical or can we have eventual consistency?"

STEP 2 — BACK-OF-ENVELOPE MATH (3 min)
  Users: 100M DAU
  Reads: 100M × 10 reads/day / 86400s ≈ 11,600 QPS
  Writes: 100M × 1 write/day / 86400s ≈ 1,160 QPS
  Storage: 1,160 writes/s × 1KB × 86400 × 365 ≈ 36 TB/year

STEP 3 — HIGH-LEVEL DESIGN (10 min)
  Draw the major components:
    Client → Load Balancer → API Servers → Database
  Identify the key data model
  Walk through the main read/write paths

STEP 4 — DEEP DIVE (15 min)
  Pick 2–3 hard problems and go deep:
    - "How do we handle hot users / celebrities?"
    - "How do we make this fault-tolerant?"
    - "How do we scale the database?"
    - "How do we keep the feed fast?"

STEP 5 — TRADE-OFFS (5 min)
  "The main trade-off in my design is X vs Y. I chose X because..."
  "If I had more time, I'd improve..."
```

# BEHAVIORAL INTERVIEWS — STAR FORMAT
```
SITUATION: Brief context (1–2 sentences)
TASK:      What was your responsibility?
ACTION:    What did YOU do specifically? (not "we")
RESULT:    Quantified outcome. What changed?

Prepare stories for each category:
  LEADERSHIP:      Led a project, made a technical decision, influenced without authority
  CONFLICT:        Disagreed with a teammate, handled a difficult stakeholder
  FAILURE:         Project that failed or went wrong, what you learned
  IMPACT:          Your biggest technical accomplishment (with metrics)
  GROWTH:          Feedback you received and acted on
  COLLABORATION:   Cross-functional work, mentoring, being mentored
  AMBIGUITY:       Navigated unclear requirements or changing priorities

Tips:
  - Prepare 6–8 stories that can flex to different questions
  - Always end with what you learned (even from successes)
  - "I" not "we" — own your specific contribution
  - Metrics: "reduced latency by 40%", "served 10M users", "saved $200k/year"
```

# COMPLEXITY REFERENCE
```
O(1)        Constant:    Hash map lookup, stack push/pop
O(log n)    Log:         Binary search, balanced BST operations
O(n)        Linear:      Single pass, linear scan
O(n log n)  Linearithm:  Comparison sort (merge, heap, tim)
O(n²)       Quadratic:   Nested loops, bubble sort
O(2ⁿ)       Exponential: Subsets, brute-force backtracking
O(n!)       Factorial:   Permutations

Space complexity — common patterns:
  O(1):    Two pointers on array (no extra space)
  O(n):    Hash map, stack, recursion depth
  O(log n): Binary search recursion stack
```

# WEEK-BY-WEEK STUDY PLAN
```
Week 1: Arrays + Hash Maps (Two Sum, Product Except Self, Sliding Window)
Week 2: Trees + Graphs (BFS, DFS, level-order, path sum)
Week 3: DP fundamentals (Fibonacci, Climbing Stairs, Coin Change, LCS)
Week 4: Advanced (Backtracking, Heaps, Union-Find, Monotonic Stack)
Week 5: System design (Design TinyURL, Design Twitter Feed, Design Uber)
Week 6: Mock interviews + behavioral stories

Daily practice: 1 medium + review 1 hard from previous day
```
