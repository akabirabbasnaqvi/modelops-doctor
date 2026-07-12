from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


from app.models.dataset import Dataset
from app.models.health_check import DiagnosisReport, HealthCheck
from app.models.model_version import ModelVersion
from app.models.prediction import PredictionBatch
from app.repositories.automation_job import AutomationJobRepository
from app.repositories.project import ProjectRepository
from app.schemas.dashboard import (
    DashboardCounts,
    DashboardHealthSummary,
    ProjectDashboardResponse,
)


class DashboardProjectNotFoundError(Exception):
    """Raised when the dashboard project cannot be found."""


class DashboardService:
    """Build aggregated project-dashboard information."""

    def __init__(
        self,
        session: AsyncSession,
        project_repository: ProjectRepository,
        job_repository: AutomationJobRepository,
    ) -> None:
        self.session = session
        self.project_repository = project_repository
        self.job_repository = job_repository

    async def get_project_dashboard(
        self,
        project_id: int,
    ) -> ProjectDashboardResponse:
        project = await self.project_repository.get_by_id(project_id)

        if project is None:
            raise DashboardProjectNotFoundError(
                f"Project with ID {project_id} was not found."
            )

        counts = DashboardCounts(
            models=await self._count(
                ModelVersion,
                ModelVersion.project_id,
                project_id,
            ),
            datasets=await self._count(
                Dataset,
                Dataset.project_id,
                project_id,
            ),
            prediction_batches=await self._count(
                PredictionBatch,
                PredictionBatch.project_id,
                project_id,
            ),
            health_checks=await self._count(
                HealthCheck,
                HealthCheck.project_id,
                project_id,
            ),
        )

        latest_health = await self._get_latest_health(project_id)

        recent_jobs = await self.job_repository.get_recent_by_project(
            project_id=project_id,
            limit=5,
        )

        recent_job_data = [
            {
                "id": job.id,
                "job_type": job.job_type,
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "finished_at": (
                    job.finished_at.isoformat() if job.finished_at is not None else None
                ),
            }
            for job in recent_jobs
        ]

        return ProjectDashboardResponse(
            project_id=project.id,
            project_name=project.name,
            counts=counts,
            latest_health=latest_health,
            recent_jobs=recent_job_data,
        )

    async def _count(
        self,
        model,
        project_column,
        project_id: int,
    ) -> int:
        query = select(func.count(model.id)).where(project_column == project_id)

        result = await self.session.execute(query)

        return int(result.scalar_one())

    async def _get_latest_health(
        self,
        project_id: int,
    ) -> DashboardHealthSummary | None:
        query = (
            select(HealthCheck, DiagnosisReport)
            .outerjoin(
                DiagnosisReport,
                DiagnosisReport.health_check_id == HealthCheck.id,
            )
            .where(HealthCheck.project_id == project_id)
            .order_by(HealthCheck.created_at.desc())
            .limit(1)
        )

        result = await self.session.execute(query)
        row = result.first()

        if row is None:
            return None

        health_check, report = row

        drifted_features = health_check.drift.get(
            "drifted_features",
            [],
        )

        return DashboardHealthSummary(
            health_check_id=health_check.id,
            health_score=health_check.health_score,
            status=health_check.status,
            risk_level=(report.risk_level if report is not None else None),
            retraining_recommended=(
                report.retraining_recommended if report is not None else None
            ),
            metrics=health_check.metrics,
            component_scores=health_check.component_scores,
            drifted_features=drifted_features,
            recommendations=(report.recommendations if report is not None else []),
            created_at=health_check.created_at,
        )
