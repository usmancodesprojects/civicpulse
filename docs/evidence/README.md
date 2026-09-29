# Required real-world evidence

Do not replace these with fabricated output. Capture them from the team's own GitHub repository and Kubernetes run:

- `branch-protection.png` - PR required, CI required, and at least one approval.
- `blocked-red.png` and `fixed-green.png` - one deliberately failing PR check, then the fixed check.
- `merge-conflict-before.png` and `merge-conflict-resolution.png` - real code conflict and selected resolution.
- `submit-result.png`, `dashboard.png`, and `stats-cache-hit.png` - the three required UI views.
- `network-isolation.txt` - frontend-to-PostgreSQL attempt failing while `/ready` succeeds.
- `compose-persistence.txt` and `postgres-pod-persistence.txt` - the same complaint readable after restart/deletion.
- `image-sizes.txt` and `build-context-sizes.txt` - measured, not estimated.
- `hpa-watch.txt`, `vpa.txt`, `hpa-scaling.csv`, and `hpa-scaling.png` - actual load-test observations.
- `zero-downtime.txt` and `rollback.txt` - client failure count, rollout, and both rollback mechanisms.

Most evidence files are ignored until you deliberately force-add the final captures, preventing accidental screenshots or logs from entering intermediate commits. Use `git add -f docs/evidence/<file>` after checking every capture for secrets.

