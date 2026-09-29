# ADR 0001: Replaceable triage providers

## Status

Accepted.

## Decision

All classifiers implement the `TriageProvider` protocol in `backend/app/providers/triage/base.py`. The factory selects Groq-compatible LLM, Ollama, rules, or deterministic simulation from `TRIAGE_PROVIDER`. `TriageService` owns retry, validation, content-hash caching, outcome history, and fallback; callers do not know which provider ran.

## Consequences

CI uses `simulated`, production can use `llm`, and an operator can recover from provider failure by changing configuration rather than application code. The abstraction adds a small amount of indirection but makes failure testing deterministic.

