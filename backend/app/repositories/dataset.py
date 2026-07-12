from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset, DatasetProfile


class DatasetRepository:
    """Perform database operations for datasets and profiles."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        dataset_data: dict[str, Any],
        profile_data: dict[str, Any],
    ) -> tuple[Dataset, DatasetProfile]:
        dataset = Dataset(**dataset_data)

        self.session.add(dataset)
        await self.session.flush()

        profile = DatasetProfile(
            dataset_id=dataset.id,
            **profile_data,
        )

        self.session.add(profile)
        await self.session.commit()

        await self.session.refresh(dataset)
        await self.session.refresh(profile)

        return dataset, profile

    async def get_by_identity(
        self,
        project_id: int,
        dataset_type: str,
        version: str,
    ) -> Dataset | None:
        query = select(Dataset).where(
            Dataset.project_id == project_id,
            Dataset.dataset_type == dataset_type,
            Dataset.version == version,
        )

        result = await self.session.execute(query)

        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        dataset_id: int,
    ) -> Dataset | None:
        return await self.session.get(Dataset, dataset_id)

    async def get_by_project(
        self,
        project_id: int,
    ):
        query = (
            select(Dataset)
            .where(Dataset.project_id == project_id)
            .order_by(Dataset.created_at.desc())
        )

        result = await self.session.execute(query)

        return list(result.scalars().all())

    async def get_profile(
        self,
        dataset_id: int,
    ) -> DatasetProfile | None:
        query = select(DatasetProfile).where(DatasetProfile.dataset_id == dataset_id)

        result = await self.session.execute(query)

        return result.scalar_one_or_none()
