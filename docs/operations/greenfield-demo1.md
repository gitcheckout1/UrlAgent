# Operation: greenfield / demo1

## Commands I ran
python -m orchestrator run scenarios/greenfield.yaml --run-id demo1
python -m orchestrator approve --gate release --run-id demo1
python -m orchestrator run scenarios/greenfield.yaml --run-id demo1

## Results
| Step | Exit | Notes |
|------|------|-------|
| First run | 2 | WAIT_RELEASE.json created |
| After approve + resume | 0 | summary DONE in state.json |

## Human action
I typed `approve --gate release`. Code never sets approvals.release alone.

## Trace lines I saw
{"ts": "2026-09-14T02:07:00.010862+00:00", "event": "run_started", "node": null, "actor": "runner", "run_id": "demo1"}
{"ts": "2026-09-14T02:07:00.402522+00:00", "event": "waiting_release", "node": "release", "actor": "runner", "run_id": "demo1"}
{"ts": "2026-09-14T02:07:10.839890+00:00", "event": "gate_approved", "node": "release", "actor": "human", "run_id": "demo1"}
{"ts": "2026-09-14T02:07:19.537057+00:00", "event": "run_started", "node": null, "actor": "runner", "run_id": "demo1"}
{"ts": "2026-09-14T02:07:19.538013+00:00", "event": "summary_metrics", "node": "summary", "actor": "runner", "run_id": "demo1", "duration_s": 10.83, "retry_count": 0, "rollback_count": 0, "success": true, "mttr_s": null}