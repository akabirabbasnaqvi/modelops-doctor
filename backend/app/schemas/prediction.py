from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class PredictionBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    model_version_id: int
    file_name: str
    file_path: str
    content_hash: str
    row_count: int
    is_labeled: bool
    status: str
    error_message: str | None
    uploaded_at: datetime


class PredictionBatchListResponse(BaseModel):
    total: int
    batches: list[PredictionBatchResponse]


class PredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    prediction_timestamp: datetime | None
    true_label: str | None
    predicted_label: str
    confidence: float | None
    features: dict[str, Any]
    created_at: datetime


class PredictionBatchDetailResponse(BaseModel):
    batch: PredictionBatchResponse
    predictions: list[PredictionResponse]
