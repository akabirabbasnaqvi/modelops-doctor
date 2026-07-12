from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.health_check import DiagnosisReport, HealthCheck
from app.models.prediction import Prediction, PredictionBatch


class HealthCheckRepository:
    """Perform database operations for health checks."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_prediction_batch(
        self,
        batch_id: int,
    ) -> PredictionBatch | None:
        return await self.session.get(PredictionBatch, batch_id)

    async def get_predictions(
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

    async def create_health_check(
        self,
        health_data: dict[str, Any],
        diagnosis_data: dict[str, Any],
    ) -> tuple[HealthCheck, DiagnosisReport]:
        health_check = HealthCheck(**health_data)

        self.session.add(health_check)
        await self.session.flush()

        diagnosis_report = DiagnosisReport(
            health_check_id=health_check.id,
            **diagnosis_data,
        )

        self.session.add(diagnosis_report)
        await self.session.commit()

        await self.session.refresh(health_check)
        await self.session.refresh(diagnosis_report)

        return health_check, diagnosis_report

    async def get_by_id(
        self,
        health_check_id: int,
    ) -> HealthCheck | None:
        return await self.session.get(
            HealthCheck,
            health_check_id,
        )

    async def get_latest_by_project(
        self,
        project_id: int,
    ) -> HealthCheck | None:
        query = (
            select(HealthCheck)
            .where(HealthCheck.project_id == project_id)
            .order_by(HealthCheck.created_at.desc())
            .limit(1)
        )

        result = await self.session.execute(query)

        return result.scalar_one_or_none()

    async def get_report(
        self,
        health_check_id: int,
    ) -> DiagnosisReport | None:
        query = select(DiagnosisReport).where(
            DiagnosisReport.health_check_id == health_check_id
        )

        result = await self.session.execute(query)

        return result.scalar_one_or_none()
