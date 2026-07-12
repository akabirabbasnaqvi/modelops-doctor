from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.repositories.dataset import DatasetRepository
from app.repositories.health_check import HealthCheckRepository
from app.repositories.model_version import ModelVersionRepository
from app.repositories.project import ProjectRepository
from app.schemas.health_check import (
    DiagnosisReportResponse,
    HealthCheckResponse,
    HealthCheckRunRequest,
    HealthCheckRunResponse,
)
from app.services.health_check import (
    HealthCheckRelationshipError,
    HealthCheckResourceNotFoundError,
    HealthCheckService,
    InvalidHealthCheckDataError,
)


router = APIRouter(tags=["Model Health"])

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_database_session),
]


def get_health_check_service(
    session: DatabaseSession,
) -> HealthCheckService:
    return HealthCheckService(
        health_repository=HealthCheckRepository(session),
        project_repository=ProjectRepository(session),
        model_repository=ModelVersionRepository(session),
        dataset_repository=DatasetRepository(session),
    )


HealthCheckServiceDependency = Annotated[
    HealthCheckService,
    Depends(get_health_check_service),
]


@router.post(
    "/projects/{project_id}/health-checks/run",
    response_model=HealthCheckRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_health_check(
    project_id: int,
    request: HealthCheckRunRequest,
    service: HealthCheckServiceDependency,
) -> HealthCheckRunResponse:
    try:
        health_check, report = await service.run_health_check(
            project_id=project_id,
            request=request,
        )
    except HealthCheckResourceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except (
        HealthCheckRelationshipError,
        InvalidHealthCheckDataError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    return HealthCheckRunResponse(
        health_check=HealthCheckResponse.model_validate(health_check),
        diagnosis_report=DiagnosisReportResponse.model_validate(report),
    )


@router.get(
    "/projects/{project_id}/health-checks/latest",
    response_model=HealthCheckResponse,
)
async def get_latest_health_check(
    project_id: int,
    service: HealthCheckServiceDependency,
) -> HealthCheckResponse:
    try:
        health_check = await service.get_latest_health_check(project_id)
    except HealthCheckResourceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return HealthCheckResponse.model_validate(health_check)


@router.get(
    "/health-checks/{health_check_id}/report",
    response_model=DiagnosisReportResponse,
)
async def get_health_check_report(
    health_check_id: int,
    service: HealthCheckServiceDependency,
) -> DiagnosisReportResponse:
    try:
        report = await service.get_diagnosis_report(health_check_id)
    except HealthCheckResourceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return DiagnosisReportResponse.model_validate(report)
