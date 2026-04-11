"""Narrative gravity and divergence tracking."""
from typing import Dict, List
from ..world.event import Event


class DivergenceTracker:
    def __init__(self, gravity_map: Dict[str, float]):
        self.gravity_map = gravity_map
        self.score: float = 0.0
        self._prevented_canon_events: List[str] = []
        self._triggered_divergent_events: List[str] = []

    def update(self, new_events: List[Event]) -> None:
        for event in new_events:
            if event.is_canon:
                # Canon event happened — slight reduction in divergence
                self.score = max(0.0, self.score - 0.01)
            elif not event.is_canon and event.gravity > 0.5:
                # High-gravity event was prevented — divergence increases
                self._diverge(event.gravity * 0.1)

    def _diverge(self, amount: float) -> None:
        self.score = min(1.0, self.score + amount)

    @property
    def is_fully_diverged(self) -> bool:
        return self.score >= 0.8
