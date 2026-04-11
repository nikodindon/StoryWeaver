"""
Extraction cache — avoids re-running expensive LLM calls.
Keyed by hash(prompt + chunk_id).
"""
from pathlib import Path
from typing import Optional
import hashlib
import json


class ExtractionCache:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._hits = 0
        self._misses = 0

    def get(self, prompt: str, chunk_id: str) -> Optional[str]:
        key = self._key(prompt, chunk_id)
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            self._hits += 1
            with open(path) as f:
                return json.load(f)["response"]
        self._misses += 1
        return None

    def set(self, prompt: str, chunk_id: str, response: str) -> None:
        key = self._key(prompt, chunk_id)
        path = self.cache_dir / f"{key}.json"
        with open(path, "w") as f:
            json.dump({"chunk_id": chunk_id, "response": response}, f)

    def stats(self) -> str:
        total = self._hits + self._misses
        rate = (self._hits / total * 100) if total > 0 else 0
        return f"Cache: {self._hits}/{total} hits ({rate:.1f}%)"

    def _key(self, prompt: str, chunk_id: str) -> str:
        content = f"{chunk_id}::{prompt[:200]}"
        return hashlib.md5(content.encode()).hexdigest()
