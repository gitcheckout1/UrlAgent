# Agent & HITL Model

## Cursor P0 rules
- only files I name.  No Redis/k8s/LangGraph unless I ask.
- Never set approvals.release in code.
- Ambiguous -> stop for human answers.

## Human vs agent (draft)
|Action | Agent | Me | 
|-------|-------|------|
|Draft code | yes | review diff |
|approve --gate release | no | yes |
|answers.json | no | yes |

## Gates (humans are not worker nodes)

| Gate | When | Human action |
|------|------|----------------|
| release | Before summary on greenfield/brownfield | `approve --gate release --run-id ID` |
| answers | Ambiguous, no answers.json | Write answers.json + `approve --gate answers` |

Runner writes WAIT_RELEASE.json or WAIT_ANSWERS.json and exits 2.

## Policy
safe_write allows: app/, tests/, docs/, scenarios/, runs/
Denies: .env, paths with ..

## Security
- http/https URLs only; reject javascript: etc.
- No server-side fetch of target URLs
- Secrets in env only; never log tokens or full URLs

