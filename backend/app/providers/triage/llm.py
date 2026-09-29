import httpx

from app.config import Settings
from app.domain import TriageResult
from app.providers.triage.base import ProviderError, RetryableProviderError
from app.providers.triage.structured import SYSTEM_PROMPT, parse_result


class LLMTriage:
    name = "llm:groq"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def triage(self, text: str, location: str) -> TriageResult:
        if not self.settings.llm_api_key:
            raise ProviderError("LLM_API_KEY is required for the llm provider")
        user = f"<complaint>\n{text}\n</complaint>\n<location>{location}</location>"
        payload = {
            "model": self.settings.llm_model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
        }
        try:
            response = httpx.post(
                f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                json=payload,
                timeout=10.0,
            )
        except httpx.TimeoutException as exc:
            raise RetryableProviderError("LLM timed out") from exc
        except httpx.HTTPError as exc:
            raise RetryableProviderError("LLM network failure") from exc
        if response.status_code == 429 or response.status_code >= 500:
            raise RetryableProviderError(f"LLM returned {response.status_code}")
        if response.status_code >= 400:
            raise ProviderError(f"LLM rejected request with {response.status_code}")
        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            raise ProviderError("LLM returned invalid structured output") from exc
        return parse_result(content, "LLM")
