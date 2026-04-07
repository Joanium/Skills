---
name: Stream Processing & Kafka
trigger: kafka, kafka streams, stream processing, apache kafka, kafka consumer, kafka producer, kafka topic, event streaming, flink, real-time data pipeline, kafka connect, consumer group, exactly-once semantics, kafka partitions, stream processing architecture
description: Build reliable real-time data pipelines with Apache Kafka. Covers Kafka fundamentals, producer/consumer patterns, partitioning, consumer groups, exactly-once semantics, Kafka Streams, Kafka Connect, and production operations.
---

# ROLE
You are a data engineer who builds real-time event streaming systems that are reliable at scale. You know that Kafka is infrastructure — not magic — and that most streaming problems are really distributed systems problems: ordering, at-least-once vs exactly-once delivery, consumer lag, and schema evolution.

# KAFKA FUNDAMENTALS
```
Core concepts:
  Topic:          Ordered, immutable log of events. Events are never deleted (until retention expires).
  Partition:      Unit of parallelism within a topic. One consumer per partition per consumer group.
  Offset:         Position of an event within a partition (starts at 0, increases monotonically).
  Producer:       Writes events to topics. Chooses partition (round-robin, key-based, or custom).
  Consumer:       Reads events from topics. Tracks its own offset.
  Consumer Group: Set of consumers sharing work on a topic (each partition assigned to one consumer).
  Broker:         Kafka server. Topics are distributed across brokers.
  Replication:    Each partition replicated to N brokers. Leader handles reads/writes; followers replicate.

Delivery guarantees:
  At-most-once:   Consumer commits offset before processing. Message loss possible on crash.
  At-least-once:  Consumer commits offset after processing. Duplicate processing possible on crash.
  Exactly-once:   Transactional producer + idempotent consumer. No loss, no duplicates. More complex.
```

# TOPIC DESIGN
```
Naming convention:
  <domain>.<entity>.<event-type>
  Examples:
    orders.order.placed
    payments.payment.completed
    users.user.email-verified
    inventory.product.stock-updated

Partitioning:
  Partition count = max parallelism for consumers
  Key determines which partition an event goes to (same key → same partition → ordering preserved)
  Rule: Events that must be ordered relative to each other must share the same partition key
  
  order.placed → key = order_id (all events for an order are ordered)
  user.activity → key = user_id (all events for a user are ordered)
  
  Partition count: start at 6-12 for high-throughput, 3 for low-throughput
  CANNOT reduce partition count after creation — plan ahead
  Adding partitions breaks key-to-partition mapping for existing keys

Retention:
  Default 7 days. Set based on downstream recovery needs:
  retention.ms = 604800000  # 7 days in milliseconds
  retention.bytes = -1       # unlimited (rely on time, not size)
  
  Log compaction (for stateful topics — latest value per key kept forever):
  cleanup.policy = compact
  Use for: current state of entities (latest user profile, current inventory level)
```

# PRODUCER PATTERNS
```python
from confluent_kafka import Producer
import json

producer = Producer({
    'bootstrap.servers': 'kafka1:9092,kafka2:9092,kafka3:9092',
    'acks': 'all',                    # wait for all ISR to acknowledge (safest)
    'retries': 5,                     # retry transient failures
    'retry.backoff.ms': 500,
    'enable.idempotence': True,       # exactly-once at producer level (no duplicate writes)
    'compression.type': 'lz4',        # compress batches (reduces network + storage)
    'linger.ms': 5,                   # wait up to 5ms to batch more messages
    'batch.size': 65536,              # 64KB batch size
})

def delivery_callback(err, msg):
    if err:
        print(f'Message delivery failed: {err}')
        # Handle: retry, dead-letter queue, alert
    else:
        print(f'Delivered to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}')

def produce_event(topic: str, key: str, value: dict):
    producer.produce(
        topic=topic,
        key=key.encode('utf-8'),
        value=json.dumps(value).encode('utf-8'),
        on_delivery=delivery_callback
    )
    producer.poll(0)  # trigger delivery callbacks without blocking

# Flush before shutdown — don't lose buffered messages
producer.flush(timeout=30)
```

# CONSUMER PATTERNS
```python
from confluent_kafka import Consumer, KafkaException

consumer = Consumer({
    'bootstrap.servers': 'kafka1:9092,kafka2:9092,kafka3:9092',
    'group.id': 'order-processor-v1',  # consumer group ID — version it!
    'auto.offset.reset': 'earliest',   # 'earliest' or 'latest' — where to start if no committed offset
    'enable.auto.commit': False,        # ALWAYS disable — commit manually after processing
    'max.poll.interval.ms': 300000,     # 5 min — if no poll in this window, rebalance triggered
    'session.timeout.ms': 30000,        # 30s — heartbeat timeout
})

consumer.subscribe(['orders.order.placed', 'orders.order.cancelled'])

try:
    while True:
        msg = consumer.poll(timeout=1.0)
        
        if msg is None:
            continue
        if msg.error():
            raise KafkaException(msg.error())
        
        try:
            key = msg.key().decode('utf-8')
            value = json.loads(msg.value().decode('utf-8'))
            
            # Process message
            process_order_event(key, value)
            
            # Commit AFTER successful processing (at-least-once delivery)
            consumer.commit(message=msg, asynchronous=False)
            
        except ProcessingError as e:
            # Decide: retry, dead-letter, skip
            send_to_dead_letter_queue(msg, str(e))
            consumer.commit(message=msg, asynchronous=False)  # commit anyway to move forward
            
except KeyboardInterrupt:
    pass
finally:
    consumer.close()  # triggers final offset commit and partition rebalance
```

# EXACTLY-ONCE SEMANTICS
```python
# Requires: idempotent producer + transactional producer + idempotent consumer processing

# Producer side — transactional
producer = Producer({
    'bootstrap.servers': '...',
    'transactional.id': 'order-processor-producer-1',   # unique per producer instance
    'enable.idempotence': True,
})
producer.init_transactions()

try:
    producer.begin_transaction()
    
    # Read input, produce output, and commit offset atomically
    producer.produce('orders.processed', key='order_123', value=json.dumps(result))
    producer.send_offsets_to_transaction(
        offsets,          # from consumer
        consumer_group_metadata   # from consumer
    )
    producer.commit_transaction()
    
except Exception as e:
    producer.abort_transaction()
    raise

# Consumer side — idempotent processing
# Even with exactly-once delivery, make your processing idempotent:
def process_order(order_id: str, event: dict):
    # Check if already processed (using DB, Redis, or unique constraint)
    if db.exists('processed_orders', order_id):
        return  # skip — already handled
    
    # Process + mark as done atomically
    with db.transaction():
        do_the_work(event)
        db.insert('processed_orders', {'id': order_id, 'processed_at': now()})
```

# SCHEMA REGISTRY
```python
# Avro + Schema Registry: enforce schema compatibility, avoid breaking consumers
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer

schema_registry = SchemaRegistryClient({'url': 'http://schema-registry:8081'})

order_schema = """
{
  "type": "record",
  "name": "OrderPlaced",
  "namespace": "com.myapp.orders",
  "fields": [
    {"name": "order_id", "type": "string"},
    {"name": "user_id", "type": "string"},
    {"name": "total_usd", "type": "double"},
    {"name": "placed_at", "type": "long", "logicalType": "timestamp-millis"},
    {"name": "metadata", "type": {"type": "map", "values": "string"}, "default": {}}
  ]
}
"""

# Compatibility modes:
#   BACKWARD:  new schema can read data written by old schema (add optional fields)
#   FORWARD:   old schema can read data written by new schema
#   FULL:      both directions (most restrictive, safest)

# Safe schema evolution (BACKWARD compatible):
#   ✓ Add optional field with default value
#   ✓ Remove field that had a default value
#   ✗ Add required field without default
#   ✗ Change field type
#   ✗ Remove field without default
```

# KAFKA STREAMS — STREAM PROCESSING IN JAVA/KOTLIN
```java
// Real-time aggregation: count orders per user per hour
StreamsBuilder builder = new StreamsBuilder();

KStream<String, OrderEvent> orders = builder.stream(
    "orders.order.placed",
    Consumed.with(Serdes.String(), orderSerde)
);

KTable<Windowed<String>, Long> orderCounts = orders
    .groupByKey()
    .windowedBy(TimeWindows.ofSizeWithNoGrace(Duration.ofHours(1)))
    .count(Materialized.as("order-counts-store"));

orderCounts.toStream()
    .map((windowedKey, count) -> KeyValue.pair(
        windowedKey.key(),
        new OrderCountEvent(windowedKey.key(), count, windowedKey.window().startTime())
    ))
    .to("analytics.order-counts-hourly", Produced.with(Serdes.String(), orderCountSerde));

KafkaStreams streams = new KafkaStreams(builder.build(), config);
streams.start();
```

# KAFKA CONNECT — DATA INTEGRATION
```yaml
# Source connector: PostgreSQL → Kafka (Debezium CDC)
name: postgres-source
config:
  connector.class: "io.debezium.connector.postgresql.PostgresConnector"
  database.hostname: "postgres"
  database.port: "5432"
  database.user: "debezium"
  database.password: "${file:/secrets/db-password.properties:password}"
  database.dbname: "production"
  database.server.name: "myapp"
  table.include.list: "public.orders,public.users"
  topic.prefix: "cdc"
  # Creates topics: cdc.public.orders, cdc.public.users

---
# Sink connector: Kafka → Snowflake
name: snowflake-sink
config:
  connector.class: "com.snowflake.kafka.connector.SnowflakeSinkConnector"
  tasks.max: "4"
  topics: "cdc.public.orders,cdc.public.users"
  snowflake.url.name: "account.snowflakecomputing.com"
  snowflake.user.name: "kafka_user"
  snowflake.private.key: "${file:/secrets/snowflake.properties:private.key}"
  snowflake.database.name: "RAW"
  snowflake.schema.name: "KAFKA"
  key.converter: "org.apache.kafka.connect.storage.StringConverter"
  value.converter: "io.confluent.connect.avro.AvroConverter"
```

# PRODUCTION OPERATIONS
```bash
# Monitor consumer lag (critical metric — lag growth = consumers falling behind)
kafka-consumer-groups.sh --bootstrap-server kafka:9092 \
  --describe --group order-processor-v1

# Output: TOPIC | PARTITION | CURRENT-OFFSET | LOG-END-OFFSET | LAG
# LAG = messages waiting to be processed. Alert if growing.

# List topics
kafka-topics.sh --list --bootstrap-server kafka:9092

# Create topic with explicit config
kafka-topics.sh --create \
  --topic orders.order.placed \
  --partitions 12 \
  --replication-factor 3 \
  --config retention.ms=604800000 \
  --config compression.type=lz4 \
  --bootstrap-server kafka:9092

# Describe topic
kafka-topics.sh --describe --topic orders.order.placed --bootstrap-server kafka:9092

# Read from beginning (debugging)
kafka-console-consumer.sh --topic orders.order.placed \
  --from-beginning \
  --bootstrap-server kafka:9092 \
  --max-messages 10
```

# PRODUCTION CHECKLIST
```
Topic design:
[ ] Naming convention: <domain>.<entity>.<event-type>
[ ] Partition count set for expected parallelism (cannot reduce later)
[ ] Partition key chosen to preserve required ordering
[ ] Retention policy set based on recovery/replay requirements
[ ] Schema registered in Schema Registry with FULL or BACKWARD compatibility

Producer:
[ ] acks=all for durability
[ ] enable.idempotence=true
[ ] Delivery callback handles failures
[ ] Flush on shutdown
[ ] Compression enabled (lz4 or snappy)

Consumer:
[ ] enable.auto.commit=false — commit manually after processing
[ ] Processing is idempotent (handles re-delivery gracefully)
[ ] Dead-letter topic for poison messages
[ ] Consumer group ID versioned (reset on breaking schema change)
[ ] Consumer lag monitored and alerted

Operations:
[ ] Replication factor >= 3 for production
[ ] min.insync.replicas=2 to prevent data loss
[ ] Monitoring: broker health, partition leadership, consumer lag, disk usage
[ ] Retention and compaction policies match use case
[ ] Schema compatibility mode set and enforced
```
