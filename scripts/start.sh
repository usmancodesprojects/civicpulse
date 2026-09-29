#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if [ ! -f "$ROOT/.env" ]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  echo "Created .env from .env.example (simulated provider; no API key required)."
fi
cd "$ROOT"
docker compose up --build -d
docker compose ps
echo "CivicPulse is starting at http://localhost:8080"

