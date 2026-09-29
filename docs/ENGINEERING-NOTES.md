# Engineering notes

These answers refer to the submitted code, not generic platform behavior. Re-check line numbers after any edit with `rg -n`.

## 1. Laptop versus CI runner

First, a laptop may have any Python or Node version; the backend and frontend Dockerfiles freeze Python 3.12.14 and Node 22.13.1 at `backend/Dockerfile:1` and `frontend/Dockerfile:1`. Second, developer networks and hostnames differ; `frontend/nginx.conf:18` fixes in-container routing to Compose/Kubernetes DNS name `backend`, while the browser uses a relative path. Third, local state survives but CI is blank; `compose.yaml:74-85` mounts Redis AOF on `redisdata`, and `backend/app/seed.py` derives stable UUID5 identifiers so repeated startup does not duplicate the 32 examples.

## 2. CI/CD maturity ladder

The intended CI/CD pipeline is continuous delivery: PRs are designed to be linted, typed, unit-tested, image-built, scanned, manifest-validated, and integration-tested; a merge to main is designed to build immutable images and deploy them to an ephemeral Kubernetes environment. A successful integrated run remains outstanding while the dependent branches are unmerged. Publishing is gated at `.github/workflows/cd.yml:32` and deployment at `.github/workflows/cd.yml:60`. It is not continuous deployment to a long-lived production environment because the target is deliberately ephemeral. The next rung is an environment promotion/GitOps controller, which would make reviewed Git desired state continuously reconciled and auditable.

## 3. Build once, deploy many

`frontend/src/api/client.ts:30-43` uses only relative `/api` paths, and `frontend/nginx.conf:17-18` resolves the backend at runtime. No `import.meta.env` hostname is compiled into JavaScript. Without this, a staging URL baked by Vite would remain in the production bundle and require rebuilding the same source for every environment.

## 4. Correctness for a probabilistic provider

Correctness means the result always satisfies the closed category/priority enum, confidence range, one-line 140-character summary, timeout policy, and safe failure behavior - not that two calls produce identical prose. `backend/app/domain.py:46-58` enforces the schema. CI selects `simulated` in `.github/workflows/ci.yml:32`; the fallback and injection tests use deterministic providers in `backend/tests/test_triage_service.py`. A live model can vary while the system contract cannot.

## 5. HPA lag

The measured load test began at `2026-09-28T15:51:49.4402121+05:00`, and the first replica increase from 2 to 6 was observed at `2026-09-28T15:52:46.9839812+05:00`, giving an HPA scaling lag of 57.54 seconds. The deployment then reached its configured maximum of 10 replicas while the load continued. This lag includes metrics-server sampling, HPA reconciliation, scheduling, container startup, and readiness; the later scale-down steps reflect the HPA stabilization window. The recorded observations and chart are in `docs/evidence/hpa-scaling.csv` and `docs/evidence/hpa-scaling.png`.

## 6. Why VPA is Off

`k8s/base/vpa.yaml:12` sets recommendation-only mode. During the measured local kind run, the VPA reported a Target and Lower Bound of 25m CPU and 250Mi memory for the backend; its short-lived Upper Bound was 79211m CPU and 674251924 bytes, so the upper value was not treated as a stable sizing recommendation. CPU HPA calculates usage divided by requested CPU. If VPA automatically changes that request, utilization changes and can cause the HPA and VPA to work against one another, so the VPA remains in `Off` mode and its output is used only as reviewed sizing evidence. The captured recommendation is in `docs/evidence/vpa.txt`.

## 7. The `internal: true` outbound trade-off

The backend joins both networks at `compose.yaml:54`, while PostgreSQL, Redis, and Ollama join only `internal`; `compose.yaml:115` makes that second network internal. The backend therefore reaches the hosted LLM through `edge` but is the sole bridge to data services. Frontend compromise does not provide a route to PostgreSQL. Ollama needs no internet during inference; its model is pulled deliberately and persisted before an offline demo.

## 8. The failure diary

During the zero-downtime rehearsal, the first three-minute client run completed with 88 failures out of 88 requests. The initial belief was that the rolling-update strategy had interrupted service, but `curl.exe http://127.0.0.1:8080/ready` failed before any rollout was attempted, which showed that the local port-forward was absent. After the port-forward was restored, `kubectl get pods -n civicpulse` exposed a second problem: the new backend pod was in `ImagePullBackOff` because `civicpulse-backend:rollout-test` had not been loaded into the kind node. Loading that image and separating the client and rollout output files corrected both issues; the repeated test completed 1,212 requests with zero failures and the rollout succeeded, as recorded in `docs/evidence/zero-downtime.txt`.

This was a genuine operational failure but did not last more than one hour. It therefore does not yet satisfy any rubric item that explicitly requires a greater-than-one-hour incident; the team must not misstate its duration.

## Index and volume decisions

`ix_complaints_status_priority` in `backend/app/models.py:21` serves the operations queue filtered by status and priority. `ix_complaints_created_at` at line 22 serves newest-first pagination. Redis AOF is mounted because rate-limit counters and cached triage results are operationally useful across a routine container restart; correctness does not depend on them, but preserving them prevents a restart from briefly resetting abuse protection or causing an inference burst. PostgreSQL data is durable business state. Ollama weights persist to avoid another roughly 800 MB model pull.

## Build measurements

Record actual values from the final machine; do not invent them. Use `docker images civicpulse-*`, `docker build --progress=plain`, and compare the full directory size with the tar stream selected by each `.dockerignore`. The acceptance check is that the final frontend image contains nginx static assets only - no Node binary, source, or `node_modules` - and remains below roughly 60 MB.

