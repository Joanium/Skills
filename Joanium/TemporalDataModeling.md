---
name: Temporal Data Modeling
trigger: bitemporal, temporal database, slowly changing dimension, SCD, valid time, transaction time, history table, time travel query, temporal table, audit trail, point-in-time, as-of query, data versioning, temporal SQL, period table, immutable data
description: Model data that changes over time with full historical accuracy. Covers bitemporal modeling, valid time vs transaction time, SQL:2011 temporal tables, slowly changing dimensions, immutable event logs, and point-in-time queries.
---

# ROLE
You are a data architect specializing in temporal modeling. You design databases that preserve the complete history of every change — both when something was true in the real world and when it was recorded. You know that "delete" and "update" are information-destroying operations.

# CORE PRINCIPLES
```
NEVER DELETE HISTORY — deleting rows destroys knowledge; mark as superseded
VALID TIME ≠ TRANSACTION TIME — "what was true" vs "what did we know and when"
BITEMPORAL = COMPLETE AUDIT — you can reconstruct any view at any past moment
EVENTS ARE IMMUTABLE — append-only ledgers; corrections are new events
CURRENT = SPECIAL CASE — "current" state is a query on temporal data, not a design target
MONOTONIC TIMESTAMPS — use database server time or logical clocks; never client time
```

# THE TWO TIME DIMENSIONS

## Valid Time (Business Time)
```
When something was TRUE in the real world.
  "John's salary was $80,000 from Jan 1 to Jun 30"
  "This contract was active from 2020-03-01 to 2022-03-01"

You control this. It can be backdated or future-dated.
Example: correcting a start date that was entered wrong.
```

## Transaction Time (System Time)
```
When the database RECORDED the fact.
  "We recorded John's salary as $80,000 at 09:15 on Jan 5"
  "At 14:22 on Mar 3 we corrected his start date to Jan 1"

The database controls this. It is always monotonically increasing.
You cannot change the past of transaction time.
```

## Bitemporal = Both Dimensions Together
```
A bitemporal record answers:
  "What did we KNOW (transaction time) about what was TRUE (valid time)?"

This enables:
  → Reconstruct any past system state ("what did our system show on date X?")
  → See corrections ("the salary was recorded as X, then corrected to Y on date Z")
  → Audit compliance ("what did we know when we made that decision?")
```

# SCHEMA DESIGN

## Uni-Temporal: Valid Time Only
```sql
CREATE TABLE employee_salary (
    employee_id     INT          NOT NULL,
    salary          DECIMAL(10,2) NOT NULL,
    valid_from      DATE         NOT NULL,
    valid_to        DATE         NOT NULL,  -- or NULL = "current"
    
    PRIMARY KEY (employee_id, valid_from),
    CHECK (valid_from < valid_to)
);

-- Current salary for employee 42
SELECT salary
FROM employee_salary
WHERE employee_id = 42
  AND CURRENT_DATE BETWEEN valid_from AND valid_to;

-- Salary as of 2023-06-01
SELECT salary
FROM employee_salary
WHERE employee_id = 42
  AND DATE '2023-06-01' BETWEEN valid_from AND valid_to;
```

## Bitemporal Schema
```sql
CREATE TABLE employee_salary_bitemporal (
    id                  BIGSERIAL    PRIMARY KEY,
    employee_id         INT          NOT NULL,
    salary              DECIMAL(10,2) NOT NULL,
    
    -- Valid time: when the salary was actually in effect
    valid_from          DATE         NOT NULL,
    valid_to            DATE         NOT NULL DEFAULT '9999-12-31',
    
    -- Transaction time: when we recorded this row
    recorded_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    superseded_at       TIMESTAMPTZ  NOT NULL DEFAULT '9999-12-31',
    
    -- Metadata
    recorded_by         TEXT         NOT NULL,
    change_reason       TEXT
);

-- Index for common queries
CREATE INDEX idx_bitemporal_current 
  ON employee_salary_bitemporal(employee_id, valid_from, valid_to)
  WHERE superseded_at = '9999-12-31';
```

## Insertion and Correction Pattern
```sql
-- INSERT: new salary effective 2024-01-01
INSERT INTO employee_salary_bitemporal
  (employee_id, salary, valid_from, valid_to, recorded_by, change_reason)
VALUES
  (42, 85000, '2024-01-01', '9999-12-31', 'hr_system', 'Annual raise');

-- CORRECTION: we entered the wrong salary — should be 87000
-- Step 1: supersede the incorrect record
UPDATE employee_salary_bitemporal
SET superseded_at = NOW()
WHERE employee_id = 42
  AND valid_from = '2024-01-01'
  AND superseded_at = '9999-12-31';

-- Step 2: insert corrected record (keeping same valid_from)
INSERT INTO employee_salary_bitemporal
  (employee_id, salary, valid_from, valid_to, recorded_by, change_reason)
VALUES
  (42, 87000, '2024-01-01', '9999-12-31', 'hr_system', 'Corrected data entry error');

-- NEVER UPDATE the salary column directly — that destroys history
```

## Querying Bitemporal Data
```sql
-- Current view (what we believe is true right now)
SELECT employee_id, salary, valid_from, valid_to
FROM employee_salary_bitemporal
WHERE superseded_at = '9999-12-31'        -- currently recorded
  AND valid_to = '9999-12-31'             -- currently effective
  AND employee_id = 42;

-- Point-in-time: what salary was effective on 2024-03-01?
SELECT salary
FROM employee_salary_bitemporal
WHERE employee_id = 42
  AND '2024-03-01' BETWEEN valid_from AND valid_to  -- was true then
  AND superseded_at = '9999-12-31';                  -- using current knowledge

-- Historical view: what did our system show on 2024-02-15 about 2024-03-01?
-- "As of our knowledge on Feb 15, what salary was effective on Mar 1?"
SELECT salary
FROM employee_salary_bitemporal
WHERE employee_id = 42
  AND '2024-03-01' BETWEEN valid_from AND valid_to        -- valid time
  AND '2024-02-15' BETWEEN recorded_at AND superseded_at; -- transaction time

-- Full history of changes (correction trail)
SELECT salary, valid_from, valid_to, recorded_at, superseded_at, change_reason
FROM employee_salary_bitemporal
WHERE employee_id = 42
ORDER BY recorded_at DESC;
```

# SQL:2011 TEMPORAL TABLES (Standard)

## PostgreSQL with temporal_tables extension or manual
```sql
-- SQL:2011 PERIOD syntax (supported in MariaDB, DB2, Oracle)
CREATE TABLE contract (
    contract_id   INT NOT NULL,
    vendor_id     INT NOT NULL,
    value         DECIMAL(15,2),
    
    -- System time period (transaction time)
    sys_start     TIMESTAMP(6) GENERATED ALWAYS AS ROW START,
    sys_end       TIMESTAMP(6) GENERATED ALWAYS AS ROW END,
    PERIOD FOR SYSTEM_TIME (sys_start, sys_end)
) WITH SYSTEM VERSIONING;

-- Query: what did this row look like on 2023-01-01?
SELECT * FROM contract
FOR SYSTEM_TIME AS OF TIMESTAMP '2023-01-01 00:00:00'
WHERE contract_id = 101;

-- Query: all versions of a row
SELECT * FROM contract
FOR SYSTEM_TIME ALL
WHERE contract_id = 101
ORDER BY sys_start;
```

# SLOWLY CHANGING DIMENSIONS (Data Warehousing)

## SCD Types Compared
```
SCD TYPE 0: Never changes — reference data (country codes, currency codes)
  → Just store the value; no history needed

SCD TYPE 1: Overwrite — track only current value
  → UPDATE in place; history lost
  → Use when the old value is irrelevant (typo correction)

SCD TYPE 2: Add row — full history with effective dates
  → Insert new row with new valid_from; close old row
  → Enables point-in-time queries (most common for dimensions)
  → Surrogate key pattern:
    dim_customer_sk (surrogate, PK) | customer_id (natural) | name | valid_from | valid_to | is_current

SCD TYPE 3: Add column — track previous and current
  → Two columns: current_name, previous_name
  → Limited history (only one change back)
  → Use when you need "what changed" but not deep history

SCD TYPE 6: Hybrid (1+2+3)
  → Current columns + full history rows + is_current flag
```

## SCD Type 2 Implementation (PostgreSQL)
```sql
-- Dimension table
CREATE TABLE dim_customer (
    customer_sk     BIGSERIAL    PRIMARY KEY,
    customer_id     INT          NOT NULL,  -- natural key
    name            TEXT         NOT NULL,
    email           TEXT         NOT NULL,
    segment         TEXT,
    valid_from      DATE         NOT NULL,
    valid_to        DATE         NOT NULL DEFAULT '9999-12-31',
    is_current      BOOLEAN      NOT NULL DEFAULT TRUE
);

-- Procedure to update with SCD2 logic
CREATE OR REPLACE PROCEDURE upsert_customer_scd2(
    p_id INT, p_name TEXT, p_email TEXT, p_segment TEXT, p_effective DATE
) LANGUAGE plpgsql AS $$
BEGIN
    -- Close the current record
    UPDATE dim_customer
    SET valid_to = p_effective - INTERVAL '1 day',
        is_current = FALSE
    WHERE customer_id = p_id AND is_current = TRUE;

    -- Insert new version
    INSERT INTO dim_customer(customer_id, name, email, segment, valid_from)
    VALUES (p_id, p_name, p_email, p_segment, p_effective);
END;
$$;
```

# EVENT SOURCING — APPEND-ONLY TEMPORAL PATTERN
```python
# Events are immutable facts; state is derived from event replay
from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass(frozen=True)
class Event:
    event_id: str
    aggregate_id: str
    event_type: str
    payload: dict
    occurred_at: datetime
    recorded_at: datetime  # server-generated

# Events are never deleted or updated
class EventStore:
    def append(self, event: Event) -> None:
        """Write-once; no update or delete methods."""
        ...

    def get_events(self, aggregate_id: str, 
                   as_of: datetime = None) -> List[Event]:
        """Replay events up to a point in time."""
        ...

# Current state = fold over events
def get_account_balance(events: List[Event]) -> float:
    balance = 0.0
    for event in events:
        if event.event_type == "Deposit":
            balance += event.payload["amount"]
        elif event.event_type == "Withdrawal":
            balance -= event.payload["amount"]
    return balance

# Point-in-time reconstruction
def get_balance_at(store: EventStore, account_id: str, at: datetime) -> float:
    events = store.get_events(account_id, as_of=at)
    return get_account_balance(events)
```

# COMMON ANTI-PATTERNS
```
ANTI-PATTERN 1: Overwriting fields (UPDATE salary = new_value)
  → History destroyed; no audit trail; can't reconstruct past state
  FIX: SCD Type 2 or bitemporal insert

ANTI-PATTERN 2: Storing only current_timestamp for "when it changed"
  → One timestamp can't represent both valid time and transaction time
  FIX: Separate valid_from/valid_to + recorded_at/superseded_at

ANTI-PATTERN 3: NULL for "open end" valid_to
  → NULLs break BETWEEN queries; hard to index
  FIX: Use sentinel date '9999-12-31' as open end

ANTI-PATTERN 4: Using application timestamp for transaction time
  → Clock skew, NTP jumps, bugs cause out-of-order records
  FIX: Let the database set recorded_at with DEFAULT NOW()

ANTI-PATTERN 5: No gap/overlap validation
  → Valid time periods for same entity must not overlap or have gaps (if continuous)
  FIX: Exclusion constraint using btree_gist (PostgreSQL)
    CREATE EXTENSION btree_gist;
    ALTER TABLE employee_salary 
    ADD CONSTRAINT no_overlap EXCLUDE USING gist (
      employee_id WITH =,
      daterange(valid_from, valid_to) WITH &&
    );
```
