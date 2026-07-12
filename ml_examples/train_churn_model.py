import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ML_EXAMPLES_DIR = PROJECT_ROOT / "ml_examples"

DATASET_PATH = ML_EXAMPLES_DIR / "sample_churn_training.csv"
ARTIFACT_DIRECTORY = ML_EXAMPLES_DIR / "artifacts"
METADATA_DIRECTORY = ML_EXAMPLES_DIR / "metadata"
PREDICTION_LOG_DIRECTORY = ML_EXAMPLES_DIR / "generated_prediction_logs"

MODEL_PATH = ARTIFACT_DIRECTORY / "churn_model_v1.joblib"
METADATA_PATH = METADATA_DIRECTORY / "churn_model_v1.json"
PREDICTION_LOG_PATH = PREDICTION_LOG_DIRECTORY / "generated_churn_predictions_v1.csv"

MLFLOW_DIRECTORY = PROJECT_ROOT / "mlruns"

TARGET_COLUMN = "churn"
MODEL_NAME = "Customer Churn Classifier"
MODEL_VERSION = "1.0.0"
RANDOM_STATE = 42


def load_dataset() -> pd.DataFrame:
    """Load and validate the sample churn dataset."""

    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Training dataset was not found: {DATASET_PATH}")

    dataframe = pd.read_csv(DATASET_PATH)

    if dataframe.empty:
        raise ValueError("The training dataset is empty.")

    if TARGET_COLUMN not in dataframe.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' was not found.")

    if dataframe[TARGET_COLUMN].nunique() < 2:
        raise ValueError("The target column must contain at least two classes.")

    return dataframe


def build_pipeline(
    numeric_features: list[str],
    categorical_features: list[str],
) -> Pipeline:
    """Build preprocessing and classification pipeline."""

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                "passthrough",
                numeric_features,
            ),
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
                categorical_features,
            ),
        ]
    )

    classifier = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,
        random_state=RANDOM_STATE,
        class_weight="balanced",
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )


def calculate_metrics(
    true_labels: pd.Series,
    predicted_labels: Any,
    positive_probabilities: Any,
) -> dict[str, float]:
    """Calculate binary-classification metrics."""

    return {
        "accuracy": float(accuracy_score(true_labels, predicted_labels)),
        "precision": float(
            precision_score(
                true_labels,
                predicted_labels,
                zero_division=0,
            )
        ),
        "recall": float(
            recall_score(
                true_labels,
                predicted_labels,
                zero_division=0,
            )
        ),
        "f1": float(
            f1_score(
                true_labels,
                predicted_labels,
                zero_division=0,
            )
        ),
        "roc_auc": float(
            roc_auc_score(
                true_labels,
                positive_probabilities,
            )
        ),
    }


def create_prediction_log(
    test_features: pd.DataFrame,
    true_labels: pd.Series,
    predicted_labels: Any,
    positive_probabilities: Any,
) -> pd.DataFrame:
    """Create a prediction log supported by ModelOps Doctor."""

    prediction_log = test_features.reset_index(drop=True).copy()

    timestamp = datetime.now(timezone.utc)

    prediction_log.insert(
        0,
        "timestamp",
        [timestamp.isoformat() for _ in range(len(prediction_log))],
    )

    prediction_log["true_label"] = true_labels.reset_index(drop=True)
    prediction_log["predicted_label"] = predicted_labels
    prediction_log["confidence"] = positive_probabilities

    return prediction_log


def save_metadata(
    metrics: dict[str, float],
    numeric_features: list[str],
    categorical_features: list[str],
    training_rows: int,
    testing_rows: int,
    mlflow_run_id: str,
) -> None:
    """Save model-registry metadata as JSON."""

    metadata = {
        "name": MODEL_NAME,
        "version": MODEL_VERSION,
        "algorithm": "Random Forest",
        "framework": "scikit-learn",
        "target_column": TARGET_COLUMN,
        "positive_class": "1",
        "metrics": metrics,
        "artifact_uri": MODEL_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "training_date": datetime.now(timezone.utc).isoformat(),
        "training_rows": training_rows,
        "testing_rows": testing_rows,
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "mlflow_run_id": mlflow_run_id,
    }

    METADATA_PATH.write_text(
        json.dumps(
            metadata,
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    """Train, evaluate, track, and save the churn model."""

    os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")

    ARTIFACT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )
    METADATA_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )
    PREDICTION_LOG_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )
    MLFLOW_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe = load_dataset()

    features = dataframe.drop(columns=[TARGET_COLUMN])
    target = dataframe[TARGET_COLUMN]

    numeric_features = list(features.select_dtypes(include="number").columns)

    categorical_features = list(features.select_dtypes(exclude="number").columns)

    train_features, test_features, train_target, test_target = train_test_split(
        features,
        target,
        test_size=0.30,
        random_state=RANDOM_STATE,
        stratify=target,
    )

    pipeline = build_pipeline(
        numeric_features=numeric_features,
        categorical_features=categorical_features,
    )

    tracking_uri = MLFLOW_DIRECTORY.resolve().as_uri()

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("modelops-doctor-churn")

    with mlflow.start_run(run_name="random-forest-v1") as run:
        pipeline.fit(
            train_features,
            train_target,
        )

        predicted_labels = pipeline.predict(test_features)

        positive_probabilities = pipeline.predict_proba(test_features)[:, 1]

        metrics = calculate_metrics(
            true_labels=test_target,
            predicted_labels=predicted_labels,
            positive_probabilities=positive_probabilities,
        )

        mlflow.log_params(
            {
                "algorithm": "RandomForestClassifier",
                "n_estimators": 100,
                "max_depth": 5,
                "random_state": RANDOM_STATE,
                "class_weight": "balanced",
                "training_rows": len(train_features),
                "testing_rows": len(test_features),
                "target_column": TARGET_COLUMN,
            }
        )

        mlflow.log_metrics(metrics)

        mlflow.set_tags(
            {
                "project": "ModelOps Doctor",
                "model_name": MODEL_NAME,
                "model_version": MODEL_VERSION,
                "dataset": DATASET_PATH.name,
                "purpose": "portfolio_demo",
            }
        )

        joblib.dump(
            pipeline,
            MODEL_PATH,
        )

        mlflow.log_artifact(
            str(MODEL_PATH),
            artifact_path="model_artifacts",
        )

        mlflow.log_artifact(
            str(DATASET_PATH),
            artifact_path="datasets",
        )

        mlflow.sklearn.log_model(
            sk_model=pipeline,
            name="model",
        )

        prediction_log = create_prediction_log(
            test_features=test_features,
            true_labels=test_target,
            predicted_labels=predicted_labels,
            positive_probabilities=positive_probabilities,
        )

        prediction_log.to_csv(
            PREDICTION_LOG_PATH,
            index=False,
        )

        mlflow.log_artifact(
            str(PREDICTION_LOG_PATH),
            artifact_path="prediction_logs",
        )

        save_metadata(
            metrics=metrics,
            numeric_features=numeric_features,
            categorical_features=categorical_features,
            training_rows=len(train_features),
            testing_rows=len(test_features),
            mlflow_run_id=run.info.run_id,
        )

        mlflow.log_artifact(
            str(METADATA_PATH),
            artifact_path="metadata",
        )

    print("Model training completed successfully.")
    print(f"Dataset: {DATASET_PATH}")
    print(f"Training rows: {len(train_features)}")
    print(f"Testing rows: {len(test_features)}")
    print(f"Model artifact: {MODEL_PATH}")
    print(f"Metadata: {METADATA_PATH}")
    print(f"Prediction log: {PREDICTION_LOG_PATH}")
    print(f"MLflow run ID: {run.info.run_id}")
    print("Metrics:")

    for metric_name, metric_value in metrics.items():
        print(f"  {metric_name}: {metric_value:.4f}")


if __name__ == "__main__":
    main()
