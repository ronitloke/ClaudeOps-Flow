import json
import re
from typing import Any, Dict

from groq import Groq

from app.core.settings import get_settings
from app.services.llm_base import BaseLLMClient


class GroqJSONClient(BaseLLMClient):
    def __init__(self) -> None:
        self.settings = get_settings()

        if not self.settings.groq_api_key.strip():
            raise ValueError("GROQ_API_KEY is empty. Add it in your .env file.")

        self.client = Groq(api_key=self.settings.groq_api_key)

    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.settings.groq_model,
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        text_output = response.choices[0].message.content or ""
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
            raise ValueError(f"Groq did not return valid JSON.\nRaw output:\n{text}")