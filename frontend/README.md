# FastAPI Project - Frontend

The frontend is built with [Vite](https://vitejs.dev/), [React](https://reactjs.org/), [TypeScript](https://www.typescriptlang.org/), [TanStack Query](https://tanstack.com/query), [TanStack Router](https://tanstack.com/router) and [Tailwind CSS](https://tailwindcss.com/).

## Requirements

- [Bun](https://bun.sh/) (recommended) or [Node.js](https://nodejs.org/)

## Quick Start

Backend infra (Postgres) needs to be up first — see [`../development.md`](../development.md).

```bash
bun install
bun run dev
```

Open http://localhost:5173/.

Check `package.json` for other scripts.

## Generate Client

### Automatically

* Activate the backend virtual environment.
* From the top level project directory, run the script:

```bash
bash ./scripts/generate-client.sh
```

* Commit the changes.

### Manually

* Start the Docker Compose stack.

* Download the OpenAPI JSON file from `http://localhost/api/v1/openapi.json` and copy it to a new file `openapi.json` at the root of the `frontend` directory.

* To generate the frontend client, run:

```bash
bun run generate-client
```

* Commit the changes.

Notice that everytime the backend changes (changing the OpenAPI schema), you should follow these steps again to update the frontend client.

## Using a Remote API

If you want to use a remote API, you can set the environment variable `VITE_API_URL` to the URL of the remote API. For example, you can set it in the `frontend/.env` file:

```env
VITE_API_URL=https://api.my-domain.example.com
```

Then, when you run the frontend, it will use that URL as the base URL for the API.

## Code Structure

The frontend code is structured as follows:

* `frontend/src` - The main frontend code.
* `frontend/src/assets` - Static assets.
* `frontend/src/client` - The generated OpenAPI client.
* `frontend/src/components` -  The different components of the frontend.
* `frontend/src/hooks` - Custom hooks.
* `frontend/src/routes` - The different routes of the frontend which include the pages.

## End-to-End Testing with Playwright

The Playwright suite runs natively against the dev infra (`compose.dev.yml` provides Postgres + Mailpit) and a backend started via `uv run fastapi run`. Playwright auto-starts the frontend via the `webServer` block in `playwright.config.ts`.

### Run locally

Boot the dev infra and the backend (with SMTP pointing at Mailpit):

```bash
# from project root
bash scripts/dev-setup.sh

# in another terminal — backend with SMTP wired to Mailpit
cd backend
SMTP_HOST=localhost SMTP_PORT=1025 SMTP_TLS=False EMAILS_FROM_EMAIL=dev@example.com \
  uv run fastapi run app/main.py --port 8000
```

Then run the tests:

```bash
cd frontend
MAILPIT_HOST=http://localhost:8025 bunx playwright test           # all tests
MAILPIT_HOST=http://localhost:8025 bunx playwright test --ui      # interactive
```

### CI

`.github/workflows/playwright.yml` runs the suite on every push to `main` and on PRs touching `backend/`, `frontend/`, `.env`, or the workflow itself. Matrix shards 1–4 in parallel; reports are merged into a single HTML artifact.
