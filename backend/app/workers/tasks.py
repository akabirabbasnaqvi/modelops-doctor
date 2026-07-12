import asyncio
from typing import Any

from app.db.session import AsyncSessionLocal, engine
from app.repositories.automation_job import AutomationJobRepository
from app.repositories.dataset import DatasetRepository
from app.repositories.health_check import HealthCheckRepository
from app.repositories.model_version import ModelVersionRepository
from app.repositories.project import ProjectRepository
from app.schemas.health_check import HealthCheckRunRequest
from app.services.health_check import HealthCheckService
from app.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    name="app.workers.tasks.run_health_check_task",
    autoretry_for=(ConnectionError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_health_check_task(
    self,
    job_id: int,
) -> dict[str, Any]:
    """Run one model-health check in a Celery worker."""

    return asyncio.run(_run_health_check_job_with_cleanup(job_id))


async def _run_health_check_job_with_cleanup(
    job_id: int,
) -> dict[str, Any]:
    try:
        return await _run_health_check_job(job_id)
    finally:
        await engine.dispose()


async def _run_health_check_job(
    job_id: int,
) -> dict[str, Any]:
    async with AsyncSessionLocal() as session:
        job_repository = AutomationJobRepository(session)
        job = await job_repository.get_by_id(job_id)

        if job is None:
            raise ValueError(f"Automation job with ID {job_id} was not found.")

        await job_repository.mark_running(job)

        try:
            payload = job.payload

            health_service = HealthCheckService(
                health_repository=HealthCheckRepository(session),
                project_repository=ProjectRepository(session),
                model_repository=ModelVersionRepository(session),
                dataset_repository=DatasetRepository(session),
            )

            request = HealthCheckRunRequest(
                model_version_id=int(payload["model_version_id"]),
                baseline_dataset_id=int(payload["baseline_dataset_id"]),
                prediction_batch_id=int(payload["prediction_batch_id"]),
            )

            health_check, diagnosis_report = await health_service.run_health_check(
                project_id=int(job.project_id),
                request=request,
            )

            result_data = {
                "health_check_id": health_check.id,
                "diagnosis_report_id": diagnosis_report.id,
                "health_score": health_check.health_score,
                "status": health_check.status,
                "risk_level": diagnosis_report.risk_level,
                "retraining_recommended": (diagnosis_report.retraining_recommended),
            }

            await job_repository.mark_completed(
                job,
                result_data=result_data,
            )

            return result_data

        except Exception as error:
            await session.rollback()

            job = await job_repository.get_by_id(job_id)

            if job is not None:
                await job_repository.mark_failed(
                    job,
                    error_message=str(error),
                )

            raise


@celery_app.task(name="app.workers.tasks.dispatch_scheduled_health_checks")
def dispatch_scheduled_health_checks() -> dict[str, Any]:
    """Scheduled placeholder for project monitoring policies."""

    return {
        "status": "completed",
        "message": (
            "Scheduled dispatcher ran successfully. "
            "No automatic monitoring policy is configured yet."
        ),
    }
