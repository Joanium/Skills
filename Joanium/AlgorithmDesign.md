---
name: Algorithm Design
trigger: algorithm design, design an algorithm, optimize algorithm, time complexity, space complexity, big o notation, algorithmic thinking, data structure selection
description: Design efficient algorithms with proper complexity analysis. Covers sorting, searching, graph algorithms, dynamic programming, greedy approaches, and complexity trade-offs. Use when designing algorithms, analyzing complexity, or optimizing performance-critical code.
---

# ROLE
You are an algorithms engineer. Your job is to design efficient algorithms, analyze their complexity, and choose appropriate data structures. You think in terms of time and space trade-offs and select the right approach for each problem.

# COMPLEXITY ANALYSIS

## Big O Notation Reference
```
O(1)        → Constant time: hash map lookup, array access
O(log n)    → Logarithmic: binary search, balanced BST operations
O(n)        → Linear: single pass through data
O(n log n)  → Linearithmic: efficient sorting (merge sort, heap sort)
O(n²)       → Quadratic: nested loops over same data
O(n³)       → Cubic: triple nested loops
O(2ⁿ)       → Exponential: naive recursion, subset generation
O(n!)       → Factorial: permutation generation
```

## Amortized Analysis
```
Some operations are occasionally expensive but average out:
- Dynamic array append: O(n) worst case, O(1) amortized
- Hash table resize: O(n) worst case, O(1) amortized

Use when analyzing data structures with occasional costly operations.
```

# ALGORITHM PATTERNS

## Two Pointers
```python
# Problem: Find if array has two numbers that sum to target
def two_sum_sorted(nums: list[int], target: int) -> tuple[int, int]:
    left, right = 0, len(nums) - 1
    while left < right:
        current = nums[left] + nums[right]
        if current == target:
            return (left, right)
        elif current < target:
            left += 1
        else:
            right -= 1
    return None

# Time: O(n), Space: O(1)
# Use when: Array is sorted, looking for pairs with specific property
```

## Sliding Window
```python
# Problem: Find maximum sum subarray of size k
def max_sum_subarray(nums: list[int], k: int) -> int:
    window_sum = sum(nums[:k])
    max_sum = window_sum
    
    for i in range(k, len(nums)):
        window_sum += nums[i] - nums[i - k]
        max_sum = max(max_sum, window_sum)
    
    return max_sum

# Time: O(n), Space: O(1)
# Use when: Finding contiguous subarrays/substrings with specific property
```

## Fast and Slow Pointers (Floyd's Cycle Detection)
```python
# Problem: Detect cycle in linked list
def has_cycle(head: ListNode) -> bool:
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            return True
    return False

# Time: O(n), Space: O(1)
# Use when: Detecting cycles, finding middle element, palindrome check
```

## Merge Intervals
```python
# Problem: Merge overlapping intervals
def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
    if not intervals:
        return []
    
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    
    return merged

# Time: O(n log n), Space: O(n)
# Use when: Working with ranges, scheduling, timeline problems
```

## Topological Sort
```python
from collections import defaultdict, deque

def topological_sort(n: int, prerequisites: list[list[int]]) -> list[int]:
    graph = defaultdict(list)
    in_degree = [0] * n
    
    for course, prereq in prerequisites:
        graph[prereq].append(course)
        in_degree[course] += 1
    
    queue = deque([i for i in range(n) if in_degree[i] == 0])
    result = []
    
    while queue:
        node = queue.popleft()
        result.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    return result if len(result) == n else []  # [] if cycle exists

# Time: O(V + E), Space: O(V + E)
# Use when: Dependency resolution, build order, course scheduling
```

# DYNAMIC PROGRAMMING

## Pattern Recognition
```
DP applies when problem has:
1. Optimal substructure: optimal solution contains optimal solutions to subproblems
2. Overlapping subproblems: same subproblems solved multiple times

Approach:
1. Define the state (what parameters define a subproblem?)
2. Define the recurrence relation (how do subproblems relate?)
3. Define base cases
4. Choose top-down (memoization) or bottom-up (tabulation)
```

## Classic DP Examples
```python
# Fibonacci with memoization
def fibonacci(n: int, memo: dict = {}) -> int:
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci(n - 1, memo) + fibonacci(n - 2, memo)
    return memo[n]

# Knapsack Problem
def knapsack(weights: list[int], values: list[int], capacity: int) -> int:
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            if weights[i-1] <= w:
                dp[i][w] = max(
                    dp[i-1][w],
                    dp[i-1][w - weights[i-1]] + values[i-1]
                )
            else:
                dp[i][w] = dp[i-1][w]
    
    return dp[n][capacity]
```

# GRAPH ALGORITHMS

## BFS (Breadth-First Search)
```python
from collections import deque

def bfs(graph: dict, start: str) -> list:
    visited = set()
    queue = deque([start])
    result = []
    
    while queue:
        node = queue.popleft()
        if node not in visited:
            visited.add(node)
            result.append(node)
            queue.extend(neighbor for neighbor in graph[node] if neighbor not in visited)
    
    return result

# Use for: Shortest path in unweighted graph, level-order traversal
```

## Dijkstra's Algorithm
```python
import heapq

def dijkstra(graph: dict, start: str) -> dict:
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    pq = [(0, start)]
    
    while pq:
        current_dist, current_node = heapq.heappop(pq)
        
        if current_dist > distances[current_node]:
            continue
        
        for neighbor, weight in graph[current_node]:
            distance = current_dist + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                heapq.heappush(pq, (distance, neighbor))
    
    return distances

# Time: O((V + E) log V), Space: O(V)
# Use for: Shortest path in weighted graph with non-negative edges
```

# GREEDY ALGORITHMS
```
Greedy works when:
- Locally optimal choices lead to globally optimal solution
- Greedy choice property + optimal substructure

Common greedy problems:
- Activity selection
- Huffman coding
- Kruskal's/Prim's MST
- Fractional knapsack
- Interval scheduling
```

# DESIGN DECISIONS

## Choosing the Right Approach
```
Problem type → Algorithm family:
Sorting data → Quick sort (general), Merge sort (stable), Counting sort (integers in range)
Searching → Binary search (sorted), Hash map (frequent lookups), Trie (prefix)
Shortest path → BFS (unweighted), Dijkstra (non-negative), Bellman-Ford (negative edges)
Connectivity → Union-Find, DFS/BFS
Optimization → DP (overlapping subproblems), Greedy (greedy property holds), Backtracking (exhaustive)
String matching → KMP, Rabin-Karp, Trie, Suffix tree
```

# REVIEW CHECKLIST
```
[ ] Time complexity analyzed and documented
[ ] Space complexity analyzed and documented
[ ] Edge cases handled (empty input, single element, duplicates)
[ ] Algorithm correctness verified
[ ] Trade-offs documented (time vs space, simplicity vs performance)
[ ] Alternative approaches considered
[ ] Benchmark data for critical paths
```
