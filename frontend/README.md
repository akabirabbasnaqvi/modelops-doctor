# ModelOps Doctor frontend

React and TypeScript dashboard for the ModelOps Doctor API. See the
[root README](../README.md) for PostgreSQL, Redis, API, and Docker setup.

## Install and run

Use Node.js 22.12 or newer on a supported even-numbered release. CI and
Docker use Node 22; `.nvmrc` selects the same major version.

From this directory:

```bash
npm ci
npm run dev
```

Open <http://localhost:5173>. The default API URL is
`http://127.0.0.1:8000/api/v1`. Set `VITE_API_URL` in `.env.local` before
starting Vite or building if your backend uses a different address.
Vite variables are public build-time configuration; keep secrets out of them.

## Run the CI checks

```bash
npm audit --omit=dev --audit-level=high
npm run lint
npm run format:check
npm run typecheck
npm run test:coverage
npm run build
```

`npm test` runs Vitest once without coverage. `npm run test:watch` watches
tests during development. `npm run test:coverage` enforces 70% on lines,
statements, branches, and functions; auto-update is disabled so thresholds
cannot change silently. Reports are written to `coverage/`.

Tests cover API request contracts, forms, page loading/error states,
navigation, logging, and dashboard components. The chart tests use real
Recharts rendering with fixed dimensions because jsdom has no layout engine.

## Dependencies

`dependencies` contains browser runtime libraries. Testing, linting, types,
formatting, and build tools are in `devDependencies`. Commit changes to
`package.json` and `package-lock.json` together for normal dependency updates.
Use `npm ci` for reproducible installs from the lockfile.

Dependabot checks `/frontend` weekly through the repository's root
`.github/dependabot.yml`. Review `npm outdated` and `npm audit` when updating.
CI rejects high/critical runtime advisories; there are no accepted exceptions.
Development dependencies can also be audited with `npm audit`.
