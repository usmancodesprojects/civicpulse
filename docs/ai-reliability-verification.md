# AI triage reliability verification

Issue: #14. This branch builds on the provider abstraction already present in `dev`.

## Behavior

- Groq and Ollama use one strict JSON result parser and one classification schema prompt. Ollama HTTP 429 is retryable.
- Transient provider failures retry up to `TRIAGE_RETRY_ATTEMPTS` (default 2) with bounded exponential jitter; malformed output is not retried.
- After `TRIAGE_CIRCUIT_FAILURES` failed triage calls (default 3) within `TRIAGE_CIRCUIT_WINDOW_SECONDS` (default 60), a Redis key opens the circuit for `TRIAGE_CIRCUIT_COOLDOWN_SECONDS` (default 30). Calls during cooldown use the existing rules-based fallback. A successful primary call clears the failure counter.
- An invalid cached decision is discarded and recomputed. Only successful primary decisions are cached.

## Local checks

On 29 September 2026, a Python 3.12 container built from the CivicPulse backend image ran against this branch's mounted `backend` directory:

```sh
python -m ruff check app tests
python -m mypy app
python -m pytest -q
```

Results: Ruff clean; mypy clean across 31 source files; 37 tests passed with 84% total coverage (65% required). Tests use `fakeredis` and mocked provider HTTP responses. No live Groq or Ollama service was exercised.
