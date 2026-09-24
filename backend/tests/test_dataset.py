"""Validation and profiling tests for DatasetService.

These exercise the branches in app/services/dataset.py that reject bad
uploads, plus the profiling helpers, using in-memory fake repositories so
no database or network is required.
"""

import asyncio
from io import BytesIO
from types import SimpleNamespace

import pandas as pd
import pytest
from fastapi import UploadFile

from app.services import dataset as dataset_module
from app.services.dataset import (
    DatasetAlreadyExistsError,
    DatasetNotFoundError,
    DatasetProjectNotFoundError,
    DatasetService,
    InvalidDatasetError,
)


def run(coroutine):
    """Execute a coroutine from a synchronous test."""

    return asyncio.run(coroutine)


def make_upload(
    content: bytes,
    filename: str = "training.csv",
) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=BytesIO(content),
    )


CSV_WITH_TARGET = b"age,city,churn\n31,leeds,1\n47,york,0\n52,leeds,1\n"


class FakeProjectRepository:
    def __init__(self, project=None) -> None:
        self.project = project

    async def get_by_id(self, project_id: int):
        if self.project is None:
            return None

        if self.project.id != project_id:
            return None

        return self.project


class FakeDatasetRepository:
    def __init__(
        self,
        existing=None,
        profile=None,
        create_error: Exception | None = None,
    ) -> None:
        self.existing = existing
        self.profile = profile
        self.create_error = create_error
        self.created_dataset_data: dict | None = None
        self.created_profile_data: dict | None = None

    async def get_by_identity(
        self,
        project_id: int,
        dataset_type: str,
        version: str,
    ):
        return self.existing

    async def create(self, dataset_data: dict, profile_data: dict):
        if self.create_error is not None:
            raise self.create_error

        self.created_dataset_data = dataset_data
        self.created_profile_data = profile_data

        return (
            SimpleNamespace(id=1, **dataset_data),
            SimpleNamespace(id=1, **profile_data),
        )

    async def get_by_id(self, dataset_id: int):
        return self.existing

    async def get_profile(self, dataset_id: int):
        return self.profile


@pytest.fixture
def project():
    return SimpleNamespace(id=1, target_column="churn")


@pytest.fixture
def storage(tmp_path, monkeypatch):
    """Redirect dataset storage into a temporary directory."""

    monkeypatch.setattr(dataset_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(dataset_module.settings, "storage_path", "storage")

    return tmp_path


def build_service(
    project=None,
    existing_dataset=None,
    profile=None,
    create_error: Exception | None = None,
):
    dataset_repository = FakeDatasetRepository(
        existing=existing_dataset,
        profile=profile,
        create_error=create_error,
    )

    service = DatasetService(
        dataset_repository=dataset_repository,
        project_repository=FakeProjectRepository(project),
    )

    return service, dataset_repository


def upload_csv(
    service: DatasetService,
    content: bytes,
    filename: str = "training.csv",
):
    return run(
        service.upload_dataset(
            project_id=1,
            dataset_type="training",
            version="1.0.0",
            upload=make_upload(content, filename),
        )
    )


class TestUploadValidation:
    def test_missing_project_is_rejected(self):
        service, _ = build_service(project=None)

        with pytest.raises(DatasetProjectNotFoundError):
            upload_csv(service, CSV_WITH_TARGET)

    def test_duplicate_version_is_rejected(self, project):
        service, _ = build_service(
            project=project,
            existing_dataset=SimpleNamespace(id=9),
        )

        with pytest.raises(DatasetAlreadyExistsError):
            upload_csv(service, CSV_WITH_TARGET)

    def test_non_csv_extension_is_rejected(self, project):
        service, _ = build_service(project=project)

        with pytest.raises(InvalidDatasetError, match="Only CSV files"):
            upload_csv(service, CSV_WITH_TARGET, filename="training.xlsx")

    def test_empty_file_is_rejected(self, project):
        service, _ = build_service(project=project)

        with pytest.raises(InvalidDatasetError, match="empty"):
            upload_csv(service, b"")

    def test_oversized_file_is_rejected(self, project, monkeypatch):
        monkeypatch.setattr(dataset_module, "MAX_DATASET_SIZE_BYTES", 10)

        service, _ = build_service(project=project)

        with pytest.raises(InvalidDatasetError, match="size limit"):
            upload_csv(service, CSV_WITH_TARGET)

    def test_unreadable_csv_is_rejected(self, project):
        service, _ = build_service(project=project)

        with pytest.raises(InvalidDatasetError, match="not a valid readable CSV"):
            upload_csv(service, b"\xff\xfe\x00\x00binary-not-text")

    def test_header_only_csv_is_rejected(self, project):
        service, _ = build_service(project=project)

        with pytest.raises(InvalidDatasetError, match="at least one data row"):
            upload_csv(service, b"age,city,churn\n")

    def test_missing_target_column_is_rejected(self, project):
        service, _ = build_service(project=project)

        with pytest.raises(InvalidDatasetError, match="Target column 'churn'"):
            upload_csv(service, b"age,city\n31,leeds\n")


class TestUploadSuccess:
    def test_valid_csv_is_stored_and_profiled(self, project, storage):
        service, repository = build_service(project=project)

        dataset, profile = upload_csv(service, CSV_WITH_TARGET)

        assert dataset.row_count == 3
        assert dataset.column_count == 3
        assert dataset.file_name == "training.csv"
        assert len(dataset.content_hash) == 64
        assert len(dataset.schema_hash) == 64

        stored_file = storage / dataset.file_path

        assert stored_file.exists()
        assert stored_file.read_bytes() == CSV_WITH_TARGET

        assert profile.class_distribution == {"1": 2, "0": 1}

    def test_directory_traversal_in_filename_is_stripped(self, project, storage):
        service, repository = build_service(project=project)

        dataset, _ = run(
            service.upload_dataset(
                project_id=1,
                dataset_type="training",
                version="1.0.0",
                upload=make_upload(
                    CSV_WITH_TARGET,
                    filename="../../etc/training.csv",
                ),
            )
        )

        assert dataset.file_name == "training.csv"

    def test_stored_file_is_removed_when_persistence_fails(self, project, storage):
        service, _ = build_service(
            project=project,
            create_error=RuntimeError("database is down"),
        )

        with pytest.raises(RuntimeError):
            upload_csv(service, CSV_WITH_TARGET)

        written_files = list((storage / "storage").rglob("*.csv"))

        assert written_files == []


class TestListAndProfileLookup:
    def test_list_datasets_requires_existing_project(self):
        service, _ = build_service(project=None)

        with pytest.raises(DatasetProjectNotFoundError):
            run(service.list_datasets(project_id=1))

    def test_missing_dataset_profile_is_rejected(self):
        service, _ = build_service(existing_dataset=None)

        with pytest.raises(DatasetNotFoundError):
            run(service.get_dataset_profile(dataset_id=404))


class TestProfiling:
    def test_schema_hash_changes_when_columns_change(self):
        first = pd.DataFrame({"a": [1], "b": ["x"]})
        second = pd.DataFrame({"a": [1], "c": ["x"]})

        assert DatasetService._calculate_schema_hash(
            first
        ) != DatasetService._calculate_schema_hash(second)

    def test_schema_hash_is_stable_for_identical_schemas(self):
        first = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        second = pd.DataFrame({"a": [7, 8], "b": ["p", "q"]})

        assert DatasetService._calculate_schema_hash(
            first
        ) == DatasetService._calculate_schema_hash(second)

    def test_profile_reports_missing_values_and_types(self):
        dataframe = pd.DataFrame(
            {
                "age": [30, None, 50],
                "city": ["leeds", "york", None],
                "churn": [1, 0, 1],
            }
        )

        profile = DatasetService._build_profile(
            dataframe=dataframe,
            target_column="churn",
        )

        assert profile["missing_values"]["age"] == 1
        assert profile["missing_values"]["city"] == 1
        assert profile["missing_values"]["churn"] == 0

        assert profile["column_types"]["city"] == "object"

    def test_profile_summarises_numeric_columns(self):
        dataframe = pd.DataFrame(
            {
                "age": [10, 20, 30],
                "churn": [1, 0, 1],
            }
        )

        profile = DatasetService._build_profile(
            dataframe=dataframe,
            target_column="churn",
        )

        age_summary = profile["numeric_summary"]["age"]

        assert age_summary["count"] == 3
        assert age_summary["mean"] == pytest.approx(20.0)
        assert age_summary["minimum"] == pytest.approx(10.0)
        assert age_summary["maximum"] == pytest.approx(30.0)
        assert age_summary["standard_deviation"] == pytest.approx(10.0)

    def test_profile_summarises_categorical_columns(self):
        dataframe = pd.DataFrame(
            {
                "city": ["leeds", "leeds", "york"],
                "churn": [1, 0, 1],
            }
        )

        profile = DatasetService._build_profile(
            dataframe=dataframe,
            target_column="churn",
        )

        city_summary = profile["categorical_summary"]["city"]

        assert city_summary["count"] == 3
        assert city_summary["unique"] == 2
        assert city_summary["most_frequent"] == "leeds"
        assert city_summary["most_frequent_count"] == 2

    def test_profile_counts_missing_target_labels(self):
        dataframe = pd.DataFrame(
            {
                "age": [10, 20],
                "churn": ["1", None],
            }
        )

        profile = DatasetService._build_profile(
            dataframe=dataframe,
            target_column="churn",
        )

        assert profile["class_distribution"]["MISSING"] == 1
        assert profile["class_distribution"]["1"] == 1
