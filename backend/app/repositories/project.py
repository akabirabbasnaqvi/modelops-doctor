from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.project import ProjectCreate


class ProjectRepository:
    """Perform database operations for projects."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, project_data: ProjectCreate) -> Project:
        project = Project(**project_data.model_dump())

        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)

        return project

    async def get_all(self):
        query = select(Project).order_by(Project.created_at.desc())
        result = await self.session.execute(query)

        return list(result.scalars().all())

    async def get_by_id(self, project_id: int) -> Project | None:
        return await self.session.get(Project, project_id)

    async def get_by_name(self, name: str) -> Project | None:
        query = select(Project).where(Project.name == name)
        result = await self.session.execute(query)

        return result.scalar_one_or_none()

    async def delete(self, project: Project) -> None:
        await self.session.delete(project)
        await self.session.commit()
