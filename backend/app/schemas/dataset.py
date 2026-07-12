from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


DatasetType = Literal[
    "training",
    "validation",
    "testing",
    "production",
]


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    dataset_type: str
    version: str
    file_name: str
    file_path: str
    content_hash: str
    schema_hash: str
    row_count: int
    column_count: int
    created_at: datetime


class DatasetListResponse(BaseModel):
    total: int
    datasets: list[DatasetResponse]


class DatasetProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: int
    missing_values: dict[str, Any]
    column_types: dict[str, Any]
    numeric_summary: dict[str, Any]
    categorical_summary: dict[str, Any]
    class_distribution: dict[str, Any]
    created_at: datetime


class DatasetUploadResponse(BaseModel):
    dataset: DatasetResponse
    profile: DatasetProfileResponse
