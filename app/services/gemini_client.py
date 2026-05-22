import json
import re
from typing import Any, Dict

from google import genai

from app.core.settings import get_settings
from app.services.llm_base import BaseLLMClient


class GeminiJSONClient(BaseLLMClient):
    def __init__(self) -> None:
        self.settings = get_settings()

        if not self.settings.gemini_api_key.strip():
            raise ValueError("GEMINI_API_KEY is empty. Add it in your .env file.")

        self.client = genai.Client(api_key=self.settings.gemini_api_key)

    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        combined_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"

        response = self.client.models.generate_content(
            model=self.settings.gemini_model,
            contents=combined_prompt,
        )

        text_output = getattr(response, "text", "") or ""
        return self._parse_json(text_output)

    @staticmethod
    def _parse_json(text: str) -> Dict[str, Any]:
        cleaned = text.strip()

        fenced_match = re.search(r"```json\s*(\{.*\})\s*```", cleaned, re.DOTALL)
        if fenced_match:
            cleaned = fenced_match.group(1)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = cleaned[start : end + 1]
                return json.loads(candidate)
            raise ValueError(f"Gemini did not return valid JSON.\nRaw output:\n{text}")