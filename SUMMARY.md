# Engineering summary

Walkthrough: [DEMO.md](DEMO.md) · Repo: https://github.com/gitcheckout1/UrlAgent
 
## What is built
 
A URL shortener (create link, redirect, click stats) and a homemade orchestrator that walks a small SDLC graph — requirements through summary, with human gates on release and on ambiguous requirements. Packaged in Docker; URLs persist in SQLite under `./data/urls.db`.
 
## Plan
 
Start with in-memory store and FastAPI v1. Add orchestrator (graph, runner, gates, nodes, CLI). Prove three scenarios with operation logs. Brownfield patch for 24h expiry and POST rate limit. SQLite for persistence. Docker + GitHub Actions CI.
 
Not microservices. Not LangGraph / Temporal / CrewAI as the orchestrator.
 
## Artifacts
 
- `app/` — write, redirect, analytics packages
- `orchestrator/` — graph, runner, gates, policy, nodes, CLI
- `scenarios/` — greenfield, brownfield, ambiguous yaml
- `tests/` — 8 passing in Docker and CI (`test_app` + `test_orchestrator`)
- `docs/operations/` — `greenfield-demo1.md`, `brownfield-bf1.md`, `ambiuguos-amb1.md` (filename typo kept)
- `docs/screenshots/` — images embedded in [DEMO.md](DEMO.md)
- `.github/workflows/ci.yml` — compose + pytest on push
- `runs/<run-id>/` — local only (gitignored): state, trace, per-run SUMMARY metrics
 
## Risks I cared about
 
- Bad URL schemes (`javascript:`, etc.) → 400
- Open redirect → http/https only
- Expired links → 410, no click bump on expired GET
- Abuse on POST → 429 on 11th request in a minute (in-process limiter)
- Shipping without human OK → release gate, exit 2, `WAIT_RELEASE.json`
- Vague requirements → ambiguous stops at design, human writes `answers.json`
 
Validation: pytest, manual scenario runs, CI runs the same docker compose test path.
 
## Assumptions
 
- Same long URL can get a new short code each POST
- One Python process for v1
- Tests use memory store (`set_store` in fixture); Docker uses SQLite via `DATABASE_URL`
- Rate limit is global per process, not per client IP
- `impact.md` lists files before brownfield code changes — I only patched those six files in M6
 
## Limitations
 
- No login / SSO / API keys in v1
- No custom HITL UI — CLI `approve` and hand-written `answers.json`
- No dynamic re-plan when requirements change mid-run; ambiguous uses answers once
- No Redis, k8s, multi-region
- Rate limit resets when the process restarts
- Human time waiting at gates is not counted as MTTR (documented in SUMMARY metrics per run)
- Stats endpoint still returns 200 after expiry — redirect is 410; I left analytics out of the brownfield patch list
- Starlette deprecation warnings under pytest — ignored for v1
- Orchestrator test node runs `pytest tests/test_app.py`, not the orchestrator tests (avoids recursion in CI)
 
## What I'd do next
 
Optional web UI for approvals. Per-IP rate limit if auth shows up. Redis only if redirect becomes a real hot path. Maybe 410 on stats for expired links if product wants consistency.