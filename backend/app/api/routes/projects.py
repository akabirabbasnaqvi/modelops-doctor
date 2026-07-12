from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.repositories.project import ProjectRepository
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
)
from app.services.project import (
    ProjectAlreadyExistsError,
    ProjectNotFoundError,
    ProjectService,
)


router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_database_session),
]


def get_project_service(
    session: DatabaseSession,
) -> ProjectService:
    repository = ProjectRepository(session)
    return ProjectService(repository)


ProjectServiceDependency = Annotated[
    ProjectService,
    Depends(get_project_service),
]


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    project_data: ProjectCreate,
    service: ProjectServiceDependency,
) -> ProjectResponse:
    try:
        project = await service.create_project(project_data)
    except ProjectAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return ProjectResponse.model_validate(project)


@router.get(
    "",
    response_model=ProjectListResponse,
)
async def list_projects(
    service: ProjectServiceDependency,
) -> ProjectListResponse:
    projects = await service.list_projects()

    return ProjectListResponse(
        total=len(projects),
        projects=[ProjectResponse.model_validate(project) for project in projects],
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
async def get_project(
    project_id: int,
    service: ProjectServiceDependency,
) -> ProjectResponse:
    try:
        project = await service.get_project(project_id)
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return ProjectResponse.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    project_id: int,
    service: ProjectServiceDependency,
) -> Response:
    try:
        await service.delete_project(project_id)
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)
