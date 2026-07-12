from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.automation_job import AutomationJob


class AutomationJobRepository:
    """Perform database operations for automation jobs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        project_id: int,
        job_type: str,
        payload: dict[str, Any],
    ) -> AutomationJob:
        job = AutomationJob(
            project_id=project_id,
            job_type=job_type,
            status="queued",
            payload=payload,
            result={},
        )

        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)

        return job

    async def get_by_id(
        self,
        job_id: int,
    ) -> AutomationJob | None:
        return await self.session.get(AutomationJob, job_id)

    async def get_all(
        self,
        limit: int = 100,
    ):
        query = (
            select(AutomationJob).order_by(AutomationJob.created_at.desc()).limit(limit)
        )

        result = await self.session.execute(query)

        return list(result.scalars().all())

    async def get_recent_by_project(
        self,
        project_id: int,
        limit: int = 5,
    ):
        query = (
            select(AutomationJob)
            .where(AutomationJob.project_id == project_id)
            .order_by(AutomationJob.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(query)

        return list(result.scalars().all())

    async def set_celery_task_id(
        self,
        job: AutomationJob,
        task_id: str,
    ) -> AutomationJob:
        job.celery_task_id = task_id

        await self.session.commit()
        await self.session.refresh(job)

        return job

    async def mark_running(
        self,
        job: AutomationJob,
    ) -> AutomationJob:
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        job.error_message = None

        await self.session.commit()
        await self.session.refresh(job)

        return job

    async def mark_completed(
        self,
        job: AutomationJob,
        result_data: dict[str, Any],
    ) -> AutomationJob:
        job.status = "completed"
        job.result = result_data
        job.finished_at = datetime.now(timezone.utc)
        job.error_message = None

        await self.session.commit()
        await self.session.refresh(job)

        return job

    async def mark_failed(
        self,
        job: AutomationJob,
        error_message: str,
    ) -> AutomationJob:
        job.status = "failed"
        job.error_message = error_message
        job.finished_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(job)

        return job
