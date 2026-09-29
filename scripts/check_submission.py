from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md", ".env.example", "compose.yaml", "compose.prod.yaml",
    "backend/Dockerfile", "frontend/Dockerfile", "backend/alembic/versions/0001_initial.py",
    "k8s/base/backend.yaml", "k8s/base/postgres.yaml", "k8s/base/hpa.yaml", "k8s/base/vpa.yaml",
    ".github/workflows/ci.yml", ".github/workflows/cd.yml", ".github/workflows/release.yml",
    "docs/ENGINEERING-NOTES.md", "docs/RUNBOOK.md", "docs/AI-USAGE.md",
    ".mailmap", "docs/evidence/README.md", "docs/evidence/merge-conflict.md",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    failures.append(message)


failures: list[str] = []
for relative in REQUIRED:
    if not (ROOT / relative).is_file():
        fail(f"missing {relative}")

tracked_text = "\n".join(
    path.read_text(encoding="utf-8", errors="ignore")
    for path in ROOT.rglob("*")
    if path.is_file()
    and not {".git", ".venv", "node_modules", "dist", "coverage"}.intersection(path.parts)
    and path.suffix not in {".png", ".lock"}
)
for pattern, label in [
    (r"(?i)(api[_-]?key|token|password)\s*[=:]\s*['\"]?[A-Za-z0-9_-]{24,}", "possible committed secret"),
    (r"image:\s+[^\s:]+:latest", "latest image deployed"),
    (r"image:\s+postgres\s*$", "unversioned postgres image"),
    (r"image:\s+redis\s*$", "unversioned redis image"),
]:
    if re.search(pattern, tracked_text, re.MULTILINE):
        fail(label)

prod_path = ROOT / "compose.prod.yaml"
if prod_path.is_file():
    prod = prod_path.read_text(encoding="utf-8")
    if "build:" in prod:
        fail("compose.prod.yaml contains build:")
    if re.search(r"(?:postgres|redis):[\s\S]{0,500}?ports:", prod):
        fail("production database/cache may publish a port")

compose_path = ROOT / "compose.yaml"
if compose_path.is_file() and "internal: true" not in compose_path.read_text(encoding="utf-8"):
    fail("internal Docker network is not isolated")

conflict_path = ROOT / "docs/evidence/merge-conflict.md"
if conflict_path.is_file():
    conflict_evidence = conflict_path.read_text(encoding="utf-8")
    for marker in ("<<<<<<<", "=======", ">>>>>>>", "672570f"):
        if marker not in conflict_evidence:
            fail(f"merge-conflict evidence is missing {marker!r}")

if failures:
    print(f"\n{len(failures)} mechanical check(s) failed.")
    sys.exit(1)
print("PASS: submission structure and automatic-deduction checks are clean.")

