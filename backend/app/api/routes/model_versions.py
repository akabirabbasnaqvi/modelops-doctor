from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.repositories.model_version import ModelVersionRepository
from app.repositories.project import ProjectRepository
from app.schemas.model_version import (
    ModelVersionCreate,
    ModelVersionListResponse,
    ModelVersionResponse,
)
from app.services.model_version import (
    ModelVersionAlreadyExistsError,
    ModelVersionNotFoundError,
    ModelVersionService,
    ParentProjectNotFoundError,
)


router = APIRouter(tags=["Model Registry"])

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_database_session),
]


def get_model_version_service(
    session: DatabaseSession,
) -> ModelVersionService:
    model_repository = ModelVersionRepository(session)
    project_repository = ProjectRepository(session)

    return ModelVersionService(
        model_repository=model_repository,
        project_repository=project_repository,
    )


ModelVersionServiceDependency = Annotated[
    ModelVersionService,
    Depends(get_model_version_service),
]


@router.post(
    "/projects/{project_id}/models",
    response_model=ModelVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_model_version(
    project_id: int,
    model_data: ModelVersionCreate,
    service: ModelVersionServiceDependency,
) -> ModelVersionResponse:
    try:
        model_version = await service.register_model(
            project_id,
            model_data,
        )
    except ParentProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ModelVersionAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return ModelVersionResponse.model_validate(model_version)


@router.get(
    "/projects/{project_id}/models",
    response_model=ModelVersionListResponse,
)
async def list_model_versions(
    project_id: int,
    service: ModelVersionServiceDependency,
) -> ModelVersionListResponse:
    try:
        model_versions = await service.list_models(project_id)
    except ParentProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return ModelVersionListResponse(
        total=len(model_versions),
        models=[
            ModelVersionResponse.model_validate(model_version)
            for model_version in model_versions
        ],
    )


@router.get(
    "/models/{model_id}",
    response_model=ModelVersionResponse,
)
async def get_model_version(
    model_id: int,
    service: ModelVersionServiceDependency,
) -> ModelVersionResponse:
    try:
        model_version = await service.get_model(model_id)
    except ModelVersionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return ModelVersionResponse.model_validate(model_version)


@router.delete(
    "/models/{model_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_model_version(
    model_id: int,
    service: ModelVersionServiceDependency,
) -> Response:
    try:
        await service.delete_model(model_id)
    except ModelVersionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)
