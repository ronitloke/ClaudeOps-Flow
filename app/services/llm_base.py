from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseLLMClient(ABC):
    @abstractmethod
    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        pass