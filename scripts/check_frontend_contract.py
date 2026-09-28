"""Fail when the handwritten TypeScript client drifts from FastAPI's OpenAPI contract."""
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("TRIAGE_PROVIDER", "simulated")

from app.main import app  # noqa: E402


schema = app.openapi()
typescript = (ROOT / "frontend" / "src" / "api" / "types.ts").read_text(encoding="utf-8")

expected_operations = {
    ("/api/complaints", "post"),
    ("/api/complaints", "get"),
    ("/api/complaints/{complaint_id}", "get"),
    ("/api/complaints/{complaint_id}/status", "patch"),
    ("/api/stats", "get"),
    ("/api/meta/providers", "get"),
    ("/health", "get"),
    ("/ready", "get"),
}
actual_operations = {
    (path, method)
    for path, operations in schema["paths"].items()
    for method in operations
    if method in {"get", "post", "patch", "put", "delete"}
}
missing_operations = expected_operations - actual_operations
if missing_operations:
    raise SystemExit(f"Frontend contract is missing backend operations: {sorted(missing_operations)}")

for name in ("Category", "Priority", "Status"):
    values = schema["components"]["schemas"][name]["enum"]
    for value in values:
        if f'"{value}"' not in typescript:
            raise SystemExit(f"TypeScript types are missing {name} value {value!r}")

required = schema["components"]["schemas"]["ComplaintRead"]["required"]
for field in required:
    if f"{field}:" not in typescript:
        raise SystemExit(f"TypeScript Complaint is missing required field {field!r}")

print("PASS: TypeScript API types match FastAPI OpenAPI enums, fields, and operations.")

