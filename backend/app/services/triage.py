import hashlib
import json
import logging
import random
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from redis import Redis

from app.config import Settings
from app.domain import ProviderOutcome, TriageResult
from app.observability import TRIAGE_FALLBACKS, TRIAGE_LATENCY
from app.providers.triage.base import ProviderError, RetryableProviderError, TriageProvider
from app.providers.triage.rules import RuleBasedTriage

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TriageDecision:
    result: TriageResult
    provider: str
    latency_ms: int
    fallback: bool


class TriageService:
    def __init__(self, provider: TriageProvider, redis: Redis, settings: Settings) -> None:
        self.provider = provider
        self.redis = redis
        self.settings = settings
        self.fallback = RuleBasedTriage()

    def triage(self, complaint_id: UUID, text: str, location: str) -> TriageDecision:
        cache_key = (
            "triage:" + hashlib.sha256(f"{text.strip()}|{location.strip()}".encode()).hexdigest()
        )
        cached = cast(str | None, self.redis.get(cache_key))
        if cached:
            payload = json.loads(cached)
            decision = TriageDecision(
                result=TriageResult.model_validate(payload["result"]),
                provider=payload["provider"],
                latency_ms=0,
                fallback=payload.get("fallback", False),
            )
            self._record(decision)
            return decision

        started = time.perf_counter()
        fallback = False
        provider_name = self.provider.name
        try:
            if self.redis.exists(self._circuit_key()):
                raise ProviderError("triage provider circuit is open")
            result = self._with_retry(text, location)
            self.redis.delete(self._failure_key())
        except (ProviderError, RetryableProviderError) as exc:
            if not self.redis.exists(self._circuit_key()):
                failures = self.redis.incr(self._failure_key())
                if failures == 1:
                    self.redis.expire(
                        self._failure_key(), self.settings.triage_circuit_window_seconds
                    )
                if failures >= self.settings.triage_circuit_failures:
                    self.redis.setex(
                        self._circuit_key(), self.settings.triage_circuit_cooldown_seconds, "open"
                    )
                    self.redis.delete(self._failure_key())
            fallback = True
            provider_name = "rules:fallback"
            result = self.fallback.triage(text, location)
            logger.warning(
                "triage_fallback",
                extra={
                    "complaint_id": str(complaint_id),
                    "provider": self.provider.name,
                    "error_class": type(exc).__name__,
                },
            )
        latency_ms = max(1, round((time.perf_counter() - started) * 1000))
        TRIAGE_LATENCY.labels(provider_name).observe(latency_ms / 1000)
        if fallback:
            TRIAGE_FALLBACKS.labels(self.provider.name).inc()
        decision = TriageDecision(result, provider_name, latency_ms, fallback)
        if not fallback:
            self.redis.setex(
                cache_key,
                self.settings.triage_cache_ttl_seconds,
                json.dumps(
                    {
                        "result": result.model_dump(mode="json"),
                        "provider": provider_name,
                        "fallback": False,
                    }
                ),
            )
        self._record(decision)
        return decision

    def _failure_key(self) -> str:
        return f"triage:circuit:{self.provider.name}:failures"

    def _circuit_key(self) -> str:
        return f"triage:circuit:{self.provider.name}:open"

    def _with_retry(self, text: str, location: str) -> TriageResult:
        for attempt in range(self.settings.triage_retry_attempts):
            try:
                return self.provider.triage(text, location)
            except RetryableProviderError:
                if attempt + 1 == self.settings.triage_retry_attempts:
                    raise
                delay = min(self.settings.triage_retry_base_seconds * 2**attempt, 1.0)
                time.sleep(random.uniform(0, delay))
        raise AssertionError("retry loop has at least one attempt")

    def _record(self, decision: TriageDecision) -> None:
        outcome = ProviderOutcome(
            provider=decision.provider,
            latency_ms=decision.latency_ms,
            fallback=decision.fallback,
            timestamp=datetime.now(UTC),
        )
        key = "triage:outcomes"
        pipeline = self.redis.pipeline()
        pipeline.lpush(key, outcome.model_dump_json())
        pipeline.ltrim(key, 0, 19)
        pipeline.execute()

    def outcomes(self) -> list[ProviderOutcome]:
        items = cast(list[str], self.redis.lrange("triage:outcomes", 0, 19))
        return [ProviderOutcome.model_validate_json(item) for item in items]
