from typing import cast

from redis import Redis

from app.config import Settings
from app.domain import StatsResponse
from app.repositories.complaints import ComplaintRepository


class StatsService:
    def __init__(self, repository: ComplaintRepository, redis: Redis, settings: Settings) -> None:
        self.repository = repository
        self.redis = redis
        self.settings = settings

    def get(self) -> tuple[StatsResponse, str]:
        cached = cast(str | None, self.redis.get("stats:v1"))
        if cached:
            return StatsResponse.model_validate_json(cached), "HIT"
        stats = StatsResponse.model_validate(self.repository.stats())
        self.redis.setex("stats:v1", self.settings.stats_cache_ttl_seconds, stats.model_dump_json())
        return stats, "MISS"
