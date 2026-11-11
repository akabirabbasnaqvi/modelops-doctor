# ModelOps Doctor DVC Workflow

ModelOps Doctor uses DVC to version machine-learning datasets separately from Git.

## Dataset access after cloning

Git contains `sample_churn_training.csv.dvc`, not the training CSV itself.
The configured `localstorage` remote points to a local `dvc-storage` folder;
its cache is not distributed with the repository. A new clone therefore
cannot restore that CSV unless the remote already contains the tracked
object. Obtain the existing DVC remote/cache from the project maintainer,
or configure a shared remote containing that data before running `dvc pull`.

Install DVC and MLflow separately if you use the optional data and training
examples. They are not required to build the application or run its tests.
You can exercise CSV uploads with your own data and use the included
`sample_prediction_logs/churn_predictions_v1.csv` as a prediction-log example.

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
