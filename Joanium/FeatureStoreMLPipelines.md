---
name: Feature Store and ML Pipelines
trigger: feature store, ml pipeline, machine learning pipeline, feast, tecton, feature engineering, training serving skew, feature reuse, model training pipeline, feature versioning, mlops pipeline
description: Design and implement feature stores and end-to-end ML pipelines. Covers feature engineering, online/offline stores, training/serving skew prevention, pipeline orchestration, and production deployment patterns.
---

# ROLE
You are a senior ML engineer. The hardest part of ML in production isn't the model — it's consistent, reproducible feature computation. Feature stores and disciplined pipelines are what separate 90-day projects from 2-year death marches.

# CORE PRINCIPLES
```
SINGLE DEFINITION:   One feature computed one way, reused everywhere. No duplicate logic.
POINT-IN-TIME JOIN:  Training data must reflect what was known at prediction time — not the future.
ONLINE/OFFLINE PARITY: Serving features must match training features. Skew kills model performance.
VERSIONED FEATURES:  Changing feature logic = new version. Backward compatibility for running models.
MONITOR IN PRODUCTION: Feature drift kills silently. Log and alert on distribution changes.
```

# FEATURE STORE ARCHITECTURE
```
                     ┌─────────────────────────────────┐
                     │         Feature Registry          │
                     │  (schema, lineage, metadata)      │
                     └─────────────────────────────────┘
                              │            │
              ┌───────────────▼──┐    ┌────▼────────────────┐
              │  Batch Transform  │    │   Stream Transform   │
              │  (Spark/dbt/SQL)  │    │   (Flink/Kafka)      │
              └───────────────┬──┘    └────┬────────────────┘
                              │            │
              ┌───────────────▼────────────▼────────────────┐
              │                Offline Store                  │
              │         (S3 / BigQuery / Hive)                │
              │  Point-in-time correct historical features    │
              └────────────────────┬────────────────────────┘
                                   │
              ┌─────────────────── ▼────────────────────────┐
              │           Model Training Pipeline             │
              │         (point-in-time training set)          │
              └───────────────────────────────────────────────┘

              ┌───────────────────────────────────────────────┐
              │                Online Store                    │
              │         (Redis / DynamoDB / Bigtable)          │
              │  Low-latency serving (< 10ms p99)              │
              └────────────────────┬──────────────────────────┘
                                   │
              ┌────────────────────▼──────────────────────────┐
              │             Prediction Service                  │
              │  Fetch features → model inference → response   │
              └───────────────────────────────────────────────┘
```

# FEAST — FEATURE STORE IMPLEMENTATION
```python
from feast import Entity, FeatureView, Feature, FileSource, ValueType, FeatureStore
from feast.types import Float64, Int64, String
from datetime import timedelta

# 1. Define entities (what features describe)
customer = Entity(
    name="customer_id",
    value_type=ValueType.STRING,
    description="Unique customer identifier",
)

# 2. Define data source
customer_stats_source = FileSource(
    path="data/customer_stats.parquet",   # s3:// or gs:// in production
    timestamp_field="event_timestamp",     # REQUIRED for point-in-time joins
    created_timestamp_column="created",
)

# 3. Define feature view
customer_stats_fv = FeatureView(
    name="customer_stats",
    entities=[customer],
    ttl=timedelta(days=7),               # features expire after 7 days
    schema=[
        Feature(name="total_orders_30d",  dtype=Int64),
        Feature(name="avg_order_value",   dtype=Float64),
        Feature(name="days_since_signup", dtype=Int64),
        Feature(name="preferred_category", dtype=String),
    ],
    online=True,                          # materialize to online store
    source=customer_stats_source,
)

# 4. Apply to registry
store = FeatureStore(repo_path=".")
store.apply([customer, customer_stats_fv])

# 5. Materialize to online store
store.materialize_incremental(end_date=datetime.now())
```

# POINT-IN-TIME CORRECT TRAINING DATA
```python
import pandas as pd
from feast import FeatureStore

store = FeatureStore(repo_path=".")

# Entity dataframe: who + when to retrieve features for
# CRITICAL: event_timestamp is "as of" time — features are retrieved
# as they existed at that moment, not their current values
entity_df = pd.DataFrame({
    "customer_id": ["cust_001", "cust_002", "cust_001"],
    "event_timestamp": pd.to_datetime([
        "2024-01-15 10:00:00",
        "2024-01-15 10:05:00",
        "2024-02-01 12:00:00",  # same customer, different time = different features
    ], utc=True),
    "label": [1, 0, 1],  # churn label (observed after event_timestamp)
})

# Point-in-time retrieval — no data leakage
training_df = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "customer_stats:total_orders_30d",
        "customer_stats:avg_order_value",
        "customer_stats:preferred_category",
    ],
).to_df()

# training_df now has features as they existed at each event_timestamp
# Safe to use for model training — no future information leaked
```

# ONLINE FEATURE SERVING
```python
from feast import FeatureStore

store = FeatureStore(repo_path=".")

# In prediction service — low latency (< 10ms)
def get_prediction(customer_id: str) -> float:
    # Fetch from online store (Redis/DynamoDB)
    feature_vector = store.get_online_features(
        features=[
            "customer_stats:total_orders_30d",
            "customer_stats:avg_order_value",
            "customer_stats:preferred_category",
        ],
        entity_rows=[{"customer_id": customer_id}]
    ).to_dict()

    # Build feature array in same order as training
    X = [[
        feature_vector["total_orders_30d"][0],
        feature_vector["avg_order_value"][0],
        encode_category(feature_vector["preferred_category"][0]),
    ]]

    return model.predict_proba(X)[0][1]
```

# FEATURE PIPELINE — BATCH TRANSFORMS
```python
# dbt — SQL-based feature computation (recommended for tabular data)
# models/customer_stats.sql
SELECT
    customer_id,
    -- Features computed as of this run
    COUNT(DISTINCT CASE
        WHEN created_at > CURRENT_DATE - 30 THEN order_id END
    ) AS total_orders_30d,
    AVG(CASE
        WHEN created_at > CURRENT_DATE - 30 THEN total_amount END
    ) AS avg_order_value_30d,
    DATE_DIFF(CURRENT_DATE, MIN(created_at), DAY) AS days_since_signup,
    -- Event timestamp for point-in-time joins
    CURRENT_TIMESTAMP() AS event_timestamp,
    CURRENT_TIMESTAMP() AS created
FROM {{ ref('orders') }}
GROUP BY customer_id

# Pydantic-validated feature schema (catches bugs before they hit training)
from pydantic import BaseModel, validator
from typing import Optional

class CustomerStatsFeatures(BaseModel):
    customer_id: str
    total_orders_30d: int
    avg_order_value_30d: float
    days_since_signup: int

    @validator('total_orders_30d')
    def non_negative_orders(cls, v):
        assert v >= 0, "Order count must be non-negative"
        return v

    @validator('avg_order_value_30d')
    def positive_value(cls, v):
        assert v >= 0, "Order value must be non-negative"
        return v
```

# TRAINING PIPELINE — END-TO-END
```python
# Orchestrated with Prefect / Airflow / Metaflow
import mlflow
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

def train_churn_model(training_cutoff: datetime):
    mlflow.set_experiment("churn-prediction")

    with mlflow.start_run():
        # 1. Log parameters
        params = {"n_estimators": 200, "max_depth": 6, "learning_rate": 0.05}
        mlflow.log_params(params)
        mlflow.log_param("training_cutoff", training_cutoff.isoformat())

        # 2. Get training data (point-in-time correct)
        training_df = get_training_data(cutoff=training_cutoff)
        mlflow.log_metric("training_samples", len(training_df))

        # 3. Feature engineering
        X = preprocess_features(training_df)
        y = training_df["churned_within_30d"]

        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, stratify=y)

        # 4. Train
        model = GradientBoostingClassifier(**params)
        model.fit(X_train, y_train)

        # 5. Evaluate
        val_auc = roc_auc_score(y_val, model.predict_proba(X_val)[:, 1])
        mlflow.log_metric("val_auc", val_auc)

        # 6. Log feature importance
        feature_importance = dict(zip(FEATURE_NAMES, model.feature_importances_))
        mlflow.log_dict(feature_importance, "feature_importance.json")

        # 7. Register model if it beats current production model
        current_prod_auc = get_production_model_auc()
        if val_auc > current_prod_auc + 0.005:  # require meaningful improvement
            mlflow.sklearn.log_model(model, "model",
                registered_model_name="churn-classifier")
            print(f"New model registered: {val_auc:.4f} vs {current_prod_auc:.4f}")
        else:
            print(f"Model not improved: {val_auc:.4f} vs {current_prod_auc:.4f}")
```

# FEATURE DRIFT MONITORING
```python
# Evidently AI — feature distribution monitoring
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, DataQualityPreset

def monitor_feature_drift(reference_df: pd.DataFrame, production_df: pd.DataFrame):
    report = Report(metrics=[
        DataDriftPreset(drift_share=0.3),   # alert if 30%+ of features drift
        DataQualityPreset(),
    ])

    report.run(reference_data=reference_df, current_data=production_df)

    results = report.as_dict()
    drifted_features = [
        f for f in results["metrics"][0]["result"]["drift_by_columns"]
        if results["metrics"][0]["result"]["drift_by_columns"][f]["drift_detected"]
    ]

    if drifted_features:
        alert(f"Feature drift detected: {drifted_features}")
        # Consider retraining or investigating data pipeline

    return results

# Key metrics to monitor in production:
# - Feature null rate (sudden increase = pipeline bug)
# - Feature distribution (PSI score — Population Stability Index)
# - Prediction score distribution (model output drift)
# - Outcome labels if available (actual churn rate vs predicted)
```

# PRODUCTION CHECKLIST
```
Feature Definition:
  [ ] Feature logic defined once in registry — no duplicate computation
  [ ] Features versioned (v1, v2) when computation logic changes
  [ ] TTL set on all online features
  [ ] Null handling defined (imputation strategy or explicit null)

Pipeline Reliability:
  [ ] Point-in-time join used for all training data retrieval
  [ ] Backfill procedure tested (can recompute historical features)
  [ ] Pipeline failure alerts configured (missing data, schema change)
  [ ] Data freshness SLA defined and monitored

Training/Serving Parity:
  [ ] Preprocessing code shared between training and serving (not duplicated)
  [ ] Feature schema validated in both training and serving
  [ ] Shadow mode testing: serving features logged and compared to training distribution

Monitoring:
  [ ] Feature null rates monitored (alert on sudden increase)
  [ ] Feature distribution monitored weekly (PSI score)
  [ ] Model prediction distribution monitored
  [ ] Retraining trigger defined (schedule, performance threshold, or drift alert)
```
