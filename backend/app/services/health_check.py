from typing import Any

import pandas as pd

from app.core.config import PROJECT_ROOT
from app.mlops.diagnosis import generate_diagnosis
from app.mlops.drift import analyze_feature_drift
from app.mlops.health import (
    calculate_component_scores,
    calculate_health_score,
)
from app.mlops.metrics import (
    calculate_classification_metrics,
    calculate_unlabeled_prediction_metrics,
)
from app.repositories.dataset import DatasetRepository
from app.repositories.health_check import HealthCheckRepository
from app.repositories.model_version import ModelVersionRepository
from app.repositories.project import ProjectRepository
from app.schemas.health_check import HealthCheckRunRequest


class HealthCheckResourceNotFoundError(Exception):
    """Raised when a required monitoring resource is missing."""


class HealthCheckRelationshipError(Exception):
    """Raised when monitoring resources do not belong together."""


class InvalidHealthCheckDataError(Exception):
    """Raised when monitoring data cannot be analyzed."""


class HealthCheckService:
    """Run and persist model-health analysis."""

    def __init__(
        self,
        health_repository: HealthCheckRepository,
        project_repository: ProjectRepository,
        model_repository: ModelVersionRepository,
        dataset_repository: DatasetRepository,
    ) -> None:
        self.health_repository = health_repository
        self.project_repository = project_repository
        self.model_repository = model_repository
        self.dataset_repository = dataset_repository

    async def run_health_check(
        self,
        project_id: int,
        request: HealthCheckRunRequest,
    ):
        project = await self.project_repository.get_by_id(project_id)

        if project is None:
            raise HealthCheckResourceNotFoundError(
                f"Project with ID {project_id} was not found."
            )

        model_version = await self.model_repository.get_by_id(request.model_version_id)

        if model_version is None:
            raise HealthCheckResourceNotFoundError(
                f"Model version with ID {request.model_version_id} was not found."
            )

        baseline_dataset = await self.dataset_repository.get_by_id(
            request.baseline_dataset_id
        )

        if baseline_dataset is None:
            raise HealthCheckResourceNotFoundError(
                f"Dataset with ID {request.baseline_dataset_id} was not found."
            )

        prediction_batch = await self.health_repository.get_prediction_batch(
            request.prediction_batch_id
        )

        if prediction_batch is None:
            raise HealthCheckResourceNotFoundError(
                f"Prediction batch with ID {request.prediction_batch_id} was not found."
            )

        self._validate_relationships(
            project_id=project_id,
            model_project_id=model_version.project_id,
            dataset_project_id=baseline_dataset.project_id,
            batch_project_id=prediction_batch.project_id,
            batch_model_id=prediction_batch.model_version_id,
            requested_model_id=request.model_version_id,
        )

        baseline_path = (PROJECT_ROOT / baseline_dataset.file_path).resolve()

        if not baseline_path.exists():
            raise InvalidHealthCheckDataError(
                f"Baseline dataset file was not found: {baseline_dataset.file_path}"
            )

        baseline_dataframe = pd.read_csv(baseline_path)

        predictions = await self.health_repository.get_predictions(
            request.prediction_batch_id
        )

        if not predictions:
            raise InvalidHealthCheckDataError(
                "The prediction batch contains no prediction records."
            )

        current_dataframe = self._build_current_dataframe(predictions)

        reference_features = baseline_dataframe.drop(
            columns=[project.target_column],
            errors="ignore",
        )

        drift_result = analyze_feature_drift(
            reference_dataframe=reference_features,
            current_dataframe=current_dataframe,
        )

        metrics_result = self._calculate_metrics(
            predictions=predictions,
            positive_class=project.positive_class,
        )

        missing_rate = self._calculate_missing_rate(current_dataframe)

        component_scores = calculate_component_scores(
            metrics=metrics_result,
            drift=drift_result,
            missing_rate=missing_rate,
        )

        health_result = calculate_health_score(
            performance_score=component_scores["performance_score"],
            drift_score=component_scores["drift_score"],
            data_quality_score=component_scores["data_quality_score"],
            confidence_score=component_scores["confidence_score"],
            class_balance_score=component_scores["class_balance_score"],
        )

        diagnosis_result = generate_diagnosis(
            metrics=metrics_result,
            drift=drift_result,
            health=health_result,
            missing_rate=missing_rate,
        )

        health_data = {
            "project_id": project_id,
            "model_version_id": request.model_version_id,
            "baseline_dataset_id": request.baseline_dataset_id,
            "prediction_batch_id": request.prediction_batch_id,
            "status": health_result["status"],
            "health_score": health_result["health_score"],
            "metrics": metrics_result,
            "drift": drift_result,
            "component_scores": component_scores,
            "missing_rate": missing_rate,
        }

        diagnosis_data = {
            "summary": diagnosis_result["summary"],
            "risk_level": diagnosis_result["risk_level"],
            "retraining_recommended": diagnosis_result["retraining_recommended"],
            "findings": diagnosis_result["findings"],
            "recommendations": diagnosis_result["recommendations"],
        }

        return await self.health_repository.create_health_check(
            health_data=health_data,
            diagnosis_data=diagnosis_data,
        )

    async def get_latest_health_check(
        self,
        project_id: int,
    ):
        project = await self.project_repository.get_by_id(project_id)

        if project is None:
            raise HealthCheckResourceNotFoundError(
                f"Project with ID {project_id} was not found."
            )

        health_check = await self.health_repository.get_latest_by_project(project_id)

        if health_check is None:
            raise HealthCheckResourceNotFoundError(
                f"No health check exists for project {project_id}."
            )

        return health_check

    async def get_diagnosis_report(
        self,
        health_check_id: int,
    ):
        health_check = await self.health_repository.get_by_id(health_check_id)

        if health_check is None:
            raise HealthCheckResourceNotFoundError(
                f"Health check with ID {health_check_id} was not found."
            )

        report = await self.health_repository.get_report(health_check_id)

        if report is None:
            raise HealthCheckResourceNotFoundError(
                f"Diagnosis report for health check {health_check_id} was not found."
            )

        return report

    @staticmethod
    def _validate_relationships(
        project_id: int,
        model_project_id: int,
        dataset_project_id: int,
        batch_project_id: int,
        batch_model_id: int,
        requested_model_id: int,
    ) -> None:
        if model_project_id != project_id:
            raise HealthCheckRelationshipError(
                "The selected model version does not belong to the selected project."
            )

        if dataset_project_id != project_id:
            raise HealthCheckRelationshipError(
                "The baseline dataset does not belong to the selected project."
            )

        if batch_project_id != project_id:
            raise HealthCheckRelationshipError(
                "The prediction batch does not belong to the selected project."
            )

        if batch_model_id != requested_model_id:
            raise HealthCheckRelationshipError(
                "The prediction batch was not generated by the selected model version."
            )

    @staticmethod
    def _build_current_dataframe(
        predictions: list,
    ) -> pd.DataFrame:
        feature_rows = [prediction.features for prediction in predictions]

        return pd.DataFrame(feature_rows)

    @staticmethod
    def _calculate_metrics(
        predictions: list,
        positive_class: str | None,
    ) -> dict[str, Any]:
        predicted_labels = [prediction.predicted_label for prediction in predictions]

        confidence_values = [prediction.confidence for prediction in predictions]

        usable_confidences = (
            confidence_values
            if all(value is not None for value in confidence_values)
            else None
        )

        true_labels = [prediction.true_label for prediction in predictions]

        is_fully_labeled = all(value is not None for value in true_labels)

        if is_fully_labeled:
            return calculate_classification_metrics(
                true_labels=true_labels,
                predicted_labels=predicted_labels,
                confidences=usable_confidences,
                positive_class=positive_class,
            )

        return calculate_unlabeled_prediction_metrics(
            predicted_labels=predicted_labels,
            confidences=usable_confidences,
        )

    @staticmethod
    def _calculate_missing_rate(
        dataframe: pd.DataFrame,
    ) -> float:
        total_values = dataframe.shape[0] * dataframe.shape[1]

        if total_values == 0:
            return 0.0

        missing_values = int(dataframe.isna().sum().sum())

        return float(missing_values / total_values)
