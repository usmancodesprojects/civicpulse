# Triage behavior

The selected provider returns schema-constrained JSON. Every response is validated again by `TriageResult`; categories, priorities, summary length, confidence, and one-line summaries cannot escape the contract.

Timeouts are 10 seconds. Timeouts, HTTP 429, network failures, and upstream 5xx responses are retried once with jitter. Invalid output and 4xx requests are not retried. Any remaining failure invokes deterministic rules and persists `triaged_by=rules:fallback`.

Results are cached in Redis for 24 hours by SHA-256 of normalized complaint text and location. Provider outcome metadata stores only provider, latency, fallback flag, and timestamp - never complaint contents or credentials. Run `GET /api/meta/providers` to see the active provider and last 20 outcomes.

