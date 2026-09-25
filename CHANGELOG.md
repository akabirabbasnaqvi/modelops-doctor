# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Prettier configuration and a `format:check` step in frontend CI.
- Coverage thresholds for the frontend suite, matching the backend's 70%
  floor.
- Vitest tests for `DashboardPage`, `JobsPage`, `DatasetsPage` and
  `PredictionBatchesPage`.
- `CONTRIBUTING.md` describing setup, the checks CI runs, and commit
  conventions.

### Changed

- `ProjectsPage`, `DashboardPage`, `StatCard`, `HealthGauge` and
  `RecentJobsTable` now use the shared classes in `styles.css` instead of
  duplicated inline style objects.

### Fixed

- Failures loading projects and model versions now surface the backend's
  error detail instead of a generic message that discarded it.

## [0.1.0] - 2026-09-25

First tagged release. A full-stack MLOps monitoring platform with drift
detection, model-health scoring, diagnosis reports and background
automation.

### Added

- FastAPI backend with route → service → repository layering over
  PostgreSQL, covering projects, model versions, datasets, prediction logs,
  health checks and automation jobs.
- Drift detection, classification metrics, weighted health scoring and
  diagnosis reports in `app/mlops/`.
- Celery worker and beat for background and scheduled health checks.
- React and TypeScript dashboard with seven routes.
- Docker Compose orchestration for the full stack.
- MLflow-tracked example training run and DVC-versioned sample datasets.
- `Backend CI`: Ruff, Alembic migrations, pytest at a 70% coverage floor,
  pip-audit over the lockfile, and a compose smoke test that boots the
  whole stack and checks its health endpoints.
- `Frontend CI`: ESLint, `tsc` type checking, Vitest with coverage, and a
  production build.
- Weekly Dependabot updates for pip, npm and GitHub Actions.
- `backend/requirements.lock.txt` pinning all 54 transitive dependencies,
  resolved for Linux to match Docker and CI.

### Fixed

- `backend/requirements.txt` was UTF-16 encoded and could not be parsed by
  pip, so installs failed on any machine following the README. It was also
  a full `pip freeze` including the Windows-only `pywin32`.
- FastAPI 422 responses return `detail` as an array of objects. Five pages
  rendered that value directly, which threw
  "Objects are not valid as a React child" and blanked the page.
- `is_labeled` was stored as a `numpy.bool_` rather than a Python `bool`.
- Line endings are normalised to LF via `.gitattributes`. Windows edits had
  been committing CRLF against an LF history, making every tracked file
  appear modified.

[Unreleased]: https://github.com/akabirabbasnaqvi/modelops-doctor/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/akabirabbasnaqvi/modelops-doctor/releases/tag/v0.1.0
