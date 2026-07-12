import hashlib
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import UploadFile
from pandas.errors import EmptyDataError, ParserError

from app.core.config import PROJECT_ROOT, settings
from app.models.prediction import PredictionBatch
from app.repositories.model_version import ModelVersionRepository
from app.repositories.prediction import PredictionRepository
from app.repositories.project import ProjectRepository


MAX_PREDICTION_FILE_SIZE_BYTES = 10 * 1024 * 1024

RESERVED_COLUMNS = {
    "timestamp",
    "true_label",
    "predicted_label",
    "confidence",
}


class InvalidPredictionLogError(Exception):
    """Raised when a prediction-log CSV is invalid."""


class PredictionBatchAlreadyExistsError(Exception):
    """Raised when the same prediction file was already uploaded."""


class PredictionBatchNotFoundError(Exception):
    """Raised when a prediction batch cannot be found."""


class PredictionProjectNotFoundError(Exception):
    """Raised when the parent project cannot be found."""


class PredictionModelNotFoundError(Exception):
    """Raised when the selected model version cannot be found."""


class ModelProjectMismatchError(Exception):
    """Raised when a model does not belong to the selected project."""


class PredictionService:
    """Validate, store, and retrieve prediction logs."""

    def __init__(
        self,
        prediction_repository: PredictionRepository,
        project_repository: ProjectRepository,
        model_repository: ModelVersionRepository,
    ) -> None:
        self.prediction_repository = prediction_repository
        self.project_repository = project_repository
        self.model_repository = model_repository

    async def upload_prediction_log(
        self,
        project_id: int,
        model_version_id: int,
        upload: UploadFile,
    ) -> PredictionBatch:
        project = await self.project_repository.get_by_id(project_id)

        if project is None:
            raise PredictionProjectNotFoundError(
                f"Project with ID {project_id} was not found."
            )

        model_version = await self.model_repository.get_by_id(model_version_id)

        if model_version is None:
            raise PredictionModelNotFoundError(
                f"Model version with ID {model_version_id} was not found."
            )

        if model_version.project_id != project_id:
            raise ModelProjectMismatchError(
                f"Model version {model_version_id} does not belong "
                f"to project {project_id}."
            )

        safe_file_name = Path(upload.filename or "predictions.csv").name

        if Path(safe_file_name).suffix.lower() != ".csv":
            raise InvalidPredictionLogError("Only CSV files are supported.")

        file_content = await upload.read()

        if not file_content:
            raise InvalidPredictionLogError("The uploaded prediction CSV is empty.")

        if len(file_content) > MAX_PREDICTION_FILE_SIZE_BYTES:
            raise InvalidPredictionLogError(
                "The prediction CSV exceeds the 10 MB size limit."
            )

        try:
            dataframe = pd.read_csv(BytesIO(file_content))
        except (EmptyDataError, ParserError, UnicodeDecodeError) as error:
            raise InvalidPredictionLogError(
                "The uploaded file is not a valid readable CSV."
            ) from error

        if dataframe.empty:
            raise InvalidPredictionLogError(
                "The prediction CSV must contain at least one row."
            )

        if "predicted_label" not in dataframe.columns:
            raise InvalidPredictionLogError(
                "Required column 'predicted_label' is missing."
            )

        if dataframe["predicted_label"].isna().any():
            raise InvalidPredictionLogError(
                "The 'predicted_label' column cannot contain missing values."
            )

        if "confidence" in dataframe.columns:
            self._validate_confidence(dataframe["confidence"])

        parsed_timestamps = self._parse_timestamps(dataframe)

        content_hash = hashlib.sha256(file_content).hexdigest()

        existing_batch = await self.prediction_repository.get_by_content_hash(
            project_id=project_id,
            model_version_id=model_version_id,
            content_hash=content_hash,
        )

        if existing_batch is not None:
            raise PredictionBatchAlreadyExistsError(
                "This prediction file has already been uploaded "
                "for the selected model version."
            )

        is_labeled = (
            "true_label" in dataframe.columns and dataframe["true_label"].notna().any()
        )

        prediction_rows = self._build_prediction_rows(
            dataframe=dataframe,
            parsed_timestamps=parsed_timestamps,
        )

        storage_directory = (
            PROJECT_ROOT / settings.storage_path / "prediction_logs" / str(project_id)
        ).resolve()

        storage_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        stored_file_name = f"model_{model_version_id}_{content_hash[:12]}.csv"

        stored_file_path = storage_directory / stored_file_name
        stored_file_path.write_bytes(file_content)

        relative_file_path = stored_file_path.relative_to(PROJECT_ROOT)

        batch_data = {
            "project_id": project_id,
            "model_version_id": model_version_id,
            "file_name": safe_file_name,
            "file_path": relative_file_path.as_posix(),
            "content_hash": content_hash,
            "row_count": int(len(dataframe)),
            "is_labeled": is_labeled,
            "status": "processed",
            "error_message": None,
        }

        try:
            return await self.prediction_repository.create_batch(
                batch_data=batch_data,
                prediction_rows=prediction_rows,
            )
        except Exception:
            stored_file_path.unlink(missing_ok=True)
            raise

    async def list_batches(
        self,
        project_id: int,
    ):
        project = await self.project_repository.get_by_id(project_id)

        if project is None:
            raise PredictionProjectNotFoundError(
                f"Project with ID {project_id} was not found."
            )

        return await self.prediction_repository.get_batches_by_project(project_id)

    async def get_batch_detail(
        self,
        batch_id: int,
    ):
        batch = await self.prediction_repository.get_batch_by_id(batch_id)

        if batch is None:
            raise PredictionBatchNotFoundError(
                f"Prediction batch with ID {batch_id} was not found."
            )

        predictions = await self.prediction_repository.get_predictions_by_batch(
            batch_id
        )

        return batch, predictions

    @staticmethod
    def _validate_confidence(series: pd.Series) -> None:
        numeric_confidence = pd.to_numeric(
            series,
            errors="coerce",
        )

        invalid_nonempty_values = series.notna() & numeric_confidence.isna()

        if invalid_nonempty_values.any():
            raise InvalidPredictionLogError("Confidence values must be numeric.")

        valid_values = numeric_confidence.dropna()

        if ((valid_values < 0) | (valid_values > 1)).any():
            raise InvalidPredictionLogError(
                "Confidence values must be between 0 and 1."
            )

    @staticmethod
    def _parse_timestamps(
        dataframe: pd.DataFrame,
    ) -> pd.Series | None:
        if "timestamp" not in dataframe.columns:
            return None

        parsed = pd.to_datetime(
            dataframe["timestamp"],
            errors="coerce",
            utc=True,
        )

        invalid_timestamps = dataframe["timestamp"].notna() & parsed.isna()

        if invalid_timestamps.any():
            raise InvalidPredictionLogError("One or more timestamp values are invalid.")

        return parsed

    @classmethod
    def _build_prediction_rows(
        cls,
        dataframe: pd.DataFrame,
        parsed_timestamps: pd.Series | None,
    ) -> list[dict[str, Any]]:
        feature_columns = [
            column for column in dataframe.columns if column not in RESERVED_COLUMNS
        ]

        prediction_rows: list[dict[str, Any]] = []

        for row_position, (_, row) in enumerate(dataframe.iterrows()):
            timestamp_value = None

            if parsed_timestamps is not None:
                parsed_value = parsed_timestamps.iloc[row_position]

                if not pd.isna(parsed_value):
                    timestamp_value = parsed_value.to_pydatetime()

            true_label = cls._optional_string(row.get("true_label"))

            confidence = cls._optional_float(row.get("confidence"))

            features = {
                str(column): cls._json_safe_value(row[column])
                for column in feature_columns
            }

            prediction_rows.append(
                {
                    "prediction_timestamp": timestamp_value,
                    "true_label": true_label,
                    "predicted_label": str(row["predicted_label"]),
                    "confidence": confidence,
                    "features": features,
                }
            )

        return prediction_rows

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        if value is None or pd.isna(value):
            return None

        return str(value)

    @staticmethod
    def _optional_float(value: Any) -> float | None:
        if value is None or pd.isna(value):
            return None

        return float(value)

    @staticmethod
    def _json_safe_value(value: Any) -> Any:
        if value is None or pd.isna(value):
            return None

        if hasattr(value, "item"):
            return value.item()

        if isinstance(value, datetime):
            return value.isoformat()

        return value
