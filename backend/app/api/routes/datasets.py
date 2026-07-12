from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.repositories.dataset import DatasetRepository
from app.repositories.project import ProjectRepository
from app.schemas.dataset import (
    DatasetListResponse,
    DatasetProfileResponse,
    DatasetResponse,
    DatasetType,
    DatasetUploadResponse,
)
from app.services.dataset import (
    DatasetAlreadyExistsError,
    DatasetNotFoundError,
    DatasetProjectNotFoundError,
    DatasetService,
    InvalidDatasetError,
)


router = APIRouter(tags=["Datasets"])

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_database_session),
]


def get_dataset_service(
    session: DatabaseSession,
) -> DatasetService:
    dataset_repository = DatasetRepository(session)
    project_repository = ProjectRepository(session)

    return DatasetService(
        dataset_repository=dataset_repository,
        project_repository=project_repository,
    )


DatasetServiceDependency = Annotated[
    DatasetService,
    Depends(get_dataset_service),
]


@router.post(
    "/projects/{project_id}/datasets",
    response_model=DatasetUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_dataset(
    project_id: int,
    service: DatasetServiceDependency,
    dataset_type: Annotated[DatasetType, Form()],
    version: Annotated[str, Form(min_length=1, max_length=50)],
    file: Annotated[UploadFile, File()],
) -> DatasetUploadResponse:
    try:
        dataset, profile = await service.upload_dataset(
            project_id=project_id,
            dataset_type=dataset_type,
            version=version,
            upload=file,
        )
    except DatasetProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except DatasetAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except InvalidDatasetError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    return DatasetUploadResponse(
        dataset=DatasetResponse.model_validate(dataset),
        profile=DatasetProfileResponse.model_validate(profile),
    )


@router.get(
    "/projects/{project_id}/datasets",
    response_model=DatasetListResponse,
)
async def list_datasets(
    project_id: int,
    service: DatasetServiceDependency,
) -> DatasetListResponse:
    try:
        datasets = await service.list_datasets(project_id)
    except DatasetProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return DatasetListResponse(
        total=len(datasets),
        datasets=[DatasetResponse.model_validate(dataset) for dataset in datasets],
    )


@router.get(
    "/datasets/{dataset_id}/profile",
    response_model=DatasetProfileResponse,
)
async def get_dataset_profile(
    dataset_id: int,
    service: DatasetServiceDependency,
) -> DatasetProfileResponse:
    try:
        profile = await service.get_dataset_profile(dataset_id)
    except DatasetNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return DatasetProfileResponse.model_validate(profile)
