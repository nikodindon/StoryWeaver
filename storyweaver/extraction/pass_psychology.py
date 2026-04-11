"""
Pass 3 — Psychology Extraction (most expensive pass)

For each major character:
  - Collects ALL passages featuring that character
  - Runs deep LLM analysis
  - Produces full psychology model (Big Five + narrative traits + goals)
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List
import json

from loguru import logger
from tqdm import tqdm

from ..models.llm_client import LLMClient
from .cache import ExtractionCache


class PsychologyPass:
    def __init__(self, llm: LLMClient, cache: ExtractionCache, micro_chunk_size: int):
        self.llm = llm
        self.cache = cache
        self.micro_chunk_size = micro_chunk_size

        # Load prompt template
        prompt_path = Path(__file__).parent / "prompts" / "character_psychology.txt"
        self.prompt_template = prompt_path.read_text()

    def run(self, segments: List[Dict], characters: List[Dict], book_id: str) -> Dict:
        psychology_models = {}
        major_chars = [c for c in characters if c.get("is_major", True)]

        logger.info(f"  Building psychology for {len(major_chars)} major characters")

        for char in tqdm(major_chars, desc="Pass 3: Psychology"):
            char_name = char["name"]
            char_passages = self._collect_passages(char_name, segments)

            if not char_passages:
                logger.warning(f"  No passages found for {char_name}, skipping")
                continue

            chunk_id = f"{book_id}::psych::{char_name}"
            combined_passages = "\n\n---\n\n".join(char_passages[:20])  # Cap at 20 passages
            # Use replace() to avoid conflict with JSON {} braces in the template
            prompt = self.prompt_template.replace(
                "{character_name}", char_name
            ).replace(
                "{character_passages}", combined_passages[:6000],
            )

            cached = self.cache.get(prompt, chunk_id)
            if cached:
                result = cached
            else:
                logger.debug(f"  Running psychology extraction for {char_name}...")
                result = self.llm.complete(
                    user=prompt,
                    temperature=0.2,
                    max_tokens=1500,
                )
                self.cache.set(prompt, chunk_id, result)

            parsed = self._safe_parse(result, char_name)
            if parsed:
                psychology_models[char_name.lower().replace(" ", "_")] = parsed

        return psychology_models

    def _collect_passages(self, char_name: str, segments: List[Dict]) -> List[str]:
        """Find all segments that mention this character."""
        passages = []
        name_lower = char_name.lower()
        for seg in segments:
            if name_lower in seg["text"].lower():
                passages.append(seg["text"])
        return passages

    def _safe_parse(self, raw: str, char_name: str) -> Dict:
        try:
            clean = raw.strip()
            if "```" in clean:
                clean = clean.split("```")[1].replace("json", "").strip()
            return json.loads(clean)
        except json.JSONDecodeError:
            logger.warning(f"Psychology parse failed for {char_name}")
            return {}
