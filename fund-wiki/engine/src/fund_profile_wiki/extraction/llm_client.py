"""OpenAI-compatible LLM client."""

from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from fund_profile_wiki.config import Settings


@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    base_url: str
    model: str


def get_llm_config(provider: str) -> LLMConfig:
    provider = provider.lower()
    if provider == "kimi":
        if not Settings.kimi_api_key:
            raise ValueError("KIMI_API_KEY is not configured")
        if not Settings.kimi_model:
            raise ValueError("FPW_KIMI_MODEL is not configured")
        return LLMConfig(Settings.kimi_api_key, Settings.kimi_base_url, Settings.kimi_model)
    if provider == "deepseek":
        if not Settings.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY is not configured")
        return LLMConfig(Settings.deepseek_api_key, Settings.deepseek_base_url, Settings.deepseek_model)
    if provider == "openai":
        if not Settings.openai_api_key:
            raise ValueError("CHATGPT_API_KEY or OPENAI_API_KEY is not configured")
        return LLMConfig(Settings.openai_api_key, Settings.openai_base_url, Settings.openai_model)
    raise ValueError(f"Unsupported provider: {provider}")


class LLMClient:
    def __init__(self, provider: str = "kimi", temperature: float = 0.1, timeout_seconds: int | None = None):
        cfg = get_llm_config(provider)
        self.client = OpenAI(
            api_key=cfg.api_key,
            base_url=cfg.base_url,
            timeout=timeout_seconds or Settings.llm_timeout_seconds,
            max_retries=Settings.llm_max_retries,
        )
        self.model = cfg.model
        self.temperature = temperature

    def complete(self, system_prompt: str, user_text: str, max_tokens: int = 4096) -> str:
        if Settings.llm_input_max_chars > 0 and len(user_text) > Settings.llm_input_max_chars:
            user_text = user_text[: Settings.llm_input_max_chars] + "\n\n[TRUNCATED_BY_FUND_WIKI]"
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            temperature=self.temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
