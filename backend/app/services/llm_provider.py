"""Configurable LLM provider abstraction layer."""

from abc import ABC, abstractmethod
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from backend.app.core.config import settings
from backend.app.core.logging import logger


class LLMResponse(BaseModel):
    """Structured response from an LLM call including token and latency metrics."""
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    model: str = ""
    provider: str = ""


class BaseLLMProvider(ABC):
    """Abstract interface for LLM calls."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        """Synchronously generate an LLM response."""
        pass


class MockLLMProvider(BaseLLMProvider):
    """Deterministic mock provider for offline testing and baseline validation."""

    def __init__(self, model_name: str = "mock-model"):
        self.model_name = model_name

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        start_time = time.perf_counter()
        # Approximate token count by words / 0.75
        words = len(prompt.split())
        in_tokens = max(1, int(words * 1.3))
        out_tokens = 25
        time.sleep(0.01)  # small simulated latency
        latency = (time.perf_counter() - start_time) * 1000.0

        return LLMResponse(
            text="Mock grounded response based on provided context.",
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            total_tokens=in_tokens + out_tokens,
            latency_ms=round(latency, 2),
            model=self.model_name,
            provider="mock",
        )


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini LLM provider."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.LLM_MODEL
        self._fallback_mock = MockLLMProvider(self.model)

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. Falling back to MockLLMProvider.")
            return self._fallback_mock.generate(prompt, system_prompt=system_prompt, **kwargs)

        start_time = time.perf_counter()
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model_instance = genai.GenerativeModel(
                self.model,
                system_instruction=system_prompt if system_prompt else None,
            )
            response = model_instance.generate_content(prompt)
            latency = (time.perf_counter() - start_time) * 1000.0

            # Estimate or extract tokens
            usage = getattr(response, "usage_metadata", None)
            if usage:
                in_tok = getattr(usage, "prompt_token_count", 0)
                out_tok = getattr(usage, "candidates_token_count", 0)
                total_tok = getattr(usage, "total_token_count", in_tok + out_tok)
            else:
                in_tok = len(prompt.split())
                out_tok = len(response.text.split()) if response.text else 0
                total_tok = in_tok + out_tok

            return LLMResponse(
                text=response.text or "",
                input_tokens=in_tok,
                output_tokens=out_tok,
                total_tokens=total_tok,
                latency_ms=round(latency, 2),
                model=self.model,
                provider="gemini",
            )
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}. Falling back to mock response.")
            mock_res = self._fallback_mock.generate(prompt, system_prompt=system_prompt, **kwargs)
            mock_res.provider = f"gemini-fallback ({e})"
            return mock_res


def get_llm_provider() -> BaseLLMProvider:
    """Factory function to instantiate the configured LLM provider."""
    provider_name = settings.LLM_PROVIDER.lower()
    if provider_name == "mock":
        return MockLLMProvider()
    elif provider_name == "gemini":
        return GeminiLLMProvider()
    else:
        logger.warning(f"Unknown LLM provider '{provider_name}'; falling back to mock provider.")
        return MockLLMProvider()


llm_provider = get_llm_provider()
