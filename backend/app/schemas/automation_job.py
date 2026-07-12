from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BackgroundHealthCheckRequest(BaseModel):
    model_version_id: int = Field(gt=0)
    baseline_dataset_id: int = Field(gt=0)
    prediction_batch_id: int = Field(gt=0)


class AutomationJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int | None
    job_type: str
    status: str
    celery_task_id: str | None
    payload: dict[str, Any]
    result: dict[str, Any]
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class AutomationJobListResponse(BaseModel):
    total: int
    jobs: list[AutomationJobResponse]
