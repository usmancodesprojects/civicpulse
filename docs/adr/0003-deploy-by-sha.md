# ADR 0003: Deploy immutable commit-SHA image tags

## Status

Accepted.

## Decision

The CD workflow pushes convenience `latest` tags but deploys only `${{ github.sha }}`. Kustomize updates both image references to that immutable source revision before apply.

## Consequences

The running revision maps directly to `git show <sha>`, and rollback can reapply a known prior SHA. A mutable tag is never used as desired cluster state.

