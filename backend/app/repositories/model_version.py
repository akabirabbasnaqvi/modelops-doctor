from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_version import ModelVersion
from app.schemas.model_version import ModelVersionCreate


class ModelVersionRepository:
    """Perform database operations for model versions."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        project_id: int,
        model_data: ModelVersionCreate,
    ) -> ModelVersion:
        model_version = ModelVersion(
            project_id=project_id,
            **model_data.model_dump(),
        )

        self.session.add(model_version)
        await self.session.commit()
        await self.session.refresh(model_version)

        return model_version

    async def get_by_id(
        self,
        model_id: int,
    ) -> ModelVersion | None:
        return await self.session.get(ModelVersion, model_id)

    async def get_by_identity(
        self,
        project_id: int,
        name: str,
        version: str,
    ) -> ModelVersion | None:
        query = select(ModelVersion).where(
            ModelVersion.project_id == project_id,
            ModelVersion.name == name,
            ModelVersion.version == version,
        )

        result = await self.session.execute(query)

        return result.scalar_one_or_none()

    async def get_by_project(
        self,
        project_id: int,
    ):
        query = (
            select(ModelVersion)
            .where(ModelVersion.project_id == project_id)
            .order_by(ModelVersion.created_at.desc())
        )

        result = await self.session.execute(query)

        return list(result.scalars().all())

    async def delete(
        self,
        model_version: ModelVersion,
    ) -> None:
        await self.session.delete(model_version)
        await self.session.commit()
