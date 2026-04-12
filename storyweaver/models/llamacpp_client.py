"""
llama.cpp backend via its OpenAI-compatible server.

Usage:
  ./llama-server -m your-model.gguf --port 8080 --ctx-size 8192

Then:
  client = LlamaCppClient(base_url="http://localhost:8080")
"""
from __future__ import annotations
from typing import List, Optional
import requests
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .llm_client import LLMClient


class LlamaCppClient(LLMClient):
    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        model: str = "local-model",
        default_max_tokens: int = 512,
        default_temperature: float = 0.7,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.default_max_tokens = default_max_tokens
        self.default_temperature = default_temperature

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def complete(
        self,
        user: str,
        system: Optional[str] = None,
        max_tokens: int = None,
        temperature: float = None,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.default_max_tokens,
            "temperature": temperature or self.default_temperature,
        }

        logger.debug(f"LLM call: {len(user)} chars input")
        url = self.base_url.rstrip("/")
        # Handle both "http://host:port" and "http://host:port/v1" base URLs
        if not url.endswith("/v1"):
            url = url.rstrip("/") + "/v1"
        response = requests.post(
            f"{url}/chat/completions",
            json=payload,
            timeout=600,  # 10 min — local inference can be slow
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        logger.debug(f"LLM response: {len(content)} chars")
        return content

    def embed(self, text: str) -> List[float]:
        url = self.base_url.rstrip("/")
        if not url.endswith("/v1"):
            url = url.rstrip("/") + "/v1"
        response = requests.post(
            f"{url}/embeddings",
            json={"input": text, "model": self.model},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]
