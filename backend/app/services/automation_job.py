from app.repositories.automation_job import AutomationJobRepository
from app.repositories.project import ProjectRepository
from app.schemas.automation_job import BackgroundHealthCheckRequest


class AutomationJobNotFoundError(Exception):
    """Raised when an automation job cannot be found."""


class AutomationProjectNotFoundError(Exception):
    """Raised when the selected project cannot be found."""


class AutomationJobService:
    """Create and retrieve background automation jobs."""

    def __init__(
        self,
        job_repository: AutomationJobRepository,
        project_repository: ProjectRepository,
    ) -> None:
        self.job_repository = job_repository
        self.project_repository = project_repository

    async def create_health_check_job(
        self,
        project_id: int,
        request: BackgroundHealthCheckRequest,
    ):
        project = await self.project_repository.get_by_id(project_id)

        if project is None:
            raise AutomationProjectNotFoundError(
                f"Project with ID {project_id} was not found."
            )

        payload = request.model_dump()

        job = await self.job_repository.create(
            project_id=project_id,
            job_type="model_health_check",
            payload=payload,
        )

        from app.workers.tasks import run_health_check_task

        try:
            task_result = run_health_check_task.delay(job.id)

            return await self.job_repository.set_celery_task_id(
                job=job,
                task_id=task_result.id,
            )
        except Exception as error:
            await self.job_repository.mark_failed(
                job,
                f"Failed to queue Celery task: {error}",
            )
            raise

    async def list_jobs(
        self,
        limit: int,
    ):
        return await self.job_repository.get_all(limit=limit)

    async def get_job(
        self,
        job_id: int,
    ):
        job = await self.job_repository.get_by_id(job_id)

        if job is None:
            raise AutomationJobNotFoundError(
                f"Automation job with ID {job_id} was not found."
            )

        return job
