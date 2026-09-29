from uuid import uuid4

import pytest

from app.config import Settings
from app.domain import Category, ComplaintCreate, Priority, Status, TriageResult
from app.providers.triage.simulated import SimulatedTriage
from app.services.complaints import ComplaintService, InvalidTransitionError
from app.services.rate_limit import RateLimiter, RateLimitExceededError
from app.services.stats import StatsService
from app.services.triage import TriageService


def config() -> Settings:
    return Settings(
        database_url="sqlite://", redis_url="redis://unused", triage_provider="simulated"
    )


def make_service(repository, redis_client) -> ComplaintService:
    triage = TriageService(SimulatedTriage(), redis_client, config())
    return ComplaintService(repository, triage, redis_client)


def test_repository_crud_filter_and_stats(repository, redis_client) -> None:
    service = make_service(repository, redis_client)
    created = service.create(
        ComplaintCreate(text="Water pipe flooding several homes", location="Street 9")
    )
    assert service.get(created.id).id == created.id
    page = service.list(
        category=Category.WATER, priority=Priority.HIGH, status=Status.OPEN, page=1, page_size=10
    )
    assert page.total == 1
    stats, cache = StatsService(repository, redis_client, config()).get()
    assert cache == "MISS"
    assert stats.by_category[Category.WATER] == 1


def test_valid_status_transition(repository, redis_client) -> None:
    service = make_service(repository, redis_client)
    created = service.create(
        ComplaintCreate(text="Road pothole requires repair now", location="Main Road")
    )
    updated = service.update_status(created.id, Status.IN_PROGRESS)
    assert updated.status == Status.IN_PROGRESS
    assert updated.allowed_transitions == [Status.REJECTED, Status.RESOLVED]


def test_invalid_status_transition_names_attempt(repository, redis_client) -> None:
    service = make_service(repository, redis_client)
    created = service.create(
        ComplaintCreate(text="Road pothole requires repair now", location="Main Road")
    )
    with pytest.raises(InvalidTransitionError, match="open -> resolved"):
        service.update_status(created.id, Status.RESOLVED)


def test_stats_cache_hit_and_write_invalidation(repository, redis_client) -> None:
    service = make_service(repository, redis_client)
    stats_service = StatsService(repository, redis_client, config())
    service.create(ComplaintCreate(text="Garbage waste remains uncollected", location="Lane 5"))
    _, first = stats_service.get()
    _, second = stats_service.get()
    assert (first, second) == ("MISS", "HIT")
    service.create(ComplaintCreate(text="Streetlight lamp is not working", location="Lane 6"))
    _, third = stats_service.get()
    assert third == "MISS"


def test_rate_limiter_uses_redis_and_returns_retry(redis_client) -> None:
    limiter = RateLimiter(redis_client, limit=2, window_seconds=60)
    limiter.check("127.0.0.1")
    limiter.check("127.0.0.1")
    with pytest.raises(RateLimitExceededError) as raised:
        limiter.check("127.0.0.1")
    assert raised.value.retry_after > 0


def test_repository_accepts_explicit_triage(repository) -> None:
    data = ComplaintCreate(text="Unknown object blocks access gate", location="Park Gate")
    result = TriageResult(
        category="other", priority="normal", summary="Object blocks gate", confidence=0.8
    )
    row = repository.create(uuid4(), data, result, "rules", 1)
    assert repository.get(row.id) is row
