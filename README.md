#UrlAgent

## Docker

Build and start the API on http://localhost:8000 (health at `/health`, docs at `/docs`):

```bash
docker compose up --build
```

Run the test suite in the container:

```bash
docker compose run --rm api pytest -q
```

Orchestrator commands. `./runs` is mounted, so artifacts and state land on the host:

```bash
docker compose run --rm api python -m orchestrator run scenarios/greenfield.yaml --run-id demo1
docker compose run --rm api python -m orchestrator status --run-id demo1
# Release is a human gate: the run stops with exit 2 until you approve it.
docker compose run --rm api python -m orchestrator approve --gate release --run-id demo1
docker compose run --rm api python -m orchestrator run scenarios/greenfield.yaml --run-id demo1
```

`DATABASE_URL` comes from `.env.example` and points at `./data/urls.db`, which is a mounted
volume, so the SQLite database survives container restarts.
