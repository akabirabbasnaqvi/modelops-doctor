from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.repositories.automation_job import AutomationJobRepository
from app.repositories.project import ProjectRepository
from app.schemas.automation_job import (
    AutomationJobListResponse,
    AutomationJobResponse,
    BackgroundHealthCheckRequest,
)
from app.services.automation_job import (
    AutomationJobNotFoundError,
    AutomationJobService,
    AutomationProjectNotFoundError,
)


router = APIRouter(tags=["Automation Jobs"])

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_database_session),
]


def get_automation_job_service(
    session: DatabaseSession,
) -> AutomationJobService:
    return AutomationJobService(
        job_repository=AutomationJobRepository(session),
        project_repository=ProjectRepository(session),
    )


AutomationJobServiceDependency = Annotated[
    AutomationJobService,
    Depends(get_automation_job_service),
]


@router.post(
    "/projects/{project_id}/health-checks/background",
    response_model=AutomationJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def queue_background_health_check(
    project_id: int,
    request: BackgroundHealthCheckRequest,
    service: AutomationJobServiceDependency,
) -> AutomationJobResponse:
    try:
        job = await service.create_health_check_job(
            project_id=project_id,
            request=request,
        )
    except AutomationProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return AutomationJobResponse.model_validate(job)


@router.get(
    "/jobs",
    response_model=AutomationJobListResponse,
)
async def list_automation_jobs(
    service: AutomationJobServiceDependency,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> AutomationJobListResponse:
    jobs = await service.list_jobs(limit=limit)

    return AutomationJobListResponse(
        total=len(jobs),
        jobs=[AutomationJobResponse.model_validate(job) for job in jobs],
    )


@router.get(
    "/jobs/{job_id}",
    response_model=AutomationJobResponse,
)
async def get_automation_job(
    job_id: int,
    service: AutomationJobServiceDependency,
) -> AutomationJobResponse:
    try:
        job = await service.get_job(job_id)
    except AutomationJobNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return AutomationJobResponse.model_validate(job)
