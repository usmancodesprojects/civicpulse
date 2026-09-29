from collections.abc import Generator

from app.config import get_settings
from app.db import session_scope
from app.providers.cache import get_redis
from app.providers.triage.factory import create_provider
from app.repositories.complaints import ComplaintRepository
from app.services.complaints import ComplaintService
from app.services.rate_limit import RateLimiter
from app.services.stats import StatsService
from app.services.triage import TriageService


def get_complaint_service() -> Generator[ComplaintService, None, None]:
    settings = get_settings()
    redis = get_redis()
    with session_scope() as session:
        repository = ComplaintRepository(session)
        triage = TriageService(create_provider(settings), redis, settings)
        yield ComplaintService(repository, triage, redis)


def get_stats_service() -> Generator[StatsService, None, None]:
    settings = get_settings()
    redis = get_redis()
    with session_scope() as session:
        yield StatsService(ComplaintRepository(session), redis, settings)


def get_rate_limiter() -> RateLimiter:
    settings = get_settings()
    return RateLimiter(
        get_redis(), settings.rate_limit_requests, settings.rate_limit_window_seconds
    )
