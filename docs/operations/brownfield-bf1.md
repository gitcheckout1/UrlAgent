# Operation: brownfield / bf1

Requirement: 24h expiry, 10 POST/min rate limit.

## Commands I ran
python -m orchestrator run scenarios/brownfield.yaml --run-id bf1
python -m orchestrator approve --gate release --run-id bf1
python -m orchestrator run scenarios/brownfield.yaml --run-id bf1

## Results
| Step | Exit | Notes |
|------|------|-------|
| First run | 2 | runs/bf1/impact.md exists |
| After approve + resume | 0 | summary DONE |

## Human action
I read impact.md before trusting product code changes. Product 410/429 is M6.

## Trace lines I saw
{"ts": "2026-09-14T02:07:28.239524+00:00", "event": "run_started", "node": null, "actor": "runner", "run_id": "bf1"}
{"ts": "2026-09-14T02:07:28.240677+00:00", "event": "node_started", "node": "impact", "actor": "runner", "run_id": "bf1"}
{"ts": "2026-09-14T02:07:28.240812+00:00", "event": "node_completed", "node": "impact", "actor": "runner", "run_id": "bf1"}
{"ts": "2026-09-14T02:07:28.601562+00:00", "event": "waiting_release", "node": "release", "actor": "runner", "run_id": "bf1"}
{"ts": "2026-09-14T02:16:05.942662+00:00", "event": "gate_approved", "node": "release", "actor": "human", "run_id": "bf1"}
{"ts": "2026-09-14T02:16:06.020131+00:00", "event": "summary_metrics", "node": "summary", "actor": "runner", "run_id": "bf1", "duration_s": 517.704, "retry_count": 0, "rollback_count": 0, "success": true, "mttr_s": null}