# CivicPulse runbook

## Local deploy

1. Install Docker Desktop and ensure `docker compose version` succeeds.
2. Run `scripts/start.ps1` on Windows or `scripts/start.sh` on macOS/Linux.
3. Wait for `docker compose ps` to report all required services healthy.
4. Verify `curl http://localhost:8080/health`, then `/ready`, then open the dashboard.

Inspect logs as JSON with `docker compose logs -f backend`. Every request has an `X-Request-ID`; search the same value in logs to follow one request. Inspect a service with `docker compose ps`, `docker compose exec postgres pg_isready -U civicpulse`, and `docker compose exec redis redis-cli ping`.

## Kubernetes deploy

The CI workflow is the production reference. It creates a kind cluster, installs metrics-server and VPA, loads images tagged with the immutable commit SHA, creates the Secret from GitHub Secrets, runs `kubectl apply -k k8s/overlays/prod`, waits for both rollouts, and smoke-tests the frontend Service.

Useful checks:

```bash
kubectl get pods,svc,ingress,hpa,pdb -n civicpulse
kubectl rollout status deployment/backend -n civicpulse
kubectl logs -n civicpulse deployment/backend --all-pods=true --tail=200
kubectl describe pod -n civicpulse -l app=backend
kubectl get events -n civicpulse --sort-by=.lastTimestamp
```

## Rollback

For the 3 a.m. fast recovery, undo the last rollout:

```bash
kubectl rollout undo deployment/backend -n civicpulse
kubectl rollout status deployment/backend -n civicpulse
```

After stabilizing, restore auditable desired state by checking out the last known-good commit, setting the overlay image to that commit SHA, and reapplying it:

```bash
cd k8s/overlays/prod
kustomize edit set image ghcr.io/your-github-user/civicpulse-backend=ghcr.io/OWNER/civicpulse-backend:KNOWN_GOOD_SHA
kubectl apply -k .
```

Use the imperative undo for speed. Use the declarative reapply to make the cluster match reviewed repository history.

## Triage failure procedure

1. Inspect `/api/meta/providers`; confirm latency and fallback flags.
2. Search backend warnings for `triage_fallback`, `provider`, and `error_class` - never print the API key.
3. Check provider quota/status and the Kubernetes Secret name, not its value: `kubectl describe secret civicpulse-secrets -n civicpulse`.
4. Switch to `rules` for deterministic emergency operation or `ollama` for offline classification, apply the ConfigMap, and restart the backend.
5. Submit a known complaint and confirm a 201 plus the expected `triaged_by` field.
6. After recovery, restore the provider and write an incident note with request IDs and timestamps.

## Persistence demonstrations

Compose: submit a unique complaint, record its ID, run `docker compose down` followed by `docker compose up -d`, and GET the same ID. Do not add `-v`.

Kubernetes: record a complaint ID, run `kubectl delete pod postgres-0 -n civicpulse`, wait for the StatefulSet, and GET the same ID. The `volumeClaimTemplates` PVC must remain.

## Network isolation demonstration

The nginx image intentionally lacks ping, so use name resolution as the portable proof:

```bash
docker compose exec frontend wget -qO- http://postgres:5432
```

It must fail because frontend is only on `edge`. Then show that backend resolves its dependencies with `/ready`. Capture the failed command and explanation in the demo video.

## HPA/VPA evidence

1. Confirm metrics-server: `kubectl top pods -n civicpulse`.
2. Record guessed requests from `k8s/base/backend.yaml` (200m CPU, 256Mi memory).
3. Start `kubectl get hpa backend-hpa -n civicpulse -w | tee docs/evidence/hpa-watch.txt`.
4. Run `k6 run -e BASE_URL=http://civicpulse.local load/k6-script.js`.
5. Record the first load-rise timestamp and first replica-rise timestamp. The difference is the measured HPA lag; do not estimate it.
6. Run `kubectl describe vpa backend-vpa -n civicpulse > docs/evidence/vpa.txt` and record Target, Lower Bound, and Upper Bound.
7. Create `docs/evidence/hpa-scaling.csv` with `seconds,replicas,offered_rps`; run `python scripts/plot_scaling.py`.
8. Update resource requests from the observed recommendation, repeat the load test, and document the changed utilization/scale-out behavior.

VPA remains in `Off` mode because an automatic VPA changing CPU requests changes the denominator used by CPU HPA. Running both controllers on the same signal can make them fight.

## Zero-downtime rollout

Run a continuous `hey` or k6 load, change only the backend image to another immutable SHA, and run `kubectl set image deployment/backend backend=IMAGE:SHA -n civicpulse`. Save client totals showing zero failed requests plus rollout output. The rolling strategy, readiness probe, `preStop`, and 40-second grace period are designed for this demonstration.

## Evidence checklist

Capture real evidence only: GitHub branch protection, five linked reviewed PRs, red blocked/green fixed pipeline, conflict markers and resolution, Compose persistence, failed frontend-to-database access, image sizes, build-context sizes, HPA watch, VPA recommendation, scaling chart, zero-downtime totals, rollback output, and both partners speaking in the <=5 minute demo.

