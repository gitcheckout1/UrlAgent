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

## M2b - 
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
