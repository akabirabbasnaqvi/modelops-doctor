import hashlib
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import UploadFile
from pandas.errors import EmptyDataError, ParserError

from app.core.config import PROJECT_ROOT, settings
from app.models.dataset import Dataset, DatasetProfile
from app.repositories.dataset import DatasetRepository
from app.repositories.project import ProjectRepository


MAX_DATASET_SIZE_BYTES = 10 * 1024 * 1024


class DatasetAlreadyExistsError(Exception):
    """Raised when a dataset version already exists."""


class DatasetNotFoundError(Exception):
    """Raised when a dataset cannot be found."""


class DatasetProjectNotFoundError(Exception):
    """Raised when the parent project cannot be found."""


class InvalidDatasetError(Exception):
    """Raised when an uploaded dataset is invalid."""


class DatasetService:
    """Validate, profile, store, and retrieve datasets."""

    def __init__(
        self,
        dataset_repository: DatasetRepository,
        project_repository: ProjectRepository,
    ) -> None:
        self.dataset_repository = dataset_repository
        self.project_repository = project_repository

    async def upload_dataset(
        self,
        project_id: int,
        dataset_type: str,
        version: str,
        upload: UploadFile,
    ) -> tuple[Dataset, DatasetProfile]:
        project = await self.project_repository.get_by_id(project_id)

        if project is None:
            raise DatasetProjectNotFoundError(
                f"Project with ID {project_id} was not found."
            )

        existing_dataset = await self.dataset_repository.get_by_identity(
            project_id=project_id,
            dataset_type=dataset_type,
            version=version,
        )

        if existing_dataset is not None:
            raise DatasetAlreadyExistsError(
                f"Dataset type '{dataset_type}' version '{version}' "
                f"already exists in project {project_id}."
            )

        safe_file_name = Path(upload.filename or "dataset.csv").name

        if Path(safe_file_name).suffix.lower() != ".csv":
            raise InvalidDatasetError("Only CSV files are supported.")

        file_content = await upload.read()

        if not file_content:
            raise InvalidDatasetError("The uploaded CSV file is empty.")

        if len(file_content) > MAX_DATASET_SIZE_BYTES:
            raise InvalidDatasetError("The uploaded CSV exceeds the 10 MB size limit.")

        try:
            dataframe = pd.read_csv(BytesIO(file_content))
        except (EmptyDataError, ParserError, UnicodeDecodeError) as error:
            raise InvalidDatasetError(
                "The uploaded file is not a valid readable CSV."
            ) from error

        if dataframe.empty:
            raise InvalidDatasetError("The CSV must contain at least one data row.")

        if len(dataframe.columns) == 0:
            raise InvalidDatasetError("The CSV must contain at least one column.")

        if project.target_column not in dataframe.columns:
            raise InvalidDatasetError(
                f"Target column '{project.target_column}' was not found in the CSV."
            )

        content_hash = hashlib.sha256(file_content).hexdigest()
        schema_hash = self._calculate_schema_hash(dataframe)

        profile_data = self._build_profile(
            dataframe=dataframe,
            target_column=project.target_column,
        )

        storage_directory = (
            PROJECT_ROOT / settings.storage_path / "datasets" / str(project_id)
        ).resolve()

        storage_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        stored_file_name = f"{dataset_type}_{version}_{content_hash[:12]}.csv"

        stored_file_path = storage_directory / stored_file_name
        stored_file_path.write_bytes(file_content)

        relative_file_path = stored_file_path.relative_to(PROJECT_ROOT)

        dataset_data = {
            "project_id": project_id,
            "dataset_type": dataset_type,
            "version": version,
            "file_name": safe_file_name,
            "file_path": relative_file_path.as_posix(),
            "content_hash": content_hash,
            "schema_hash": schema_hash,
            "row_count": int(dataframe.shape[0]),
            "column_count": int(dataframe.shape[1]),
        }

        try:
            return await self.dataset_repository.create(
                dataset_data=dataset_data,
                profile_data=profile_data,
            )
        except Exception:
            stored_file_path.unlink(missing_ok=True)
            raise

    async def list_datasets(
        self,
        project_id: int,
    ):
        project = await self.project_repository.get_by_id(project_id)

        if project is None:
            raise DatasetProjectNotFoundError(
                f"Project with ID {project_id} was not found."
            )

        return await self.dataset_repository.get_by_project(project_id)

    async def get_dataset_profile(
        self,
        dataset_id: int,
    ) -> DatasetProfile:
        dataset = await self.dataset_repository.get_by_id(dataset_id)

        if dataset is None:
            raise DatasetNotFoundError(f"Dataset with ID {dataset_id} was not found.")

        profile = await self.dataset_repository.get_profile(dataset_id)

        if profile is None:
            raise DatasetNotFoundError(
                f"Profile for dataset ID {dataset_id} was not found."
            )

        return profile

    @staticmethod
    def _calculate_schema_hash(
        dataframe: pd.DataFrame,
    ) -> str:
        schema_text = "|".join(
            f"{column}:{dataframe[column].dtype}" for column in dataframe.columns
        )

        return hashlib.sha256(schema_text.encode("utf-8")).hexdigest()

    @staticmethod
    def _build_profile(
        dataframe: pd.DataFrame,
        target_column: str,
    ) -> dict[str, Any]:
        missing_values = {
            str(column): int(count) for column, count in dataframe.isna().sum().items()
        }

        column_types = {
            str(column): str(data_type)
            for column, data_type in dataframe.dtypes.items()
        }

        numeric_summary: dict[str, Any] = {}

        for column in dataframe.select_dtypes(include="number").columns:
            series = dataframe[column].dropna()

            numeric_summary[str(column)] = {
                "count": int(series.count()),
                "mean": (float(series.mean()) if not series.empty else None),
                "minimum": (float(series.min()) if not series.empty else None),
                "maximum": (float(series.max()) if not series.empty else None),
                "standard_deviation": (float(series.std()) if len(series) > 1 else 0.0),
            }

        categorical_summary: dict[str, Any] = {}

        for column in dataframe.select_dtypes(exclude="number").columns:
            series = dataframe[column].dropna().astype(str)
            value_counts = series.value_counts()

            categorical_summary[str(column)] = {
                "count": int(series.count()),
                "unique": int(series.nunique()),
                "most_frequent": (
                    str(value_counts.index[0]) if not value_counts.empty else None
                ),
                "most_frequent_count": (
                    int(value_counts.iloc[0]) if not value_counts.empty else 0
                ),
            }

        target_counts = (
            dataframe[target_column]
            .fillna("MISSING")
            .astype(str)
            .value_counts(dropna=False)
        )

        class_distribution = {
            str(label): int(count) for label, count in target_counts.items()
        }

        return {
            "missing_values": missing_values,
            "column_types": column_types,
            "numeric_summary": numeric_summary,
            "categorical_summary": categorical_summary,
            "class_distribution": class_distribution,
        }
