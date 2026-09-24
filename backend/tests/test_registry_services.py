"""Business-rule tests for ProjectService and ModelVersionService.

These cover the duplicate-detection and not-found branches that guard
project creation and model-version registration, using in-memory fake
repositories so no database is required.
"""

import asyncio
from types import SimpleNamespace

import pytest

from app.schemas.model_version import ModelVersionCreate
from app.schemas.project import ProjectCreate
from app.services.model_version import (
    ModelVersionAlreadyExistsError,
    ModelVersionNotFoundError,
    ModelVersionService,
    ParentProjectNotFoundError,
)
from app.services.project import (
    ProjectAlreadyExistsError,
    ProjectNotFoundError,
    ProjectService,
)


def run(coroutine):
    """Execute a coroutine from a synchronous test."""

    return asyncio.run(coroutine)


def make_project_payload(name: str = "Customer Churn Monitoring") -> ProjectCreate:
    return ProjectCreate(
        name=name,
        problem_type="binary_classification",
        target_column="churn",
    )


def make_model_payload(
    name: str = "Customer Churn Classifier",
    version: str = "1.0.0",
) -> ModelVersionCreate:
    return ModelVersionCreate(
        name=name,
        version=version,
        algorithm="Random Forest",
        framework="scikit-learn",
    )


class FakeProjectRepository:
    def __init__(self, existing_by_name=None, existing_by_id=None) -> None:
        self.existing_by_name = existing_by_name
        self.existing_by_id = existing_by_id
        self.created_payload = None
        self.deleted = None

    async def get_by_name(self, name: str):
        return self.existing_by_name

    async def get_by_id(self, project_id: int):
        return self.existing_by_id

    async def get_all(self):
        return [self.existing_by_id] if self.existing_by_id else []

    async def create(self, project_data):
        self.created_payload = project_data

        return SimpleNamespace(id=1, name=project_data.name)

    async def delete(self, project) -> None:
        self.deleted = project


class FakeModelRepository:
    def __init__(self, existing_by_identity=None, existing_by_id=None) -> None:
        self.existing_by_identity = existing_by_identity
        self.existing_by_id = existing_by_id
        self.created_args = None
        self.deleted = None

    async def get_by_identity(self, project_id: int, name: str, version: str):
        return self.existing_by_identity

    async def get_by_id(self, model_id: int):
        return self.existing_by_id

    async def get_by_project(self, project_id: int):
        return []

    async def create(self, project_id: int, model_data):
        self.created_args = (project_id, model_data)

        return SimpleNamespace(
            id=1,
            project_id=project_id,
            name=model_data.name,
            version=model_data.version,
        )

    async def delete(self, model_version) -> None:
        self.deleted = model_version


class TestProjectService:
    def test_new_project_is_created(self):
        repository = FakeProjectRepository()
        service = ProjectService(repository)

        project = run(service.create_project(make_project_payload()))

        assert project.name == "Customer Churn Monitoring"
        assert repository.created_payload is not None

    def test_duplicate_project_name_is_rejected(self):
        repository = FakeProjectRepository(
            existing_by_name=SimpleNamespace(id=1),
        )
        service = ProjectService(repository)

        with pytest.raises(ProjectAlreadyExistsError, match="already exists"):
            run(service.create_project(make_project_payload()))

        assert repository.created_payload is None

    def test_missing_project_lookup_is_rejected(self):
        service = ProjectService(FakeProjectRepository())

        with pytest.raises(ProjectNotFoundError, match="404"):
            run(service.get_project(project_id=404))

    def test_existing_project_is_returned(self):
        existing = SimpleNamespace(id=7, name="Existing")
        service = ProjectService(FakeProjectRepository(existing_by_id=existing))

        assert run(service.get_project(project_id=7)) is existing

    def test_list_projects_returns_repository_results(self):
        existing = SimpleNamespace(id=7, name="Existing")
        service = ProjectService(FakeProjectRepository(existing_by_id=existing))

        assert run(service.list_projects()) == [existing]

    def test_delete_requires_existing_project(self):
        service = ProjectService(FakeProjectRepository())

        with pytest.raises(ProjectNotFoundError):
            run(service.delete_project(project_id=404))

    def test_delete_removes_existing_project(self):
        existing = SimpleNamespace(id=7, name="Existing")
        repository = FakeProjectRepository(existing_by_id=existing)
        service = ProjectService(repository)

        run(service.delete_project(project_id=7))

        assert repository.deleted is existing


class TestModelVersionService:
    def build(self, project=None, existing_by_identity=None, existing_by_id=None):
        model_repository = FakeModelRepository(
            existing_by_identity=existing_by_identity,
            existing_by_id=existing_by_id,
        )

        service = ModelVersionService(
            model_repository=model_repository,
            project_repository=FakeProjectRepository(existing_by_id=project),
        )

        return service, model_repository

    def test_model_is_registered_against_existing_project(self):
        service, repository = self.build(project=SimpleNamespace(id=1))

        model = run(
            service.register_model(
                project_id=1,
                model_data=make_model_payload(),
            )
        )

        assert model.project_id == 1
        assert model.version == "1.0.0"
        assert repository.created_args[0] == 1

    def test_registration_requires_existing_project(self):
        service, _ = self.build(project=None)

        with pytest.raises(ParentProjectNotFoundError):
            run(
                service.register_model(
                    project_id=404,
                    model_data=make_model_payload(),
                )
            )

    def test_duplicate_name_and_version_is_rejected(self):
        service, repository = self.build(
            project=SimpleNamespace(id=1),
            existing_by_identity=SimpleNamespace(id=9),
        )

        with pytest.raises(ModelVersionAlreadyExistsError, match="already exists"):
            run(
                service.register_model(
                    project_id=1,
                    model_data=make_model_payload(),
                )
            )

        assert repository.created_args is None

    def test_same_name_with_new_version_is_allowed(self):
        service, _ = self.build(project=SimpleNamespace(id=1))

        model = run(
            service.register_model(
                project_id=1,
                model_data=make_model_payload(version="2.0.0"),
            )
        )

        assert model.version == "2.0.0"

    def test_listing_requires_existing_project(self):
        service, _ = self.build(project=None)

        with pytest.raises(ParentProjectNotFoundError):
            run(service.list_models(project_id=404))

    def test_missing_model_lookup_is_rejected(self):
        service, _ = self.build(project=SimpleNamespace(id=1))

        with pytest.raises(ModelVersionNotFoundError, match="404"):
            run(service.get_model(model_id=404))

    def test_delete_requires_existing_model(self):
        service, _ = self.build(project=SimpleNamespace(id=1))

        with pytest.raises(ModelVersionNotFoundError):
            run(service.delete_model(model_id=404))

    def test_delete_removes_existing_model(self):
        existing = SimpleNamespace(id=5, project_id=1)
        service, repository = self.build(
            project=SimpleNamespace(id=1),
            existing_by_id=existing,
        )

        run(service.delete_model(model_id=5))

        assert repository.deleted is existing
