# Operation: ambiguous / amb1

Requirement: "Make it enterprise-ready."

## Commands I ran
python -m orchestrator run scenarios/ambiguous.yaml --run-id amb1
(wrote runs/amb1/answers.json myself)
python -m orchestrator approve --gate answers --run-id amb1
python -m orchestrator run scenarios/ambiguous.yaml --run-id amb1

## Results
| Step | Exit | Notes |
|------|------|-------|
| First run | 2 | WAIT_ANSWERS.json |
| After answers + approve + resume | 0 | short graph — no release gate |

## answers.json I wrote
persist: memory, auth: none, reliable: tests_and_validation_not_multi_region

## Human action
I wrote answers.json myself — did not guess SSO, k8s, or multi-region.

## Trace lines I saw
{"ts": "2026-09-14T02:07:37.955794+00:00", "event": "run_started", "node": null, "actor": "runner", "run_id": "amb1"}
{"ts": "2026-09-14T02:07:37.956649+00:00", "event": "waiting_answers", "node": "design", "actor": "runner", "run_id": "amb1"}
{"ts": "2026-09-14T02:11:33.996344+00:00", "event": "gate_approved", "node": "answers", "actor": "human", "run_id": "amb1"}
{"ts": "2026-09-14T02:11:44.967235+00:00", "event": "node_completed", "node": "design", "actor": "runner", "run_id": "amb1"}
{"ts": "2026-09-14T02:11:44.967499+00:00", "event": "summary_metrics", "node": "summary", "actor": "runner", "run_id": "amb1", "duration_s": 236.041, "retry_count": 0, "rollback_count": 0, "success": true, "mttr_s": null}