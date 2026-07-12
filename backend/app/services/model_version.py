from app.models.model_version import ModelVersion
from app.repositories.model_version import ModelVersionRepository
from app.repositories.project import ProjectRepository
from app.schemas.model_version import ModelVersionCreate


class ModelVersionAlreadyExistsError(Exception):
    """Raised when the same model version already exists."""


class ModelVersionNotFoundError(Exception):
    """Raised when a model version cannot be found."""


class ParentProjectNotFoundError(Exception):
    """Raised when the parent project cannot be found."""


class ModelVersionService:
    """Apply business rules for model-version registration."""

    def __init__(
        self,
        model_repository: ModelVersionRepository,
        project_repository: ProjectRepository,
    ) -> None:
        self.model_repository = model_repository
        self.project_repository = project_repository

    async def register_model(
        self,
        project_id: int,
        model_data: ModelVersionCreate,
    ) -> ModelVersion:
        project = await self.project_repository.get_by_id(project_id)

        if project is None:
            raise ParentProjectNotFoundError(
                f"Project with ID {project_id} was not found."
            )

        existing_model = await self.model_repository.get_by_identity(
            project_id=project_id,
            name=model_data.name,
            version=model_data.version,
        )

        if existing_model is not None:
            raise ModelVersionAlreadyExistsError(
                f"Model '{model_data.name}' version "
                f"'{model_data.version}' already exists "
                f"in project {project_id}."
            )

        return await self.model_repository.create(
            project_id,
            model_data,
        )

    async def list_models(
        self,
        project_id: int,
    ):
        project = await self.project_repository.get_by_id(project_id)

        if project is None:
            raise ParentProjectNotFoundError(
                f"Project with ID {project_id} was not found."
            )

        return await self.model_repository.get_by_project(project_id)

    async def get_model(
        self,
        model_id: int,
    ) -> ModelVersion:
        model_version = await self.model_repository.get_by_id(model_id)

        if model_version is None:
            raise ModelVersionNotFoundError(
                f"Model version with ID {model_id} was not found."
            )

        return model_version

    async def delete_model(
        self,
        model_id: int,
    ) -> None:
        model_version = await self.get_model(model_id)
        await self.model_repository.delete(model_version)
