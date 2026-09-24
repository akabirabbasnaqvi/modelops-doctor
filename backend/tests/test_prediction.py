"""Validation tests for PredictionService.

These exercise the branches in app/services/prediction.py that reject bad
prediction logs, plus the row-building helpers, using in-memory fake
repositories so no database or network is required.
"""

import asyncio
from io import BytesIO
from types import SimpleNamespace

import pandas as pd
import pytest
from fastapi import UploadFile

from app.services import prediction as prediction_module
from app.services.prediction import (
    InvalidPredictionLogError,
    ModelProjectMismatchError,
    PredictionBatchAlreadyExistsError,
    PredictionBatchNotFoundError,
    PredictionModelNotFoundError,
    PredictionProjectNotFoundError,
    PredictionService,
)


def run(coroutine):
    """Execute a coroutine from a synchronous test."""

    return asyncio.run(coroutine)


def make_upload(
    content: bytes,
    filename: str = "predictions.csv",
) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=BytesIO(content),
    )


LABELED_CSV = (
    b"timestamp,age,true_label,predicted_label,confidence\n"
    b"2026-01-05T10:00:00Z,31,1,1,0.91\n"
    b"2026-01-05T11:00:00Z,47,0,0,0.78\n"
)

UNLABELED_CSV = b"age,predicted_label,confidence\n31,1,0.91\n47,0,0.78\n"


class FakeProjectRepository:
    def __init__(self, project=None) -> None:
        self.project = project

    async def get_by_id(self, project_id: int):
        if self.project is None or self.project.id != project_id:
            return None

        return self.project


class FakeModelRepository:
    def __init__(self, model=None) -> None:
        self.model = model

    async def get_by_id(self, model_version_id: int):
        if self.model is None or self.model.id != model_version_id:
            return None

        return self.model


class FakePredictionRepository:
    def __init__(
        self,
        existing_batch=None,
        batch=None,
        predictions=None,
        create_error: Exception | None = None,
    ) -> None:
        self.existing_batch = existing_batch
        self.batch = batch
        self.predictions = predictions or []
        self.create_error = create_error
        self.created_batch_data: dict | None = None
        self.created_rows: list | None = None

    async def get_by_content_hash(
        self,
        project_id: int,
        model_version_id: int,
        content_hash: str,
    ):
        return self.existing_batch

    async def create_batch(self, batch_data: dict, prediction_rows: list):
        if self.create_error is not None:
            raise self.create_error

        self.created_batch_data = batch_data
        self.created_rows = prediction_rows

        return SimpleNamespace(id=1, **batch_data)

    async def get_batches_by_project(self, project_id: int):
        return []

    async def get_batch_by_id(self, batch_id: int):
        return self.batch

    async def get_predictions_by_batch(self, batch_id: int):
        return self.predictions


@pytest.fixture
def project():
    return SimpleNamespace(id=1, target_column="churn")


@pytest.fixture
def model():
    return SimpleNamespace(id=5, project_id=1)


@pytest.fixture
def storage(tmp_path, monkeypatch):
    """Redirect prediction-log storage into a temporary directory."""

    monkeypatch.setattr(prediction_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(prediction_module.settings, "storage_path", "storage")

    return tmp_path


def build_service(
    project=None,
    model=None,
    existing_batch=None,
    batch=None,
    create_error: Exception | None = None,
):
    prediction_repository = FakePredictionRepository(
        existing_batch=existing_batch,
        batch=batch,
        create_error=create_error,
    )

    service = PredictionService(
        prediction_repository=prediction_repository,
        project_repository=FakeProjectRepository(project),
        model_repository=FakeModelRepository(model),
    )

    return service, prediction_repository


def upload_csv(
    service: PredictionService,
    content: bytes,
    filename: str = "predictions.csv",
):
    return run(
        service.upload_prediction_log(
            project_id=1,
            model_version_id=5,
            upload=make_upload(content, filename),
        )
    )


class TestOwnershipValidation:
    def test_missing_project_is_rejected(self, model):
        service, _ = build_service(project=None, model=model)

        with pytest.raises(PredictionProjectNotFoundError):
            upload_csv(service, LABELED_CSV)

    def test_missing_model_version_is_rejected(self, project):
        service, _ = build_service(project=project, model=None)

        with pytest.raises(PredictionModelNotFoundError):
            upload_csv(service, LABELED_CSV)

    def test_model_from_another_project_is_rejected(self, project):
        foreign_model = SimpleNamespace(id=5, project_id=99)

        service, _ = build_service(project=project, model=foreign_model)

        with pytest.raises(ModelProjectMismatchError):
            upload_csv(service, LABELED_CSV)


class TestFileValidation:
    def test_non_csv_extension_is_rejected(self, project, model):
        service, _ = build_service(project=project, model=model)

        with pytest.raises(InvalidPredictionLogError, match="Only CSV files"):
            upload_csv(service, LABELED_CSV, filename="predictions.json")

    def test_empty_file_is_rejected(self, project, model):
        service, _ = build_service(project=project, model=model)

        with pytest.raises(InvalidPredictionLogError, match="empty"):
            upload_csv(service, b"")

    def test_oversized_file_is_rejected(self, project, model, monkeypatch):
        monkeypatch.setattr(
            prediction_module,
            "MAX_PREDICTION_FILE_SIZE_BYTES",
            10,
        )

        service, _ = build_service(project=project, model=model)

        with pytest.raises(InvalidPredictionLogError, match="size limit"):
            upload_csv(service, LABELED_CSV)

    def test_unreadable_csv_is_rejected(self, project, model):
        service, _ = build_service(project=project, model=model)

        with pytest.raises(
            InvalidPredictionLogError,
            match="not a valid readable CSV",
        ):
            upload_csv(service, b"\xff\xfe\x00\x00binary-not-text")

    def test_header_only_csv_is_rejected(self, project, model):
        service, _ = build_service(project=project, model=model)

        with pytest.raises(InvalidPredictionLogError, match="at least one row"):
            upload_csv(service, b"age,predicted_label\n")


class TestColumnValidation:
    def test_missing_predicted_label_column_is_rejected(self, project, model):
        service, _ = build_service(project=project, model=model)

        with pytest.raises(
            InvalidPredictionLogError,
            match="'predicted_label' is missing",
        ):
            upload_csv(service, b"age,confidence\n31,0.9\n")

    def test_null_predicted_label_is_rejected(self, project, model):
        service, _ = build_service(project=project, model=model)

        with pytest.raises(
            InvalidPredictionLogError,
            match="cannot contain missing values",
        ):
            upload_csv(service, b"age,predicted_label\n31,1\n47,\n")

    def test_non_numeric_confidence_is_rejected(self, project, model):
        service, _ = build_service(project=project, model=model)

        with pytest.raises(InvalidPredictionLogError, match="must be numeric"):
            upload_csv(
                service,
                b"age,predicted_label,confidence\n31,1,very-sure\n",
            )

    def test_confidence_above_one_is_rejected(self, project, model):
        service, _ = build_service(project=project, model=model)

        with pytest.raises(InvalidPredictionLogError, match="between 0 and 1"):
            upload_csv(
                service,
                b"age,predicted_label,confidence\n31,1,1.4\n",
            )

    def test_negative_confidence_is_rejected(self, project, model):
        service, _ = build_service(project=project, model=model)

        with pytest.raises(InvalidPredictionLogError, match="between 0 and 1"):
            upload_csv(
                service,
                b"age,predicted_label,confidence\n31,1,-0.2\n",
            )

    def test_invalid_timestamp_is_rejected(self, project, model):
        service, _ = build_service(project=project, model=model)

        with pytest.raises(InvalidPredictionLogError, match="timestamp"):
            upload_csv(
                service,
                b"timestamp,predicted_label\nnot-a-date,1\n",
            )


class TestDuplicateDetection:
    def test_same_file_twice_is_rejected(self, project, model):
        service, _ = build_service(
            project=project,
            model=model,
            existing_batch=SimpleNamespace(id=7),
        )

        with pytest.raises(PredictionBatchAlreadyExistsError):
            upload_csv(service, LABELED_CSV)


class TestUploadSuccess:
    def test_labeled_log_is_stored(self, project, model, storage):
        service, repository = build_service(project=project, model=model)

        batch = upload_csv(service, LABELED_CSV)

        assert batch.row_count == 2
        assert batch.is_labeled is True
        assert batch.status == "processed"
        assert batch.error_message is None
        assert len(batch.content_hash) == 64

        assert (storage / batch.file_path).read_bytes() == LABELED_CSV

    def test_unlabeled_log_is_flagged(self, project, model, storage):
        service, _ = build_service(project=project, model=model)

        batch = upload_csv(service, UNLABELED_CSV)

        assert batch.is_labeled is False

    def test_reserved_columns_are_excluded_from_features(
        self,
        project,
        model,
        storage,
    ):
        service, repository = build_service(project=project, model=model)

        upload_csv(service, LABELED_CSV)

        first_row = repository.created_rows[0]

        assert first_row["features"] == {"age": 31}
        assert first_row["predicted_label"] == "1"
        assert first_row["true_label"] == "1"
        assert first_row["confidence"] == pytest.approx(0.91)
        assert first_row["prediction_timestamp"] is not None

    def test_missing_optional_columns_become_none(
        self,
        project,
        model,
        storage,
    ):
        service, repository = build_service(project=project, model=model)

        upload_csv(service, b"age,predicted_label\n31,1\n")

        first_row = repository.created_rows[0]

        assert first_row["true_label"] is None
        assert first_row["confidence"] is None
        assert first_row["prediction_timestamp"] is None

    def test_stored_file_is_removed_when_persistence_fails(
        self,
        project,
        model,
        storage,
    ):
        service, _ = build_service(
            project=project,
            model=model,
            create_error=RuntimeError("database is down"),
        )

        with pytest.raises(RuntimeError):
            upload_csv(service, LABELED_CSV)

        assert list((storage / "storage").rglob("*.csv")) == []


class TestLookups:
    def test_list_batches_requires_existing_project(self):
        service, _ = build_service(project=None)

        with pytest.raises(PredictionProjectNotFoundError):
            run(service.list_batches(project_id=1))

    def test_missing_batch_detail_is_rejected(self):
        service, _ = build_service(batch=None)

        with pytest.raises(PredictionBatchNotFoundError):
            run(service.get_batch_detail(batch_id=404))


class TestHelpers:
    def test_blank_confidence_column_is_allowed(self):
        series = pd.Series([0.4, None, 0.9])

        PredictionService._validate_confidence(series)

    def test_confidence_at_bounds_is_allowed(self):
        series = pd.Series([0.0, 1.0])

        PredictionService._validate_confidence(series)

    def test_timestamps_are_optional(self):
        dataframe = pd.DataFrame({"predicted_label": [1]})

        assert PredictionService._parse_timestamps(dataframe) is None

    def test_optional_float_handles_missing_values(self):
        assert PredictionService._optional_float(None) is None
        assert PredictionService._optional_float(float("nan")) is None
        assert PredictionService._optional_float("0.5") == pytest.approx(0.5)

    def test_optional_string_handles_missing_values(self):
        assert PredictionService._optional_string(None) is None
        assert PredictionService._optional_string(1) == "1"

    def test_json_safe_value_unwraps_numpy_scalars(self):
        numpy_value = pd.Series([7]).iloc[0]

        result = PredictionService._json_safe_value(numpy_value)

        assert result == 7
        assert isinstance(result, int)
