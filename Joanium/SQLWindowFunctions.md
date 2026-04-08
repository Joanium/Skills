---
name: SQL Window Functions
trigger: window functions, SQL analytics, OVER clause, PARTITION BY, ROW_NUMBER, RANK, LAG, LEAD, running total, moving average, CTEs, common table expressions, recursive CTE, analytical queries, NTILE, FIRST_VALUE, LAST_VALUE, dense_rank, sql ranking, sql aggregation advanced
description: Write powerful analytical SQL using window functions, CTEs, and recursive queries. Covers ranking, running totals, moving averages, lag/lead comparisons, and advanced query composition.
---

# ROLE
You are a data engineer who writes SQL that makes ORMs cry. You know that most "I'll just process this in code" problems are actually one well-written query away from being solved directly in the database, faster, with less memory, and with far less code.

# CORE CONCEPT: WINDOW FUNCTIONS
```
Unlike GROUP BY (which collapses rows), window functions COMPUTE ACROSS ROWS while keeping each row.

Syntax:
  function_name(column) OVER (
    PARTITION BY partition_column    -- split into groups (optional)
    ORDER BY sort_column             -- order within each partition (optional)
    ROWS/RANGE BETWEEN ... AND ...   -- frame definition (optional)
  )

The OVER() clause is what makes it a window function.
Empty OVER() = entire result set is one window.
```

# RANKING FUNCTIONS

## ROW_NUMBER, RANK, DENSE_RANK
```sql
SELECT
  name,
  department,
  salary,
  ROW_NUMBER()  OVER (PARTITION BY department ORDER BY salary DESC) AS row_num,
  RANK()        OVER (PARTITION BY department ORDER BY salary DESC) AS rank,
  DENSE_RANK()  OVER (PARTITION BY department ORDER BY salary DESC) AS dense_rank
FROM employees;

-- Results:
-- name    | dept  | salary | row_num | rank | dense_rank
-- Alice   | Eng   | 120000 |    1    |   1  |     1
-- Bob     | Eng   | 100000 |    2    |   2  |     2
-- Charlie | Eng   | 100000 |    3    |   2  |     2      ← same salary as Bob
-- Dave    | Eng   |  90000 |    4    |   4  |     3      ← rank skips 3; dense_rank doesn't

-- ROW_NUMBER:  always unique, arbitrary tiebreaker
-- RANK:        ties get same rank, next rank skips (1,2,2,4)
-- DENSE_RANK:  ties get same rank, no skipping (1,2,2,3)
```

## Get Top-N Per Group (Classic Use Case)
```sql
-- Top 3 highest-paid employees per department
WITH ranked AS (
  SELECT
    name,
    department,
    salary,
    ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS rn
  FROM employees
)
SELECT name, department, salary
FROM ranked
WHERE rn <= 3;

-- Latest order per customer
WITH ranked AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at DESC) AS rn
  FROM orders
)
SELECT * FROM ranked WHERE rn = 1;
```

## NTILE — Percentile Buckets
```sql
-- Divide users into 4 quartiles by revenue
SELECT
  user_id,
  total_revenue,
  NTILE(4) OVER (ORDER BY total_revenue) AS quartile,
  NTILE(100) OVER (ORDER BY total_revenue) AS percentile
FROM user_revenue;

-- quartile 1 = bottom 25%, quartile 4 = top 25%
```

## PERCENT_RANK and CUME_DIST
```sql
SELECT
  product_name,
  price,
  PERCENT_RANK() OVER (ORDER BY price) AS percent_rank,  -- 0 to 1
  CUME_DIST()    OVER (ORDER BY price) AS cume_dist       -- cumulative % of rows ≤ this value
FROM products;
```

# AGGREGATE WINDOW FUNCTIONS (Running Totals, Moving Averages)

## Running Total
```sql
SELECT
  order_date,
  amount,
  SUM(amount) OVER (ORDER BY order_date) AS running_total,
  SUM(amount) OVER (PARTITION BY customer_id ORDER BY order_date) AS customer_running_total
FROM orders;
```

## Moving Average (Frame Definition)
```sql
-- 7-day moving average
SELECT
  date,
  revenue,
  AVG(revenue) OVER (
    ORDER BY date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW   -- current row + 6 before = 7 days
  ) AS moving_avg_7d,

  -- 30-day moving average
  AVG(revenue) OVER (
    ORDER BY date
    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
  ) AS moving_avg_30d
FROM daily_revenue;
```

## Frame Clause Options
```sql
-- ROWS: physical rows
-- RANGE: logical rows (same ORDER BY value)

ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW   -- from first row to current (running total)
ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING           -- 5-row window centered on current
ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING   -- current to last (reverse running)
RANGE BETWEEN INTERVAL '7 days' PRECEDING AND CURRENT ROW  -- date-based range (Postgres)

-- Running sum using UNBOUNDED (default if ORDER BY given, no frame specified):
SUM(amount) OVER (ORDER BY date)
-- is equivalent to:
SUM(amount) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
```

## Count, Min, Max Over Window
```sql
SELECT
  id,
  department,
  salary,
  COUNT(*) OVER (PARTITION BY department) AS dept_headcount,
  MAX(salary) OVER (PARTITION BY department) AS dept_max_salary,
  MIN(salary) OVER (PARTITION BY department) AS dept_min_salary,
  AVG(salary) OVER (PARTITION BY department) AS dept_avg_salary,
  salary - AVG(salary) OVER (PARTITION BY department) AS salary_vs_avg
FROM employees;
```

# LAG AND LEAD — COMPARE ADJACENT ROWS

## Syntax
```sql
LAG(column, offset, default)  OVER (...)  -- look BACK n rows
LEAD(column, offset, default) OVER (...)  -- look FORWARD n rows
```

## Day-Over-Day / Month-Over-Month Changes
```sql
SELECT
  date,
  revenue,
  LAG(revenue) OVER (ORDER BY date) AS prev_day_revenue,
  revenue - LAG(revenue) OVER (ORDER BY date) AS day_over_day_change,
  ROUND(
    100.0 * (revenue - LAG(revenue) OVER (ORDER BY date))
    / NULLIF(LAG(revenue) OVER (ORDER BY date), 0),
    2
  ) AS pct_change
FROM daily_revenue;

-- Per-customer: time between orders
SELECT
  customer_id,
  order_date,
  LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS prev_order_date,
  order_date - LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS days_since_last_order
FROM orders;
```

## Detect Status Changes
```sql
-- Find rows where status changed from previous row
WITH with_prev AS (
  SELECT
    id,
    status,
    changed_at,
    LAG(status) OVER (PARTITION BY entity_id ORDER BY changed_at) AS prev_status
  FROM status_log
)
SELECT * FROM with_prev
WHERE status <> prev_status OR prev_status IS NULL;
```

# FIRST_VALUE AND LAST_VALUE

## Get First/Last Value in Window
```sql
SELECT
  customer_id,
  order_date,
  amount,
  FIRST_VALUE(amount) OVER (
    PARTITION BY customer_id ORDER BY order_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
  ) AS first_order_amount,

  LAST_VALUE(amount) OVER (
    PARTITION BY customer_id ORDER BY order_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING  -- IMPORTANT: need full frame
  ) AS last_order_amount
FROM orders;
-- Note: LAST_VALUE needs explicit full frame — default frame stops at current row
```

# CTEs (COMMON TABLE EXPRESSIONS)

## Basic CTE — Named Subquery
```sql
WITH active_users AS (
  SELECT id, email, created_at
  FROM users
  WHERE status = 'active' AND last_login > NOW() - INTERVAL '30 days'
),
user_orders AS (
  SELECT user_id, COUNT(*) AS order_count, SUM(total) AS total_spent
  FROM orders
  WHERE created_at > NOW() - INTERVAL '30 days'
  GROUP BY user_id
)
SELECT
  u.email,
  COALESCE(o.order_count, 0) AS orders_last_30d,
  COALESCE(o.total_spent, 0) AS spent_last_30d
FROM active_users u
LEFT JOIN user_orders o ON o.user_id = u.id
ORDER BY total_spent DESC;
```

## Multiple CTEs — Chain Them
```sql
WITH
monthly_revenue AS (
  SELECT
    DATE_TRUNC('month', created_at) AS month,
    SUM(amount) AS revenue
  FROM orders
  GROUP BY 1
),
with_growth AS (
  SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) AS prev_revenue
  FROM monthly_revenue
)
SELECT
  month,
  revenue,
  ROUND(100.0 * (revenue - prev_revenue) / NULLIF(prev_revenue, 0), 2) AS growth_pct
FROM with_growth
ORDER BY month;
```

## Recursive CTE — Hierarchical Data
```sql
-- Traverse org chart (employee → manager → manager's manager)
WITH RECURSIVE org_chart AS (
  -- Base case: start with the root (CEO, no manager)
  SELECT id, name, manager_id, 0 AS depth, ARRAY[id] AS path
  FROM employees
  WHERE manager_id IS NULL

  UNION ALL

  -- Recursive case: join each employee to their manager in the result so far
  SELECT e.id, e.name, e.manager_id, oc.depth + 1, oc.path || e.id
  FROM employees e
  INNER JOIN org_chart oc ON e.manager_id = oc.id
  WHERE NOT e.id = ANY(oc.path)  -- prevent infinite loops from bad data
)
SELECT
  REPEAT('  ', depth) || name AS indented_name,  -- indent by depth
  depth
FROM org_chart
ORDER BY path;

-- Fibonacci (classic demo)
WITH RECURSIVE fib AS (
  SELECT 0 AS n, 0 AS a, 1 AS b
  UNION ALL
  SELECT n + 1, b, a + b FROM fib WHERE n < 20
)
SELECT n, a AS fibonacci FROM fib;

-- Find all descendants of a category node
WITH RECURSIVE descendants AS (
  SELECT id, name, parent_id FROM categories WHERE id = 5  -- start node
  UNION ALL
  SELECT c.id, c.name, c.parent_id
  FROM categories c
  INNER JOIN descendants d ON c.parent_id = d.id
)
SELECT * FROM descendants;
```

# PRACTICAL ANALYTICAL QUERIES

## Cohort Retention Analysis
```sql
WITH cohorts AS (
  SELECT
    user_id,
    DATE_TRUNC('month', MIN(created_at)) AS cohort_month
  FROM orders
  GROUP BY user_id
),
user_activity AS (
  SELECT
    o.user_id,
    c.cohort_month,
    DATE_TRUNC('month', o.created_at) AS activity_month,
    EXTRACT(YEAR FROM AGE(DATE_TRUNC('month', o.created_at), c.cohort_month)) * 12 +
    EXTRACT(MONTH FROM AGE(DATE_TRUNC('month', o.created_at), c.cohort_month)) AS months_since_cohort
  FROM orders o
  JOIN cohorts c USING (user_id)
)
SELECT
  cohort_month,
  months_since_cohort,
  COUNT(DISTINCT user_id) AS retained_users
FROM user_activity
GROUP BY 1, 2
ORDER BY 1, 2;
```

## Gaps and Islands (Find Consecutive Sequences)
```sql
-- Find consecutive active days (sessions with no gaps)
WITH numbered AS (
  SELECT
    user_id,
    active_date,
    active_date - (ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY active_date))::INTEGER AS grp
  FROM user_activity
),
streaks AS (
  SELECT
    user_id,
    MIN(active_date) AS streak_start,
    MAX(active_date) AS streak_end,
    COUNT(*) AS streak_length
  FROM numbered
  GROUP BY user_id, grp
)
SELECT * FROM streaks WHERE streak_length >= 7  -- find 7+ day streaks
ORDER BY streak_length DESC;
```

## Percentile Distribution
```sql
SELECT
  department,
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY salary) AS p25,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY salary) AS median,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY salary) AS p75,
  PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY salary) AS p90
FROM employees
GROUP BY department;
```

# PERFORMANCE TIPS
```
Window functions are applied AFTER WHERE and GROUP BY, BEFORE ORDER BY and LIMIT

Index your PARTITION BY and ORDER BY columns — window functions scan sorted data

Avoid computing the same window multiple times:
  BAD:  SUM(x) OVER (PARTITION BY a ORDER BY b) + AVG(x) OVER (PARTITION BY a ORDER BY b)
  GOOD: use a CTE, compute window once, reference the CTE

MATERIALIZED CTEs (Postgres 12+):
  WITH MATERIALIZED cte AS (...)  -- force evaluation once (vs inline expansion)
  WITH cte AS (...)               -- default: planner decides

Filter AFTER window functions run:
  WITH ranked AS (SELECT *, ROW_NUMBER() OVER (...) AS rn FROM t)
  SELECT * FROM ranked WHERE rn = 1   -- correct
  -- vs WHERE ROW_NUMBER() OVER (...) = 1  → invalid, window can't be in WHERE
```
