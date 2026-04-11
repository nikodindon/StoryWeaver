"""
Unified LLM client interface.
All LLM calls go through here. Swap backends without touching simulation code.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional


class LLMClient(ABC):
    """Abstract interface for all LLM backends."""

    @abstractmethod
    def complete(
        self,
        user: str,
        system: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> str:
        ...

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        ...
