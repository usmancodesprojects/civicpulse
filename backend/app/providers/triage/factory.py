from app.config import Settings
from app.providers.triage.base import ProviderError, TriageProvider
from app.providers.triage.llm import LLMTriage
from app.providers.triage.ollama import OllamaTriage
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage


def create_provider(settings: Settings) -> TriageProvider:
    if settings.triage_provider == "llm":
        return LLMTriage(settings)
    if settings.triage_provider == "ollama":
        return OllamaTriage(settings)
    if settings.triage_provider == "rules":
        return RuleBasedTriage()
    if settings.triage_provider == "simulated":
        return SimulatedTriage()
    raise ProviderError(f"Unknown TRIAGE_PROVIDER: {settings.triage_provider}")
