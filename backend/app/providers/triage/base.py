from typing import Protocol

from app.domain import TriageResult


class RetryableProviderError(RuntimeError):
    """A timeout, rate limit, or upstream server failure."""


class ProviderError(RuntimeError):
    """A non-retryable provider or response-validation failure."""


class TriageProvider(Protocol):
    name: str

    def triage(self, text: str, location: str) -> TriageResult: ...
