from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DashboardCounts(BaseModel):
    models: int
    datasets: int
    prediction_batches: int
    health_checks: int


class DashboardHealthSummary(BaseModel):
    health_check_id: int
    health_score: float
    status: str
    risk_level: str | None
    retraining_recommended: bool | None
    metrics: dict[str, Any]
    component_scores: dict[str, Any]
    drifted_features: list[str]
    recommendations: list[str]
    created_at: datetime


class ProjectDashboardResponse(BaseModel):
    project_id: int
    project_name: str
    counts: DashboardCounts
    latest_health: DashboardHealthSummary | None
    recent_jobs: list[dict[str, Any]]
