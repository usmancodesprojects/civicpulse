# ADR 0004: Minimize data sent to hosted models

## Status

Accepted with an operator-controlled offline option.

## Decision

The hosted provider sends only complaint text and location. Reporter contact is never included in the prompt or logs. Complaint text can still contain names, phone numbers, or addresses, so deployments handling sensitive data must select `ollama` to keep input on the machine. For the classroom Groq path, the team must use synthetic demo complaints and disclose the provider in the UI and privacy notice.

## Consequences

Data minimization reduces exposure but cannot reliably remove PII embedded in free text. The offline provider trades speed and classification quality for stronger locality. API keys stay in environment variables, Kubernetes Secrets, and GitHub Secrets, and never enter logs.

