from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ModelVersionCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=150,
        examples=["Customer Churn Classifier"],
    )

    version: str = Field(
        min_length=1,
        max_length=50,
        examples=["1.0.0"],
    )

    algorithm: str = Field(
        min_length=1,
        max_length=150,
        examples=["Random Forest"],
    )

    framework: str = Field(
        min_length=1,
        max_length=100,
        examples=["scikit-learn"],
    )

    metrics: dict[str, Any] = Field(
        default_factory=dict,
        examples=[
            {
                "accuracy": 0.89,
                "precision": 0.86,
                "recall": 0.81,
                "f1": 0.83,
            }
        ],
    )

    artifact_uri: str | None = Field(
        default=None,
        max_length=500,
        examples=["artifacts/churn-model-v1.joblib"],
    )

    status: str = Field(
        default="registered",
        min_length=1,
        max_length=50,
    )

    training_date: datetime | None = None


class ModelVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    version: str
    algorithm: str
    framework: str
    metrics: dict[str, Any]
    artifact_uri: str | None
    status: str
    training_date: datetime | None
    created_at: datetime
    updated_at: datetime


class ModelVersionListResponse(BaseModel):
    total: int
    models: list[ModelVersionResponse]
