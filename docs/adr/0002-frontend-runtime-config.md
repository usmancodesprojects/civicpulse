# ADR 0002: Relative API paths through nginx

## Status

Accepted.

## Decision

The browser always calls relative `/api` paths. The frontend nginx configuration proxies those paths to the backend in Compose; Kubernetes Ingress routes `/api` directly to the backend Service. No API hostname is compiled by Vite.

## Consequences

One frontend image runs in local, CI, and production environments. The reverse proxy or Ingress becomes responsible for routing and same-origin policy, which also removes avoidable CORS configuration.

