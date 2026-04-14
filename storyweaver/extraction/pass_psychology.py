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
import re

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

    def _resolve_name_variants(self, characters: List[Dict]) -> Dict[str, List[str]]:
        """
        Group character names that likely refer to the same entity.

        Strategy:
        - For each character name, find all other names that are substrings
          or contain it (e.g. "Ron" ↔ "Ron Weasley" ↔ "Weasley")
        - Returns: {canonical_name: [variant1, variant2, ...]}

        The canonical name is the LONGEST variant (most complete form).
        """
        all_names = sorted(set(c["name"] for c in characters), key=len, reverse=True)
        resolved: Dict[str, List[str]] = {}  # canonical -> [variants]
        assigned = set()  # names already assigned to a group

        for name in all_names:
            if name in assigned:
                continue

            # Find all names that overlap with this one
            variants = [name]
            assigned.add(name)

            for other in all_names:
                if other == name or other in assigned:
                    continue
                name_lower = name.lower()
                other_lower = other.lower()

                # Check if one is contained in the other
                # "ron" in "ron weasley" or "weasley" in "ron weasley"
                if (other_lower in name_lower or name_lower in other_lower):
                    # Additional check: they must share at least one word
                    name_words = set(name_lower.split())
                    other_words = set(other_lower.split())
                    if name_words & other_words:  # intersection non vide
                        variants.append(other)
                        assigned.add(other)

            # Canonical = longest name (most descriptive)
            canonical = max(variants, key=len)
            resolved[canonical] = variants

        return resolved

    def run(self, segments: List[Dict], characters: List[Dict], book_id: str) -> Dict:
        psychology_models = {}

        # ── Step 1: Resolve name variants ──
        # "Ron" + "Ron Weasley" + "Weasley" → one group
        name_groups = self._resolve_name_variants(characters)
        logger.info(f"  Resolved {len(characters)} character names → "
                    f"{len(name_groups)} unique entities")

        # Log the groupings for debugging
        for canonical, variants in sorted(name_groups.items(), key=lambda x: -len(x[1])):
            if len(variants) > 1:
                logger.debug(f"    '{canonical}' ← {variants}")

        # ── Step 2: Filter by segment count (using ALL variants) ──
        min_segment_count = 3
        canonical_chars: Dict[str, List[str]] = {}  # canonical -> [variants]

        for canonical, variants in name_groups.items():
            # Count segments mentioning ANY variant of this name
            total_count = sum(
                1 for seg in segments
                if any(v.lower() in seg["text"].lower() for v in variants)
            )

            if total_count >= min_segment_count:
                # Find the original character dict for metadata
                char_data = next(
                    (c for c in characters if c["name"] == canonical),
                    {"name": canonical, "is_major": True, "description": ""}
                )
                canonical_chars[canonical] = variants
            else:
                logger.debug(f"  Skipping '{canonical}' ({variants}) — only in {total_count} segment(s)")

        logger.info(f"  Building psychology for {len(canonical_chars)} major characters "
                    f"(filtered from {len(characters)} total, min {min_segment_count} segments)")

        # ── Step 3: Extract psychology for each canonical character ──
        for char_name, variants in tqdm(canonical_chars.items(), desc="Pass 3: Psychology"):
            # Collect passages mentioning ANY variant
            char_passages = self._collect_passages_variants(variants, segments)

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

    def _collect_passages_variants(self, variants: List[str], segments: List[Dict]) -> List[str]:
        """Find all segments that mention ANY of the name variants."""
        passages = []
        for seg in segments:
            text_lower = seg["text"].lower()
            if any(v.lower() in text_lower for v in variants):
                passages.append(seg["text"])
        return passages

    def _count_segments(self, char_name: str, segments: List[Dict]) -> int:
        """Count how many segments mention this character."""
        name_lower = char_name.lower()
        return sum(1 for seg in segments if name_lower in seg["text"].lower())

    def _collect_passages(self, char_name: str, segments: List[Dict]) -> List[str]:
        """Find all segments that mention this character."""
        passages = []
        name_lower = char_name.lower()
        for seg in segments:
            if name_lower in seg["text"].lower():
                passages.append(seg["text"])
        return passages

    def _safe_parse(self, raw: str, char_name: str) -> Dict:
        """Robustly parse JSON from LLM output with multiple fallback strategies."""
        # Strategy 1: Try clean parse of whole text
        try:
            clean = raw.strip()
            if "```" in clean:
                parts = clean.split("```")
                for i in range(1, len(parts), 2):
                    block = parts[i].replace("json", "").strip()
                    try:
                        return json.loads(block)
                    except json.JSONDecodeError:
                        continue
            return json.loads(clean)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract JSON blocks by brace matching
        depth = 0
        start = None
        for i, ch in enumerate(raw):
            if ch == '{' and depth == 0:
                start = i
            depth += 1 if ch == '{' else (-1 if ch == '}' else 0)
            if depth == 0 and start is not None:
                block = raw[start:i+1]
                try:
                    return json.loads(block.strip())
                except json.JSONDecodeError:
                    # Strategy 3: Fix common issues
                    try:
                        fixed = re.sub(r',\s*([}\]])', r'\1', block)  # trailing commas
                        fixed = re.sub(r'(\w+)(\s*:)', r'"\1"\2', fixed)  # unquoted keys
                        fixed = fixed.replace("'", '"')  # single quotes
                        return json.loads(fixed)
                    except Exception:
                        pass
                start = None

        logger.warning(f"Psychology parse failed for {char_name}")
        return {}
