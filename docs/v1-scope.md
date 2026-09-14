# v1 scope

## In
- POST /v1/urls - create short code for http or https URL
- GET /{code} - 302 redirect, clicks go up
- GET /v1/urls/{code}/stats - clicks and last_clicked_at
- Reject non-http(s) schemes with 400 ( e.g. javascript:, ftp:, file:)
- Validate URL shape with Pydantic HttpUrl ( or equivalent) - must parse as http(s) URL
- Short codes: 7 random chars ( server-generated, not user input)

## Out
- Auth, custom aliases, Redis, Kubernetes, multi-region
- User-chosen short codes
- "Enterprise-ready" without asking what it means( ambiguous scenario handles that)

## Assumptions
- Same long URL can get a new code each POST
- one python process - write, redirect, analytics are package not separate servers
- v1 store in-memory then SQLite in M7
- No explicit max URL length in v1 beyond what HttpUrl / DB column allows (document if we hit limits)

## Risks
- Open redirect - only allow http/https scheme
- In-memory loss on restrt until SQLite
- Very long URLs - acceptable for demo; production would cap length ( e.g.2048)

## Security ( v1)
- URL allowlist: http and https only
- We do not fetch or preview user URLs server-side ( no SSRF surface)
- No auth in v1; rate limit ( M6) is abuse protection only

## Brownfield (added M6)
- Links expire 24h -> 410 on redirect
- 10 POSTS per minute -> 429 on 11th
