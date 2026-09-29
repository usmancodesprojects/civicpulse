import httpx

from app.config import Settings
from app.domain import TriageResult
from app.providers.triage.base import ProviderError, RetryableProviderError
from app.providers.triage.structured import SYSTEM_PROMPT, parse_result


class OllamaTriage:
    name = "llm:ollama"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def triage(self, text: str, location: str) -> TriageResult:
        prompt = (
            f"{SYSTEM_PROMPT}\n"
            f"<complaint>{text}</complaint>\n<location>{location}</location>"
        )
        try:
            response = httpx.post(
                f"{self.settings.ollama_url.rstrip('/')}/api/generate",
                json={
                    "model": self.settings.ollama_model,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                },
                timeout=10.0,
            )
        except httpx.TimeoutException as exc:
            raise RetryableProviderError("Ollama timed out") from exc
        except httpx.HTTPError as exc:
            raise RetryableProviderError("Ollama network failure") from exc
        if response.status_code == 429 or response.status_code >= 500:
            raise RetryableProviderError(f"Ollama returned {response.status_code}")
        if response.status_code >= 400:
            raise ProviderError(f"Ollama rejected request with {response.status_code}")
        try:
            content = response.json()["response"]
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError("Ollama returned invalid structured output") from exc
        return parse_result(content, "Ollama")
