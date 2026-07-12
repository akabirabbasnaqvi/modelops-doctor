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
from app.repositories.model_version import ModelVersionRepository
from app.repositories.prediction import PredictionRepository
from app.repositories.project import ProjectRepository
from app.schemas.prediction import (
    PredictionBatchDetailResponse,
    PredictionBatchListResponse,
    PredictionBatchResponse,
    PredictionResponse,
)
from app.services.prediction import (
    InvalidPredictionLogError,
    ModelProjectMismatchError,
    PredictionBatchAlreadyExistsError,
    PredictionBatchNotFoundError,
    PredictionModelNotFoundError,
    PredictionProjectNotFoundError,
    PredictionService,
)


router = APIRouter(tags=["Prediction Logs"])

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_database_session),
]


def get_prediction_service(
    session: DatabaseSession,
) -> PredictionService:
    return PredictionService(
        prediction_repository=PredictionRepository(session),
        project_repository=ProjectRepository(session),
        model_repository=ModelVersionRepository(session),
    )


PredictionServiceDependency = Annotated[
    PredictionService,
    Depends(get_prediction_service),
]


@router.post(
    "/projects/{project_id}/prediction-batches",
    response_model=PredictionBatchResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_prediction_batch(
    project_id: int,
    service: PredictionServiceDependency,
    model_version_id: Annotated[int, Form(gt=0)],
    file: Annotated[UploadFile, File()],
) -> PredictionBatchResponse:
    try:
        batch = await service.upload_prediction_log(
            project_id=project_id,
            model_version_id=model_version_id,
            upload=file,
        )
    except (
        PredictionProjectNotFoundError,
        PredictionModelNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except PredictionBatchAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except (
        InvalidPredictionLogError,
        ModelProjectMismatchError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    return PredictionBatchResponse.model_validate(batch)


@router.get(
    "/projects/{project_id}/prediction-batches",
    response_model=PredictionBatchListResponse,
)
async def list_prediction_batches(
    project_id: int,
    service: PredictionServiceDependency,
) -> PredictionBatchListResponse:
    try:
        batches = await service.list_batches(project_id)
    except PredictionProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return PredictionBatchListResponse(
        total=len(batches),
        batches=[PredictionBatchResponse.model_validate(batch) for batch in batches],
    )


@router.get(
    "/prediction-batches/{batch_id}",
    response_model=PredictionBatchDetailResponse,
)
async def get_prediction_batch(
    batch_id: int,
    service: PredictionServiceDependency,
) -> PredictionBatchDetailResponse:
    try:
        batch, predictions = await service.get_batch_detail(batch_id)
    except PredictionBatchNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return PredictionBatchDetailResponse(
        batch=PredictionBatchResponse.model_validate(batch),
        predictions=[
            PredictionResponse.model_validate(prediction) for prediction in predictions
        ],
    )
