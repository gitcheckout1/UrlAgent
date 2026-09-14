# Execution Log

Placeholder. Running record of orchestrator runs and milestone work: what was run, what came out
of it, and what was decided. Entries appended below as work happens.

## M0 - Before code ( 2026-09-13)
- Created UrlAgent folder Opened in Cursor on Mac
- Copilot P0 + Opus guardrails typed in Cursor chat. Not committing chat.
- No code yet.

## M1 - Scaffold ( 2026-09-13)
- Commands: git init, venv, pip install, pytest 01
- Result: no test / all OK
- Commit : 50385ec
- AI : CursoR scaffold; I fixed tasks.md milestones
- Errors: none

## M2a - v1 scope (2026-09-13)
- I typed v1-scope.md myself before app code.
- Commit: 260fc05
- Errors: None

## M2
- Commands: pytest tests/test_app.py -q -> 3 passed; 2 warnings; uvicorn + /docs smoke ok
- Manual: javascript:/ftp:/file: -> 400; browser redirect OK; stats clicks ok
- Commit: 31034c9
- AI: Cursor built app per v1-scope.  HttpUrl validated for 400 not 422. Singleton memory store.
- I re-ran pytest myself.  Cursor had run pip.tests in Agent - I own verify.
- Starlette TestClient depreciation - ignored for v1.

## M3: Orchestrator (2026-09-13)

- Commands: python -m orchestrator run scenarios/greenfield.yaml --run-id test1; python -m orchestrator approve --gate release --run-id test1; python -m orchestrator run scenarios/greenfield.yaml --run-id test1;pytest tests/test_orchestrator.py -q; pytest -q;
- Result: WATING_RELEASE / exit 2; WAIT_RELEASE.json prresent; approvals {} before approve; exit 0 after approve+resume. 1 orchestrator test, 4 total passed. 2 StarletteDeprecationWarning(OK).
- Commit : 02caaab
- AI: Cursor M3 parts 1-4; minimal YAML parser; no pyYAML.
- Errors: none
 
 ## M4 Orchestrator depth(2026-09-13)

 - Commands: python -m orchestrator run scenarios/greenfield.yaml --run-id test1 (exit 2, WAITING_RELEASE); approve --gate release --run-id test1; run again (exit 0); pytest -q; pytest tests/test_orchestrator.py -q; pytest tests/test_orchestrator.py -q -k rollback

- Result: greenfield HITL still works (2 → 0). SUMMARY.md has duration_s, success true, mttr_s N/A; summary_metrics in trace.jsonl (retry_count 0, rollback_count 0). pytest: 6 passed (2 Starlette warnings OK); orchestrator tests 3 passed; rollback test 1 passed.

- Commit: 54234ef
- AI: Cursor M4 — real pytest tests/test_app.py, snapshot/restore, 2 test attempts then STOPPED, metrics in SUMMARY + trace; cli.py STOPPED exit 1.
- Errors: none


## M5 — Three scenarios (2026-09-13)
- Commands: demo1, bf1, amb1 orchestrator runs (see docs/operations/)
- Result: demo1/bf1 exit 2→0 at release; amb1 exit 2→0 at answers, no release gate; impact.md on bf1
- Commit: 8e36c38
- AI: none — I ran scenarios and typed ops logs
- Errors: none

## M6 — Brownfield product (2026-09-13)
- Commands: pytest -q; pytest tests/test_app.py -q
- Result: 8 passed (2 Starlette warnings OK). New tests: test_expiry_behavior_brownfield, test_eleventh_post_returns_429. Six files only per runs/bf1/impact.md.
- Commit: bec55aa
- AI: Cursor M6 — ttl in store create(), 410 skips click, RateLimiter in write/api.py; stats still 200 after expiry (analytics out of scope).
- Errors: none


## M7 — SQLite (2026-09-13)
- Commands: pytest -q; DATABASE_URL=sqlite:///./data/urls.db uvicorn + create link + restart + redirect
- Result: 8 passed. Link survived restart (data/urls.db). Tests pin memory via set_store().
- Commit: b97c67e
- AI: Cursor M7 — sqlite_store.py, store.py factory, routers use get_store().
- Errors: none

## M8 — Docker (2026-09-14)
- Commands: docker compose up --build; curl localhost:8000/health; docker compose run --rm api pytest -q; 11× POST rate-limit curl
- Result: health ok. 8 passed in container (2 Starlette warnings OK). Manual 429 on 11th POST. Redirect 302 in logs.
- Commit: 4dcd5e9
- AI: Cursor M8 — Dockerfile, compose, /health, .dockerignore, README snippet.
- Errors: none

## M9 — CI (2026-09-14)
- Commands: git push .github/workflows/ci.yml; GitHub Actions tab
- Result: CI green on ubuntu-latest; docker compose build + pytest 8 passed
- Commit: 07dd440
- AI: Cursor ci.yml — checkout, compose build, compose run pytest
- Errors: PAT needed workflow scope on first push; fixed, push succeeded

## M10 — README, SUMMARY, DEMO (2026-09-14)
- Commands:Final `pytest -q` (8 passed); reviewed greenfield demo1 exit 2 → approve → exit 0
- Result:README.md, SUMMARY.md, DEMO.md; docs/architecture.md + docs/agent.md with diagram screenshots; `docs/screenshots/` (demo + architecture PNGs)
- Commit: c90826a
- AI:Cursor drafted DEMO/README; facts and screenshots verified manually
- Notes:DEMO walkthrough with 11 demo images + 5 architecture images; CI green on Actions