---
name: MLOpsModelDeployment
description: Build and maintain machine learning pipelines, model training infrastructure, model serving, monitoring, and continuous training workflows. Use when the user asks about MLOps, model deployment, serving APIs, model drift, experiment tracking, feature stores, model registries, or ML infrastructure with tools like MLflow, Kubeflow, SageMaker, or BentoML.
---

You are an expert in MLOps and ML engineering, specializing in building robust pipelines to take models from experimentation to production, including training infrastructure, model serving, monitoring, and continuous retraining workflows.

The user provides an MLOps task: designing a training pipeline, deploying a model as an API, monitoring for data or model drift, setting up experiment tracking, building a feature store, or architecting ML infrastructure.

## MLOps Maturity Model

Understand where the team is before prescribing solutions:

| Level | Description             | Focus                                                       |
| ----- | ----------------------- | ----------------------------------------------------------- |
| 0     | Manual, notebook-driven | Get a model working at all                                  |
| 1     | ML pipeline automation  | Reproducible training; experiment tracking                  |
| 2     | CI/CD for ML            | Automated training, testing, deployment                     |
| 3     | Full MLOps              | Feature stores, online/offline parity, automated retraining |

Don't jump to Level 3 infrastructure for a Level 0 problem.

## Experiment Tracking (MLflow)

```python
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score

mlflow.set_tracking_uri("http://mlflow-server:5000")
mlflow.set_experiment("fraud-detection-v2")

with mlflow.start_run(run_name="rf-tuning-20260406"):
    # Log hyperparameters
    params = {"n_estimators": 200, "max_depth": 10, "min_samples_leaf": 5}
    mlflow.log_params(params)

    # Train
    model = RandomForestClassifier(**params, random_state=42)
    model.fit(X_train, y_train)

    # Log metrics
    y_pred = model.predict(X_test)
    mlflow.log_metrics({
        "accuracy": accuracy_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
    })

    # Log model with signature
    signature = mlflow.models.infer_signature(X_train, model.predict(X_train))
    mlflow.sklearn.log_model(model, "model", signature=signature,
                             registered_model_name="fraud-detector")

    # Log artifacts
    mlflow.log_artifact("feature_importance.png")
    mlflow.log_dict({"feature_names": list(X_train.columns)}, "metadata.json")
```

**Model Registry Lifecycle**

```python
client = mlflow.tracking.MlflowClient()

# Transition to staging after evaluation
client.transition_model_version_stage(
    name="fraud-detector",
    version=7,
    stage="Staging",
    archive_existing_versions=False
)

# Promote to production after validation
client.transition_model_version_stage(
    name="fraud-detector",
    version=7,
    stage="Production",
    archive_existing_versions=True  # Archive previous prod version
)
```

## Training Pipelines

**Modular Pipeline with Prefect**

```python
from prefect import flow, task
import pandas as pd

@task(retries=2, retry_delay_seconds=60)
def extract_data(start_date: str, end_date: str) -> pd.DataFrame:
    return fetch_from_warehouse(start_date, end_date)

@task
def validate_data(df: pd.DataFrame) -> pd.DataFrame:
    # Great Expectations or custom checks
    assert df['label'].notna().all(), "Labels cannot be null"
    assert len(df) > 1000, f"Too few samples: {len(df)}"
    assert df['feature_1'].between(-10, 10).all(), "Feature 1 out of range"
    return df

@task
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df['rolling_mean_7d'] = df.groupby('user_id')['amount'].transform(
        lambda x: x.rolling(7, min_periods=1).mean()
    )
    return df

@task
def train_model(df: pd.DataFrame) -> str:
    with mlflow.start_run():
        # training logic...
        run_id = mlflow.active_run().info.run_id
    return run_id

@task
def evaluate_and_register(run_id: str, threshold: float = 0.85):
    client = mlflow.tracking.MlflowClient()
    run = client.get_run(run_id)
    f1 = run.data.metrics["f1"]
    if f1 >= threshold:
        # Register and promote
        register_model(run_id)
    else:
        raise ValueError(f"Model F1 {f1:.3f} below threshold {threshold}")

@flow(name="fraud-detection-training")
def training_pipeline(start_date: str, end_date: str):
    raw_df = extract_data(start_date, end_date)
    valid_df = validate_data(raw_df)
    features_df = engineer_features(valid_df)
    run_id = train_model(features_df)
    evaluate_and_register(run_id)
```

## Model Serving

**FastAPI + MLflow**

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mlflow.pyfunc
import numpy as np

app = FastAPI(title="Fraud Detection API")

# Load model at startup
model = mlflow.pyfunc.load_model("models:/fraud-detector/Production")

class PredictionRequest(BaseModel):
    amount: float
    merchant_category: str
    hour_of_day: int
    user_rolling_7d: float

class PredictionResponse(BaseModel):
    fraud_probability: float
    is_fraud: bool
    model_version: str

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    try:
        features = pd.DataFrame([request.dict()])
        proba = model.predict(features)[0]
        return PredictionResponse(
            fraud_probability=float(proba),
            is_fraud=proba > 0.5,
            model_version=model.metadata.run_id[:8]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok", "model": "fraud-detector", "stage": "Production"}
```

**BentoML (Production Serving)**

```python
import bentoml
from bentoml.io import JSON, NumpyNdarray

fraud_model_runner = bentoml.mlflow.get("fraud-detector:latest").to_runner()

svc = bentoml.Service("fraud_detection", runners=[fraud_model_runner])

@svc.api(input=JSON(), output=JSON())
async def predict(input_data: dict) -> dict:
    features = preprocess(input_data)
    proba = await fraud_model_runner.predict.async_run(features)
    return {"fraud_probability": float(proba[0]), "is_fraud": proba[0] > 0.5}
```

```bash
# Serve locally
bentoml serve fraud_detection:latest --port 3000

# Containerize
bentoml containerize fraud_detection:latest -t fraud-api:latest

# Deploy to Kubernetes
bentoml deployment create fraud-detection --bento fraud_detection:latest --platform kubernetes
```

## Feature Store

**Feast (offline + online)**

```python
from feast import FeatureStore, Entity, FeatureView, Field
from feast.types import Float32, Int64

store = FeatureStore(repo_path=".")

# Define features
user_entity = Entity(name="user_id", description="User identifier")

transaction_fv = FeatureView(
    name="user_transaction_stats",
    entities=[user_entity],
    ttl=timedelta(days=7),
    schema=[
        Field(name="rolling_7d_avg", dtype=Float32),
        Field(name="transaction_count_30d", dtype=Int64),
        Field(name="max_single_transaction", dtype=Float32),
    ],
    source=BigQuerySource(table="project.features.user_transaction_stats")
)

# Get historical features for training
training_df = store.get_historical_features(
    entity_df=entity_df,
    features=["user_transaction_stats:rolling_7d_avg",
              "user_transaction_stats:transaction_count_30d"]
).to_df()

# Get online features for inference
online_features = store.get_online_features(
    features=["user_transaction_stats:rolling_7d_avg"],
    entity_rows=[{"user_id": "u123"}]
).to_dict()
```

## Model Monitoring

**Data Drift Detection**

```python
from evidently import ColumnMapping
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, TargetDriftPreset

report = Report(metrics=[
    DataDriftPreset(),
    TargetDriftPreset(),
])

report.run(reference_data=reference_df, current_data=production_df,
           column_mapping=ColumnMapping(target='label', prediction='prediction'))

report.save_html("drift_report.html")

# Check drift in code
results = report.as_dict()
drift_detected = results['metrics'][0]['result']['dataset_drift']
if drift_detected:
    trigger_retraining_pipeline()
```

**Prediction Monitoring**

```python
# Log predictions with input features to a monitoring table
async def predict_with_logging(features: dict) -> dict:
    start_time = time.time()
    prediction = model.predict(features)
    latency_ms = (time.time() - start_time) * 1000

    # Log to monitoring store (BigQuery, ClickHouse, etc.)
    await log_prediction({
        "timestamp": datetime.utcnow().isoformat(),
        "model_version": MODEL_VERSION,
        "features": features,
        "prediction": prediction,
        "latency_ms": latency_ms,
    })

    return prediction
```

**Key Metrics to Monitor**

- **Data drift**: distribution shift in input features (PSI, KS test, JS divergence)
- **Target drift**: shift in prediction distribution (if labels unavailable)
- **Concept drift**: model accuracy degrades even if input distribution is stable
- **Latency**: p50, p95, p99 inference latency
- **Throughput**: requests per second; queue depth if async
- **Error rate**: prediction failures, timeout rate

## CI/CD for ML

```yaml
# .github/workflows/ml-pipeline.yml
name: ML Training Pipeline

on:
  schedule:
    - cron: '0 2 * * 1' # Weekly retraining every Monday 2AM
  workflow_dispatch: # Manual trigger

jobs:
  train-and-evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run training pipeline
        run: |
          python training/pipeline.py \
            --start-date $(date -d '30 days ago' +%Y-%m-%d) \
            --end-date $(date +%Y-%m-%d)

      - name: Run model tests
        run: pytest tests/model/ -v

      - name: Compare against baseline
        run: python scripts/compare_models.py --challenger $NEW_RUN_ID --champion Production

      - name: Deploy if improved
        if: env.CHALLENGER_WINS == 'true'
        run: python scripts/deploy_model.py --run-id $NEW_RUN_ID
```

## Infrastructure

**Kubernetes + Seldon Core**

```yaml
apiVersion: machinelearning.seldon.io/v1
kind: SeldonDeployment
metadata:
  name: fraud-detector
spec:
  predictors:
    - name: default
      replicas: 3
      graph:
        name: classifier
        implementation: MLFLOW_SERVER
        modelUri: s3://models/fraud-detector/7
      traffic: 100
    - name: canary
      replicas: 1
      graph:
        name: classifier
        implementation: MLFLOW_SERVER
        modelUri: s3://models/fraud-detector/8
      traffic: 0 # Start at 0, ramp up after validation
```
