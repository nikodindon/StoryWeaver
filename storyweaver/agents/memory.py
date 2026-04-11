"""Per-agent memory system with vector retrieval."""
from __future__ import annotations
from typing import List
import json


class AgentMemory:
    """
    Two-tier memory:
    - episodic: full event log (runtime)
    - compressed: summarized chunks (when episodic grows large)
    """
    MAX_EPISODIC_EVENTS = 200

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self._episodic: List[str] = []
        self._compressed: List[str] = []
        self._discovered_facts: List[str] = []
        self._vector_store = None   # Initialized lazily

    def add_event(self, description: str) -> None:
        self._episodic.append(description)
        if len(self._episodic) > self.MAX_EPISODIC_EVENTS:
            self._compress_oldest()

    def add_discovered_fact(self, fact: str) -> None:
        self._discovered_facts.append(fact)

    def retrieve_relevant(self, query: str, k: int = 5) -> List[str]:
        """
        Retrieve most relevant memories for a given query.
        Falls back to recency-based retrieval if vector store not available.
        """
        # TODO: implement FAISS vector retrieval
        # Fallback: return most recent k events
        all_memories = self._compressed + self._episodic
        return all_memories[-k:] if len(all_memories) >= k else all_memories

    def format_discovered_knowledge(self) -> str:
        if not self._discovered_facts:
            return ""
        return "Things you've learned:\n" + "\n".join(f"- {f}" for f in self._discovered_facts)

    def _compress_oldest(self) -> None:
        """Compress the oldest 50 events into a summary chunk."""
        # TODO: LLM-based summarization
        chunk = self._episodic[:50]
        summary = f"[Earlier events: {len(chunk)} interactions summarized]"
        self._compressed.append(summary)
        self._episodic = self._episodic[50:]
