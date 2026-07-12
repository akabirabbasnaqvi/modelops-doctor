from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.repositories.automation_job import AutomationJobRepository
from app.repositories.project import ProjectRepository
from app.schemas.dashboard import ProjectDashboardResponse
from app.services.dashboard import (
    DashboardProjectNotFoundError,
    DashboardService,
)


router = APIRouter(tags=["Dashboard"])

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_database_session),
]


def get_dashboard_service(
    session: DatabaseSession,
) -> DashboardService:
    return DashboardService(
        session=session,
        project_repository=ProjectRepository(session),
        job_repository=AutomationJobRepository(session),
    )


DashboardServiceDependency = Annotated[
    DashboardService,
    Depends(get_dashboard_service),
]


@router.get(
    "/projects/{project_id}/dashboard",
    response_model=ProjectDashboardResponse,
)
async def get_project_dashboard(
    project_id: int,
    service: DashboardServiceDependency,
) -> ProjectDashboardResponse:
    try:
        return await service.get_project_dashboard(project_id)
    except DashboardProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
