"""
Intent parser — converts raw player text into structured game actions.

Hybrid approach:
  1. Fast rule-based pass for common commands
  2. LLM fallback for ambiguous/complex input
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Dict, Optional
from loguru import logger


@dataclass
class Intent:
    action: str                     # go, talk, take, examine, drop, wait, help, quit
    target: Optional[str] = None
    target_type: Optional[str] = None   # location, character, object
    parameters: Dict = field(default_factory=dict)
    raw_input: str = ""
    confidence: float = 1.0


# Common command patterns (fast path)
PATTERNS = [
    (r'^(go|move|walk|run|travel|head)\s+(?:to\s+)?(.+)$', 'go', 'location'),
    (r'^(north|south|east|west|up|down|n|s|e|w)$', 'go', 'direction'),
    (r'^(talk|speak|ask|say)\s+(?:to\s+)?(.+)$', 'talk', 'character'),
    (r'^(take|pick up|grab|get)\s+(.+)$', 'take', 'object'),
    (r'^(drop|put down|leave)\s+(.+)$', 'drop', 'object'),
    (r'^(examine|look at|inspect|check|read)\s+(.+)$', 'examine', 'object'),
    (r'^(look|l)$', 'look', None),
    (r'^(inventory|i|items)$', 'inventory', None),
    (r'^(wait|w|rest)$', 'wait', None),
    (r'^(help|h|\?)$', 'help', None),
    (r'^(quit|exit|q)$', 'quit', None),
]


class IntentParser:
    def __init__(self, llm_client=None, use_llm_fallback: bool = True):
        self.llm = llm_client
        self.use_llm_fallback = use_llm_fallback

    def parse(self, raw_input: str, world_snapshot: Dict = None) -> Intent:
        raw = raw_input.strip().lower()

        # Fast path: rule-based
        for pattern, action, target_type in PATTERNS:
            match = re.match(pattern, raw, re.IGNORECASE)
            if match:
                groups = match.groups()
                target = groups[-1].strip() if len(groups) > 1 else None
                logger.debug(f"Rule-based parse: {action} -> {target}")
                return Intent(
                    action=action,
                    target=target,
                    target_type=target_type,
                    raw_input=raw_input,
                    confidence=0.95,
                )

        # LLM fallback
        if self.use_llm_fallback and self.llm and world_snapshot:
            return self._llm_parse(raw_input, world_snapshot)

        # Unknown command
        return Intent(action="unknown", raw_input=raw_input, confidence=0.0)

    def _llm_parse(self, raw_input: str, world_snapshot: Dict) -> Intent:
        import json
        prompt = f"""Parse this player command from a text adventure game into a structured intent.

Command: "{raw_input}"

Current scene: {world_snapshot.get('scene_description', 'unknown location')}
Available characters: {world_snapshot.get('characters_nearby', [])}
Available objects: {world_snapshot.get('objects_nearby', [])}

Respond ONLY with JSON:
{{"action": "go|talk|take|drop|examine|look|wait|other", "target": "target name or null", "target_type": "location|character|object|null"}}"""

        try:
            result = self.llm.complete(user=prompt, temperature=0.1, max_tokens=100)
            clean = result.strip()
            if "```" in clean:
                clean = clean.split("```")[1].replace("json", "").strip()
            data = json.loads(clean)
            return Intent(
                action=data.get("action", "unknown"),
                target=data.get("target"),
                target_type=data.get("target_type"),
                raw_input=raw_input,
                confidence=0.75,
            )
        except Exception as e:
            logger.warning(f"LLM parse failed: {e}")
            return Intent(action="unknown", raw_input=raw_input, confidence=0.0)
