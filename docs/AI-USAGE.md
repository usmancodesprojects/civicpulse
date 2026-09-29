# AI usage disclosure

OpenAI Codex assisted both Usman and Nafay with implementation, debugging, tests, deployment configuration, CI workflows, documentation, and verification. Both team members reviewed the generated changes, ran the recorded checks, resolved failures, and remain responsible for understanding and explaining the submitted work.

## Usman's verified work

- Usman implemented the backend foundation and complaint API, including persistence, triage services, health endpoints, migrations, and automated tests in PR #5.
- Usman added the backend and frontend container images, development and production Compose definitions, startup helpers, and persistence evidence in PR #4.
- Usman implemented the CI/CD and release workflows in PR #6, including linting, typing, tests, coverage, manifest validation, image builds, integration checks, vulnerability scanning, and submission-readiness gates.
- Usman integrated and reviewed the feature branches, reviewed and approved Nafay's frontend, Kubernetes, documentation, and reliability changes, and merged the approved PRs through `dev` without committing directly to `main`.
- Usman normalized contributor identities with `.mailmap`, documented the deliberate `.gitignore` merge conflict and its resolution, expanded the submission checker, and recorded the final backend, frontend, Compose, and Kubernetes verification results.

## Nafay's verified work

- Nafay reviewed the backend provider and triage service, reproduced failure cases, and fixed fallback caching, empty LLM choices, and trusted proxy client identity in PR #5.
- Nafay reviewed the Docker/Compose configuration in PR #4, corrected proxy trust configuration, and verified distinct rate-limit buckets through the nginx-backed Compose stack.
- Nafay reviewed PR #6, fixed the deployment smoke-check false positive, wired the submission checker into CI, and verified the integrated workflow before approval.
- Nafay implemented and tested the frontend in PR #8, the Kubernetes deployment and autoscaling configuration in PR #10, and the repository documentation and captured evidence in PR #12.
- Nafay hardened AI triage reliability in PR #16 with shared structured-output validation, bounded retries, a Redis-backed circuit breaker, corrupt-cache recovery, and focused tests.

## Final verification

- The integrated backend suite passes 37 tests with 84.27% coverage; Ruff and mypy pass.
- Frontend linting, TypeScript checking, 12 component tests, coverage, and the production build pass.
- Docker Compose validation and both Kubernetes overlays pass, and the repository contains the captured persistence, rollout, HPA, VPA, rollback, and zero-downtime evidence.
- The final `dev` to `main` PR #15 received partner approval, passed all 14 GitHub checks, and merged into protected `main`.
