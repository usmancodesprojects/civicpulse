import time
from typing import cast

from redis import Redis


class RateLimitExceededError(RuntimeError):
    def __init__(self, retry_after: int) -> None:
        super().__init__("Rate limit exceeded")
        self.retry_after = retry_after


class RateLimiter:
    def __init__(self, redis: Redis, limit: int, window_seconds: int) -> None:
        self.redis = redis
        self.limit = limit
        self.window_seconds = window_seconds

    def check(self, client_ip: str) -> None:
        window = int(time.time()) // self.window_seconds
        key = f"rate:{client_ip}:{window}"
        count = cast(int, self.redis.incr(key))
        if count == 1:
            self.redis.expire(key, self.window_seconds + 1)
        if count > self.limit:
            retry_after = self.window_seconds - (int(time.time()) % self.window_seconds)
            raise RateLimitExceededError(max(1, retry_after))
