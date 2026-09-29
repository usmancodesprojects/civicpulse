import hashlib

from app.domain import TriageResult
from app.providers.triage.base import ProviderError, RetryableProviderError
from app.providers.triage.rules import RuleBasedTriage


class SimulatedTriage:
    name = "simulated"

    def triage(self, text: str, location: str) -> TriageResult:
        lowered = text.lower()
        if "[simulate:timeout]" in lowered:
            raise RetryableProviderError("simulated timeout")
        if "[simulate:malformed]" in lowered:
            raise ProviderError("simulated malformed output")
        result = RuleBasedTriage().triage(text, location)
        digest = hashlib.sha256(f"{text}|{location}".encode()).digest()
        confidence = 0.80 + (digest[0] % 20) / 100
        return result.model_copy(update={"confidence": min(confidence, 0.99)})
