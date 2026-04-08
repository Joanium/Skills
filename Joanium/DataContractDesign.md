---
name: Data Contract Design
trigger: data contract, data schema agreement, producer consumer contract, schema registry, data quality agreement, pipeline contract, data mesh contract, data ownership, data SLA, schema evolution
description: Define and govern data contracts between producers and consumers in modern data platforms. Covers schema design, versioning, quality rules, SLAs, tooling, and enforcement strategies for data mesh and event-driven architectures.
---

# ROLE
You are a senior data engineer or data platform architect. Data contracts are the API design of the data world — they make pipelines reliable, ownership clear, and breaking changes visible before they cause 3am incidents.

# CORE PRINCIPLES
```
PRODUCER OWNS THE SCHEMA:  The team generating data defines and maintains its contract.
CONSUMERS DECLARE NEEDS:   Consumers register which fields and SLAs they depend on.
BREAKING CHANGES NEGOTIATED: No silent schema changes. Version explicitly, deprecate gracefully.
MACHINE-ENFORCEABLE:       Contracts aren't documentation — they're enforced at runtime.
QUALITY IS CONTRACTUAL:    Null rates, freshness, row counts are part of the agreement.
```

# CONTRACT ANATOMY
```yaml
# data-contract.yaml — canonical format (OpenDataContractStandard compatible)
apiVersion: v2.2.2
kind: DataContract

id: urn:datacontract:ecommerce:orders:v2
name: Orders Data Contract
version: 2.1.0
status: active                  # active | deprecated | draft
owner:
  team: checkout-engineering
  contact: checkout@company.com

description: |
  Order lifecycle events from checkout through fulfillment.
  Produced by the Checkout service, updated on every state transition.

# Where the data lives
servers:
  production:
    type: kafka
    topic: ecommerce.orders.v2
    format: avro
  analytics:
    type: bigquery
    project: data-prod
    dataset: ecommerce
    table: orders

# The schema
models:
  Order:
    type: object
    required: [orderId, customerId, status, createdAt, totalAmount]
    fields:
      orderId:
        type: string
        pattern: "^ORD-[0-9]{10}$"
        description: Globally unique order identifier
        pii: false
      customerId:
        type: string
        description: Reference to Customer contract
        pii: true
        classification: internal
      status:
        type: string
        enum: [pending, confirmed, shipped, delivered, cancelled, refunded]
      createdAt:
        type: timestamp
        format: ISO8601
      totalAmount:
        type: number
        minimum: 0
        description: Total in minor currency units (cents)
      lineItems:
        type: array
        items:
          $ref: "#/models/LineItem"

  LineItem:
    fields:
      productId: { type: string }
      quantity:  { type: integer, minimum: 1 }
      unitPrice: { type: number, minimum: 0 }

# Quality rules — the non-negotiable data quality SLA
quality:
  - rule: orderId must not be null
    type: not_null
    field: orderId
    threshold: 100%

  - rule: status must be a valid enum value
    type: accepted_values
    field: status
    values: [pending, confirmed, shipped, delivered, cancelled, refunded]
    threshold: 100%

  - rule: totalAmount must be non-negative
    type: range
    field: totalAmount
    min: 0
    threshold: 99.9%

  - rule: orders must arrive within 5 minutes of creation
    type: freshness
    field: createdAt
    maxAge: 5m

  - rule: row count must not drop more than 20% day-over-day
    type: volume
    metric: daily_count
    maxChange: 20%

# SLA commitments
sla:
  latency:   p99 < 500ms end-to-end
  freshness: data available within 5 minutes of event
  uptime:    99.9% monthly
  retention: 90 days in Kafka, 3 years in BigQuery

# Versioning policy
versioning:
  strategy: semantic
  backwardsCompatibilityGuarantee: true
  breakingChangePolicyDays: 90     # minimum notice before breaking change
  deprecationNoticeChannels:
    - slack:#data-contracts
    - email:data-consumers@company.com
```

# SCHEMA EVOLUTION RULES
```
BACKWARDS-COMPATIBLE (no version bump):
  + Adding an optional field with a default value
  + Adding a new enum value (if consumers use allow-unknown)
  + Adding a new optional nested object
  + Expanding a string field's max length

BACKWARDS-INCOMPATIBLE (requires major version bump + migration period):
  - Removing a field
  - Renaming a field
  - Changing a field's type (string → integer)
  - Making an optional field required
  - Narrowing enum values (removing an allowed value)
  - Changing the primary key structure

DEPRECATION WORKFLOW:
  1. Mark field as deprecated in contract
  2. Notify all registered consumers (automated from registry)
  3. Maintain field for agreed period (default 90 days)
  4. Remove only after all consumers have migrated (confirm via registry)
```

# ENFORCEMENT PATTERNS

## Kafka / Schema Registry
```python
# Producer-side enforcement — fail fast on contract violation
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

schema_registry = SchemaRegistryClient({"url": "https://schema-registry:8081"})

# Schema compatibility set to FULL (backwards + forwards)
# schema_registry.set_compatibility("ecommerce.orders.v2-value", "FULL")

producer = SerializingProducer({
    "bootstrap.servers": KAFKA_BROKERS,
    "value.serializer": AvroSerializer(schema_registry, order_schema_str),
})

# Any message not matching the schema raises SerializationError at produce time
```

## dbt / SQL — Data Quality at Transform Layer
```sql
-- schema.yml in dbt
models:
  - name: orders
    description: "{{ doc('orders') }}"
    constraints:
      - type: not_null
        columns: [order_id, customer_id, status]
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
      - name: status
        tests:
          - accepted_values:
              values: ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
      - name: total_amount
        tests:
          - dbt_utils.expression_is_true:
              expression: ">= 0"
```

## Great Expectations — Programmatic Quality Gates
```python
import great_expectations as gx

context = gx.get_context()
suite = context.add_expectation_suite("orders.critical")

suite.add_expectation(gx.expectations.ExpectColumnToExist(column="order_id"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="order_id"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToBeInSet(
    column="status",
    value_set=["pending", "confirmed", "shipped", "delivered", "cancelled"]
))
suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(
    column="total_amount", min_value=0
))

# Run in CI and block pipeline on failure
results = context.run_validation_operator("action_list_operator", assets_to_validate=[batch])
assert results["success"], f"Data quality gate failed: {results}"
```

# CONTRACT REGISTRY — DISCOVERY & GOVERNANCE
```
Every contract should be registered in a central catalog (DataHub, Atlan, custom):

  Producer registers:
    - Contract YAML
    - Owner + on-call contact
    - SLA commitments
    - Changelog

  Consumer registers:
    - Which contract + version they depend on
    - Which specific fields they use
    - Their SLA requirements (freshness, uptime)

  Registry enables:
    - Impact analysis: "Who breaks if I remove field X?"
    - Automated deprecation notifications
    - SLA compliance monitoring
    - Data lineage visualization
```

# BREAKING CHANGE COMMUNICATION TEMPLATE
```
Subject: [DATA CONTRACT BREAKING CHANGE] orders/v2 → status field change (90-day notice)

Affected Contract: urn:datacontract:ecommerce:orders:v2
Change Type: BREAKING — enum value 'refund_pending' added, 'refunded' deprecated
Effective Date: 2025-06-01 (90 days from today)
Owner: checkout-engineering

What's changing:
  BEFORE: status ∈ {pending, confirmed, shipped, delivered, cancelled, refunded}
  AFTER:  status ∈ {pending, confirmed, shipped, delivered, cancelled, refund_pending, refunded}
  NOTE:   'refunded' will be removed in v3 (separate notice)

What you need to do:
  1. Add handling for 'refund_pending' in your consumer by 2025-05-15
  2. Reply to this thread to confirm migration complete

Migration guide: [link to runbook]
Questions: #data-contracts in Slack or contracts@company.com
```

# TOOLING ECOSYSTEM
```
Schema Registries:  Confluent Schema Registry, AWS Glue Schema Registry, Apicurio
Contract Tools:     Schemata, OpenDataContractStandard (ODCS), Data Contract CLI
Quality:            Great Expectations, dbt tests, Soda Core, Monte Carlo
Catalogs:           DataHub, Atlan, OpenMetadata, Collibra
CI Enforcement:     data-contract-cli test, pytest + GE, dbt test --select tag:contract
```

# GOVERNANCE CHECKLIST
```
[ ] Every producer-owned dataset has a registered contract
[ ] Contract includes schema + quality rules + SLA
[ ] Schema registry compatibility set to FULL or BACKWARD
[ ] Consumer registry is up-to-date (who depends on what)
[ ] Automated quality gate in pipeline — breaking = alert, not silent failure
[ ] Breaking changes announced 90+ days in advance
[ ] Deprecated fields tracked until all consumers have migrated
[ ] Contracts versioned in Git alongside pipeline code
[ ] On-call rotation documented for contract incidents
```
