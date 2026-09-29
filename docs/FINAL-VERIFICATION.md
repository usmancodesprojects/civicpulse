# Final verification record

Run these checks from the integrated commit before creating the final `dev` to `main` pull request. Record failures honestly and rerun them after each fix.

## Backend

```powershell
cd backend
python -m pytest
```

Verified on 2026-09-29: 29 tests passed and total coverage was 82.72%, above the configured 65% threshold. The only output outside the pass summary was an upstream AnyIO deprecation warning from Starlette's test client.

## Frontend

```powershell
cd frontend
npm run lint
npm run typecheck
npm test -- --run
npm run build
```

Verified on 2026-09-29: ESLint and TypeScript completed without errors, all 8 Vitest tests passed, statement coverage was 85.71%, and the Vite production build succeeded.

## Deployment definitions

```powershell
docker compose config --quiet
docker compose -f compose.yaml -f compose.prod.yaml config --quiet
kubectl kustomize k8s/overlays/dev | Out-Null
kubectl kustomize k8s/overlays/prod | Out-Null
```

Verified on 2026-09-29: both Compose configurations parsed successfully and both Kubernetes overlays rendered successfully. Environment-variable warnings are expected when `.env` is intentionally absent during syntax-only validation; live deployment must supply those values through the documented runtime secret workflow.
