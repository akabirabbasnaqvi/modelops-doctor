from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import Prediction, PredictionBatch


class PredictionRepository:
    """Perform database operations for prediction batches."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_batch(
        self,
        batch_data: dict[str, Any],
        prediction_rows: list[dict[str, Any]],
    ) -> PredictionBatch:
        batch = PredictionBatch(**batch_data)

        self.session.add(batch)
        await self.session.flush()

        predictions = [
            Prediction(
                batch_id=batch.id,
                **prediction_data,
            )
            for prediction_data in prediction_rows
        ]

        self.session.add_all(predictions)
        await self.session.commit()
        await self.session.refresh(batch)

        return batch

    async def get_batch_by_id(
        self,
        batch_id: int,
    ) -> PredictionBatch | None:
        return await self.session.get(PredictionBatch, batch_id)

    async def get_batches_by_project(
        self,
        project_id: int,
    ):
        query = (
            select(PredictionBatch)
            .where(PredictionBatch.project_id == project_id)
            .order_by(PredictionBatch.uploaded_at.desc())
        )

        result = await self.session.execute(query)

        return list(result.scalars().all())

    async def get_predictions_by_batch(
        self,
        batch_id: int,
    ):
        query = (
            select(Prediction)
            .where(Prediction.batch_id == batch_id)
            .order_by(Prediction.id)
        )

        result = await self.session.execute(query)

        return list(result.scalars().all())

    async def get_by_content_hash(
        self,
        project_id: int,
        model_version_id: int,
        content_hash: str,
    ) -> PredictionBatch | None:
        query = select(PredictionBatch).where(
            PredictionBatch.project_id == project_id,
            PredictionBatch.model_version_id == model_version_id,
            PredictionBatch.content_hash == content_hash,
        )

        result = await self.session.execute(query)

        return result.scalar_one_or_none()
