# ModelOps Doctor DVC Workflow

ModelOps Doctor uses DVC to version machine-learning datasets separately from Git.

## Track the Training Dataset

```powershell
dvc add ml_examples\sample_churn_training.csv
```

## Push the Dataset

```powershell
dvc push
```

## Restore the Dataset

```powershell
dvc pull
```

## Check DVC Status

```powershell
dvc status
```

## MLOps Tools

- DVC versions datasets.
- MLflow tracks experiments, parameters, metrics, and model artifacts.
- PostgreSQL stores application metadata and monitoring results.
- Redis and Celery run background health checks.