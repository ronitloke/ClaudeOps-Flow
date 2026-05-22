import json
import re

from anthropic import Anthropic

from app.core.settings import get_settings
from app.services.llm_base import BaseLLMClient


class ClaudeClient(BaseLLMClient):
    def __init__(self) -> None:
        settings = get_settings()

        if not settings.anthropic_api_key.strip():
            raise ValueError("ANTHROPIC_API_KEY is missing in .env")

        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model
        self.max_tokens = settings.claude_max_tokens
        self.temperature = settings.claude_temperature

    @staticmethod
    def _extract_text(response) -> str:
        parts = []
        for block in response.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        return "\n".join(parts).strip()

    @staticmethod
    def _extract_json_text(text: str) -> str:
        text = text.strip()

        fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fenced:
            return fenced.group(1)

        fenced_generic = re.search(r"```\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fenced_generic:
            return fenced_generic.group(1)

        first = text.find("{")
        last = text.rfind("}")
        if first != -1 and last != -1 and last > first:
            return text[first:last + 1]

        return text

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
        )

        text = self._extract_text(response)
        json_text = self._extract_json_text(text)

        usage = getattr(response, "usage", None)

        input_tokens = getattr(usage, "input_tokens", None) if usage else None
        output_tokens = getattr(usage, "output_tokens", None) if usage else None

        total_tokens = None
        if input_tokens is not None or output_tokens is not None:
            total_tokens = int(input_tokens or 0) + int(output_tokens or 0)

        try:
            parsed = json.loads(json_text)
            parsed["_llm_usage"] = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            }
            return parsed
        except json.JSONDecodeError as exc:
            raise ValueError(f"Claude returned non-JSON output: {text}") from exc