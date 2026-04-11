"""
Deep Extraction Pipeline — The most expensive, most important component.

Runs offline, once per book. Produces the structured data that feeds
the World Compiler. Results are cached aggressively.

Pipeline passes:
  Pass 1 — STRUCTURE  : entities, locations, objects, events
  Pass 2 — RELATIONS  : social graph, conflicts, timeline
  Pass 3 — PSYCHOLOGY : per-character personality models
  Pass 4 — SYMBOLISM  : themes, motifs, world rules, narrative gravity
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional
import json
import hashlib

from loguru import logger
from tqdm import tqdm

from ..models.llm_client import LLMClient
from .pass_structure import StructurePass
from .pass_relations import RelationsPass
from .pass_psychology import PsychologyPass
from .pass_symbolism import SymbolismPass
from .cache import ExtractionCache


class ExtractionPipeline:
    """
    Orchestrates all four extraction passes.

    Designed for long runtimes — a full novel may take 2–8 hours.
    Progress is checkpointed at every pass so you can resume.
    """

    PASSES = ["structure", "relations", "psychology", "symbolism"]

    def __init__(
        self,
        llm_client: LLMClient,
        cache_dir: Path,
        config: Dict,
    ):
        self.llm = llm_client
        self.cache = ExtractionCache(cache_dir)
        self.config = config
        self.chunk_size = config.get("chunk_size_tokens", 2000)
        self.micro_chunk_size = config.get("micro_chunk_size_tokens", 500)

    def run(
        self,
        segments: List[Dict],       # From Segmenter: [{id, text, chapter, scene}]
        book_id: str,
        passes: Optional[List[str]] = None,
    ) -> Dict:
        """
        Run the full extraction pipeline.
        Returns: combined extraction result dict.
        """
        passes_to_run = passes or self.PASSES
        results = {}

        logger.info(f"Starting extraction for '{book_id}' — passes: {passes_to_run}")
        logger.info(f"  {len(segments)} segments to process")

        # --- PASS 1: STRUCTURE ---
        if "structure" in passes_to_run:
            logger.info("Pass 1/4: Structure extraction")
            p1 = StructurePass(self.llm, self.cache, self.chunk_size)
            results["structure"] = p1.run(segments, book_id)
            self._checkpoint(book_id, "structure", results["structure"])

        # --- PASS 2: RELATIONS ---
        if "relations" in passes_to_run:
            logger.info("Pass 2/4: Relations extraction")
            structure = results.get("structure") or self._load_checkpoint(book_id, "structure")
            p2 = RelationsPass(self.llm, self.cache, self.chunk_size)
            results["relations"] = p2.run(segments, structure, book_id)
            self._checkpoint(book_id, "relations", results["relations"])

        # --- PASS 3: PSYCHOLOGY ---
        if "psychology" in passes_to_run:
            logger.info("Pass 3/4: Psychology extraction (most expensive)")
            structure = results.get("structure") or self._load_checkpoint(book_id, "structure")
            p3 = PsychologyPass(self.llm, self.cache, self.micro_chunk_size)
            results["psychology"] = p3.run(segments, structure["characters"], book_id)
            self._checkpoint(book_id, "psychology", results["psychology"])

        # --- PASS 4: SYMBOLISM ---
        if "symbolism" in passes_to_run:
            logger.info("Pass 4/4: Symbolism & world rules extraction")
            structure = results.get("structure") or self._load_checkpoint(book_id, "structure")
            p4 = SymbolismPass(self.llm, self.cache)
            results["symbolism"] = p4.run(segments, structure, book_id)
            self._checkpoint(book_id, "symbolism", results["symbolism"])

        logger.info(f"Extraction complete for '{book_id}'")
        return results

    def _checkpoint(self, book_id: str, pass_name: str, data: Dict) -> None:
        path = self.cache.cache_dir / book_id / f"pass_{pass_name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"  Checkpoint saved: {pass_name}")

    def _load_checkpoint(self, book_id: str, pass_name: str) -> Dict:
        path = self.cache.cache_dir / book_id / f"pass_{pass_name}.json"
        if not path.exists():
            raise FileNotFoundError(f"No checkpoint found for {book_id}/{pass_name}. Run that pass first.")
        with open(path) as f:
            return json.load(f)
