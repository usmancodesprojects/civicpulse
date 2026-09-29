# CivicPulse

[![CI](https://github.com/usmancodesprojects/civicpulse/actions/workflows/ci.yml/badge.svg)](https://github.com/usmancodesprojects/civicpulse/actions/workflows/ci.yml)
[![CD](https://github.com/usmancodesprojects/civicpulse/actions/workflows/cd.yml/badge.svg)](https://github.com/usmancodesprojects/civicpulse/actions/workflows/cd.yml)

CivicPulse turns free-text municipal complaints into an ordered, observable operations queue. It validates a report, classifies it behind a replaceable provider interface, persists it in PostgreSQL, caches and rate-limits with Redis, and presents the result in a React dashboard. Provider failures do not become citizen-facing failures: the system retries only retryable errors and falls back to deterministic rules.

## Architecture

```mermaid
flowchart LR
    Citizen[Citizen / operator] -->|HTTP :8080| UI[React + nginx]
    UI -->|relative /api| API[FastAPI backend]
    API -->|SQL| PG[(PostgreSQL 16)]
    API -->|cache + rate limit| Redis[(Redis 7 AOF)]
    API --> Triage{TriageProvider}
    Triage --> Groq[Hosted LLM]
    Triage --> Ollama[Ollama 1B]
    Triage --> Rules[Rules / simulated]
    subgraph edge network
      UI
      API
    end
    subgraph internal network
      PG
      Redis
      Ollama
    end
```

The frontend joins only `edge`; PostgreSQL, Redis, and Ollama join only the isolated `internal` network; the backend is the sole bridge. The backend can reach a hosted provider through the non-internal edge network without exposing data services to the frontend.

## Quickstart

Prerequisite: Docker Desktop with Compose v2 and at least 4 GB available to Docker.

On Windows PowerShell, from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

On macOS/Linux:

```bash
./scripts/start.sh
```

The script creates `.env` from the safe simulated-provider example, builds the images, runs Alembic, idempotently seeds 32 realistic complaints, and starts the five containers. Open [http://localhost:8080](http://localhost:8080). Check readiness with:

```powershell
curl.exe http://localhost:8080/ready
```

Stop without deleting data using `docker compose down`. Start again and the rows remain. Use `docker compose down -v` only when you deliberately want to delete the database, Redis AOF, and Ollama model volumes.

## Provider choices

The default `TRIAGE_PROVIDER=simulated` is deterministic and needs no key. Other values are `rules`, `ollama`, and `llm`. For Groq-compatible hosted inference, update only your uncommitted `.env`:

```dotenv
TRIAGE_PROVIDER=llm
LLM_API_KEY=your-real-key
```

For the offline path, use `TRIAGE_PROVIDER=ollama`, start the stack, then pull the model once into the persistent volume:

```powershell
docker compose exec ollama ollama pull llama3.2:1b
```

Never commit `.env`. Reporter contact is never sent to an LLM. See [ADR 0004](docs/adr/0004-pii-and-data-governance.md) before using real citizen data.

## API contract

| Method | Path | Result |
|---|---|---|
| POST | `/api/complaints` | Validate, rate-limit, triage, persist; 201 or field-level 400; 429 with `Retry-After` |
| GET | `/api/complaints/{id}` | One complaint; 404 when absent |
| GET | `/api/complaints` | Filters `category`, `priority`, `status`; pagination up to 100 |
| PATCH | `/api/complaints/{id}/status` | Server-owned transition table; invalid transition returns descriptive 409 |
| GET | `/api/stats` | Category and priority aggregates; `X-Cache: HIT\|MISS` |
| GET | `/api/meta/providers` | Active provider and last 20 triage outcomes |
| GET | `/health` | Liveness only; never touches dependencies |
| GET | `/ready` | 200 only when PostgreSQL and Redis respond |
| GET | `/metrics` | Prometheus request and triage metrics |
| GET | `/docs` | Interactive OpenAPI documentation |

## Development verification

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
ruff check app tests
mypy app
pytest
python ..\scripts\check_frontend_contract.py
```

Frontend:

```powershell
cd frontend
npm ci
npm run lint
npm run typecheck
npm test
npm run build
```

Repository lint:

```powershell
python scripts/check_submission.py
docker compose config --quiet
kubectl kustomize k8s/overlays/prod > rendered.yaml
```

## Kubernetes

Install `kind`, `kubectl`, metrics-server, and the Vertical Pod Autoscaler. Build and load the two local `:dev` images, create the runtime Secret without committing it, and apply the development overlay:

```powershell
kind create cluster --name civicpulse
docker build -t civicpulse-backend:dev .\backend
docker build -t civicpulse-frontend:dev .\frontend
kind load docker-image --name civicpulse civicpulse-backend:dev civicpulse-frontend:dev
kubectl apply -f .\k8s\base\namespace.yaml
kubectl create secret generic civicpulse-secrets -n civicpulse --from-literal=POSTGRES_PASSWORD=change-this --from-literal=DATABASE_URL=postgresql+psycopg://civicpulse:change-this@postgres:5432/civicpulse --from-literal=LLM_API_KEY=not-used
kubectl apply -k .\k8s\overlays\dev
kubectl rollout status deployment/backend -n civicpulse
kubectl port-forward service/frontend 8080:8080 -n civicpulse
```

The production overlay is intentionally non-runnable until CI replaces `REPLACE_OWNER`, `REPLACE_WITH_COMMIT_SHA`, and creates the real Secret. This prevents placeholder credentials or mutable tags from becoming an accidental deployment.

## Tests and operational documents

- [Runbook](docs/RUNBOOK.md): deployment, logs, incidents, and both rollback modes.
- [Engineering notes](docs/ENGINEERING-NOTES.md): required eight questions grounded in this repository.
- [Triage design](docs/TRIAGE.md): validation, retry, fallback, and caching.
- [AI disclosure](docs/AI-USAGE.md): required attribution and review checklist.
- [ADRs](docs/adr): provider boundary, frontend runtime routing, immutable deployment, and PII governance.

## Screenshots to add before submission

The repository cannot truthfully manufacture account-specific evidence. After pushing to GitHub and running a real cluster test, add these to `docs/evidence/`: branch protection, a red blocked merge followed by green checks, deliberate conflict resolution, dashboard and submit views, `kubectl get hpa -w`, VPA recommendations, a replicas-versus-load chart, zero-downtime rollout output, image sizes, and build-context measurements. The exact capture procedure is in the runbook.

![Complaint submission](docs/evidence/submit-result.png)
![Operations dashboard](docs/evidence/dashboard.png)
![Statistics cache state](docs/evidence/stats-cache-hit.png)

## License

MIT - see [LICENSE](LICENSE).

