from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HealthCheckRunRequest(BaseModel):
    model_version_id: int = Field(gt=0)
    baseline_dataset_id: int = Field(gt=0)
    prediction_batch_id: int = Field(gt=0)


class HealthCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    model_version_id: int
    baseline_dataset_id: int
    prediction_batch_id: int
    status: str
    health_score: float
    metrics: dict[str, Any]
    drift: dict[str, Any]
    component_scores: dict[str, Any]
    missing_rate: float
    created_at: datetime


class DiagnosisReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    health_check_id: int
    summary: str
    risk_level: str
    retraining_recommended: bool
    findings: list[dict[str, Any]]
    recommendations: list[str]
    created_at: datetime


class HealthCheckRunResponse(BaseModel):
    health_check: HealthCheckResponse
    diagnosis_report: DiagnosisReportResponse
