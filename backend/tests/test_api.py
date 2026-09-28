from contextlib import contextmanager
from uuid import uuid4

from fastapi.testclient import TestClient

from app.dependencies import get_complaint_service, get_rate_limiter, get_stats_service
from app.domain import ComplaintPage, ComplaintRead, StatsResponse, Status
from app.main import app


def sample() -> ComplaintRead:
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    return ComplaintRead(
        id=uuid4(),
        text="Water pipe flooding the street",
        location="Street 1",
        reporter_contact=None,
        category="water",
        priority="high",
        status="open",
        ai_summary="Water pipe flooding street",
        triaged_by="simulated",
        triage_latency_ms=2,
        created_at=now,
        updated_at=now,
        allowed_transitions=[Status.IN_PROGRESS, Status.REJECTED],
    )


class FakeComplaintService:
    def __init__(self) -> None:
        self.item = sample()

    def create(self, _payload):
        return self.item

    def get(self, _id):
        return self.item

    def list(self, **_kwargs):
        return ComplaintPage(items=[self.item], total=1, page=1, page_size=20)

    def update_status(self, _id, target):
        return self.item.model_copy(update={"status": target})


class NoopLimiter:
    def check(self, _ip):
        return None


class FakeStatsService:
    def get(self):
        return StatsResponse(by_category={"water": 1}, by_priority={"high": 1}, total=1), "HIT"


@contextmanager
def client():
    app.dependency_overrides[get_complaint_service] = lambda: FakeComplaintService()
    app.dependency_overrides[get_rate_limiter] = lambda: NoopLimiter()
    app.dependency_overrides[get_stats_service] = lambda: FakeStatsService()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_is_live_without_dependencies() -> None:
    with client() as test_client:
        assert test_client.get("/health").json() == {"status": "alive"}


def test_post_contract_returns_201() -> None:
    with client() as test_client:
        response = test_client.post(
            "/api/complaints", json={"text": "Water pipe flooding road", "location": "Street 1"}
        )
        assert response.status_code == 201
        assert response.json()["triaged_by"] == "simulated"


def test_trusted_proxy_keeps_client_rate_limit_buckets_separate(monkeypatch) -> None:
    from app.config import Settings

    identities: list[str] = []

    class RecordingLimiter:
        def check(self, client_ip: str) -> None:
            identities.append(client_ip)

    monkeypatch.setattr(
        "app.routes.complaints.get_settings", lambda: Settings(trust_proxy_headers=True)
    )
    app.dependency_overrides[get_complaint_service] = lambda: FakeComplaintService()
    app.dependency_overrides[get_rate_limiter] = lambda: RecordingLimiter()
    try:
        with TestClient(app) as test_client:
            for address in ("203.0.113.10", "203.0.113.11"):
                response = test_client.post(
                    "/api/complaints",
                    headers={"X-Real-IP": address},
                    json={"text": "Water pipe flooding road", "location": "Street 1"},
                )
                assert response.status_code == 201
    finally:
        app.dependency_overrides.clear()
    assert identities == ["203.0.113.10", "203.0.113.11"]


def test_validation_returns_400_field_errors() -> None:
    with client() as test_client:
        response = test_client.post("/api/complaints", json={"text": "short", "location": "x"})
        assert response.status_code == 400
        assert {error["field"] for error in response.json()["errors"]} == {"text", "location"}


def test_list_and_status_contracts() -> None:
    with client() as test_client:
        listed = test_client.get("/api/complaints?page=1&page_size=20")
        assert listed.status_code == 200 and listed.json()["total"] == 1
        item_id = listed.json()["items"][0]["id"]
        updated = test_client.patch(
            f"/api/complaints/{item_id}/status", json={"status": "in_progress"}
        )
        assert updated.status_code == 200 and updated.json()["status"] == "in_progress"


def test_stats_exposes_cache_header() -> None:
    with client() as test_client:
        response = test_client.get("/api/stats")
        assert response.headers["X-Cache"] == "HIT"
