# Contributing to ModelOps Doctor

Thanks for taking an interest in the project. This guide covers how to get
the code running, what the checks expect, and how changes are shipped.

## Getting set up

Prerequisites: Python 3.11+, Node.js 20+, Docker (optional, for the full
stack).

Follow the Local Development section of [README.md](README.md). The short
version, from a fresh clone:

```bash
# Backend
python3.11 -m venv backend/.venv
source backend/.venv/bin/activate        # Windows: backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements-dev.txt
cp .env.example .env                     # Windows: Copy-Item .env.example .env

# Frontend
cd frontend
npm ci
```

Use `npm ci`, not `npm install`, so you get the exact versions in
`package-lock.json`.

## Running the checks

CI runs exactly these. Run them locally before opening a pull request.

Backend, from `backend/`:

```bash
python -m ruff check app tests alembic/env.py
python -m ruff format --check app tests alembic/env.py
python -m pytest
```

`pytest` fails below 70% coverage. The threshold lives in
`backend/pytest.ini`.

Frontend, from `frontend/`:

```bash
npm run lint
npm run format:check
npm run typecheck
npm run test
npm run build
```

`npm run test` fails below 70% coverage on lines, statements, branches and
functions. The thresholds live in `frontend/vitest.config.ts`.

Run `npm run format` to fix formatting, and `npm run test:watch` while
working on tests.

## How we commit

**Every behaviour change ships with the test that pins it, in the same
commit.** A fix and its regression test belong together; a reviewer should
be able to read one commit and see both the problem and the proof.

Keep commits small and single-purpose. Do not mix formatting, refactors and
behaviour changes in one commit — split them, even when that means three
commits touching the same file.

Order commits so each one is green on its own. If you are adding a CI gate,
land the code that satisfies it first, so the commit introducing the gate
passes its own build.

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat:     a new capability
fix:      a bug fix
test:     adding or correcting tests
refactor: behaviour-preserving restructuring
docs:     documentation only
build:    dependencies, Docker, packaging
ci:       workflows and automation
chore:    tooling and housekeeping
style:    formatting only, no behaviour change
```

Write the subject in the imperative and under ~72 characters. Use the body
to explain *why* the change is needed and what the previous behaviour was —
that context is what makes the history worth reading later.

```
fix: store is_labeled as a Python bool

dataframe.notna().any() returns numpy.bool_, so a numpy scalar was passed
into the batch record while the neighbouring row_count was cast with
int(). Wrap it in bool() and pin the behaviour with a test.
```

## Adding dependencies

Backend: add the direct dependency to `backend/requirements.txt` (runtime)
or `backend/requirements-dev.txt` (tests and tooling), pinned to an exact
version. Then regenerate the lockfile **on Linux**:

```bash
pip install pip-tools
pip-compile --output-file=backend/requirements.lock.txt backend/requirements.txt
```

This must not be done on Windows. `uvicorn[standard]` pulls `uvloop` and
`httptools`, which have no Windows wheels, so a lockfile resolved there
silently omits them and the Docker image degrades to the pure-Python event
loop. CI fails if the lockfile no longer satisfies `requirements.txt`.

Frontend: `npm install <pkg>` and commit the updated `package.json` **and**
`package-lock.json` together.

Dependabot opens grouped update PRs weekly for pip, npm and GitHub Actions.

## Line endings

`.gitattributes` forces LF everywhere. Do not override `core.autocrlf`
locally — mixed endings make every file look modified and turn small
commits into repo-wide diffs.

## Project layout

```
backend/app/api/          FastAPI routes
backend/app/services/     business rules
backend/app/repositories/ database access
backend/app/mlops/        drift, metrics, health scoring, diagnosis
backend/tests/            pytest suite
frontend/src/api/         typed HTTP clients
frontend/src/pages/       one component per route
frontend/src/hooks/       shared React hooks
frontend/src/styles.css   shared classes — prefer these to inline styles
```

Backend requests flow route → service → repository. Put business rules in
the service layer, not in routes.

On the frontend, reuse the classes in `src/styles.css` (`.panel`,
`.form-grid`, `.alert`, `.data-table`, `.primary-button`) rather than
writing inline style objects. Inline styles are for values that genuinely
vary at runtime, such as a progress bar's width.

Route API errors through `getErrorMessage()` in `src/api/errors.ts`.
FastAPI returns `detail` as a string for `HTTPException` but as an array of
objects for 422 validation errors; rendering that array directly crashes
React.

## Reporting bugs

Open an issue with what you expected, what happened, and the steps to
reproduce. Include the failing command and its output where relevant.
