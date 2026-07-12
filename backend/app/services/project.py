from app.models.project import Project
from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectCreate


class ProjectAlreadyExistsError(Exception):
    """Raised when a project with the same name already exists."""


class ProjectNotFoundError(Exception):
    """Raised when the requested project does not exist."""


class ProjectService:
    """Apply business rules for project management."""

    def __init__(self, repository: ProjectRepository) -> None:
        self.repository = repository

    async def create_project(
        self,
        project_data: ProjectCreate,
    ) -> Project:
        existing_project = await self.repository.get_by_name(project_data.name)

        if existing_project is not None:
            raise ProjectAlreadyExistsError(
                f"A project named '{project_data.name}' already exists."
            )

        return await self.repository.create(project_data)

    async def list_projects(self):
        return await self.repository.get_all()

    async def get_project(self, project_id: int) -> Project:
        project = await self.repository.get_by_id(project_id)

        if project is None:
            raise ProjectNotFoundError(f"Project with ID {project_id} was not found.")

        return project

    async def delete_project(self, project_id: int) -> None:
        project = await self.get_project(project_id)
        await self.repository.delete(project)
