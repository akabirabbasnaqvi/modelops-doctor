from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ProblemType = Literal[
    "binary_classification",
    "multiclass_classification",
]


class ProjectCreate(BaseModel):
    name: str = Field(
        min_length=3,
        max_length=150,
        examples=["Customer Churn Monitoring"],
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
    )
    problem_type: ProblemType
    target_column: str = Field(
        min_length=1,
        max_length=100,
        examples=["churn"],
    )
    positive_class: str | None = Field(
        default=None,
        max_length=100,
        examples=["1"],
    )
    metric_priority: str = Field(
        default="f1",
        min_length=1,
        max_length=50,
        examples=["f1"],
    )
    owner: str | None = Field(
        default=None,
        max_length=150,
        examples=["Akabir Abbas"],
    )


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    problem_type: str
    target_column: str
    positive_class: str | None
    metric_priority: str
    owner: str | None
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    total: int
    projects: list[ProjectResponse]
