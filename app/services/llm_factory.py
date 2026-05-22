from app.core.settings import get_settings
from app.services.llm_base import BaseLLMClient


def get_llm_client() -> BaseLLMClient:
    settings = get_settings()
    provider = settings.llm_provider.strip().lower()

    if provider == "groq":
        from app.services.groq_client import GroqClient
        return GroqClient()

    if provider == "gemini":
        from app.services.gemini_client import GeminiClient
        return GeminiClient()

    if provider == "claude":
        from app.services.claude_client import ClaudeClient
        return ClaudeClient()

    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")