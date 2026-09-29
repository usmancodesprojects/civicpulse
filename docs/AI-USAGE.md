# AI usage disclosure

OpenAI Codex assisted with the initial CivicPulse application, tests, Docker and Kubernetes files, CI workflows, and documentation. The team is responsible for reviewing, testing, and explaining the submitted work.

## Verified work to date

- Nafay reviewed the backend provider and triage service, reproduced three failure cases, and added fixes for fallback caching, empty LLM choices, and trusted proxy client identity in PR #5. Ruff, mypy, and 29 backend tests passed locally after the fixes, with 82.72% coverage.
- Nafay reviewed the Docker/Compose configuration in PR #4, corrected proxy trust configuration, and verified two distinct rate-limit buckets through the nginx-backed Compose stack.
- Nafay reviewed PR #6, reproduced a deployment smoke-check false positive, added an explicit failure assertion, and wired the submission checker into CI. A temporary combined branch passed all seven CI jobs in PR #13. PR #6 itself remains red because its dependent frontend, documentation, and Kubernetes branches are still outside `dev`.
- Nafay added frontend PR #8 and Kubernetes draft PR #10. Eight frontend component tests and both Kustomize overlay renders passed locally. Live Kubernetes rollout and scaling evidence for PR #10 remains to be verified.

## Outstanding verification

Before submission, rerun the full CI pipeline on the integrated `dev` branch, verify the live Kubernetes deployment and scaling behavior, obtain the required partner reviews, and capture final PR and merge evidence. This file should be updated with those results only after they occur.
