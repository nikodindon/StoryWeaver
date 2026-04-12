"""
Game State Manager — Save/Load system for StoryWeaver sessions.

Manages persistent game state across browser sessions.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAVES_DIR = PROJECT_ROOT / "data" / "saves"


@dataclass
class SaveState:
    """Serializable game state for a single session."""
    save_name: str
    world_name: str
    player_location: str
    tick: int
    history: List[Dict[str, str]]  # [{"input": "...", "output": "..."}]
    inventory: List[str] = field(default_factory=list)
    player_name: str = "Traveler"
    divergence_score: float = 0.0
    visited_locations: List[str] = field(default_factory=list)
    talked_characters: List[str] = field(default_factory=list)
    examined_objects: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SaveState":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class GameStateManager:
    """Manages save/load operations for game sessions."""

    def __init__(self, saves_dir: Optional[Path] = None):
        self.saves_dir = saves_dir or SAVES_DIR
        self.saves_dir.mkdir(parents=True, exist_ok=True)

    def _save_path(self, name: str) -> Path:
        """Get path for a save file."""
        safe_name = name.replace(" ", "_").lower()
        return self.saves_dir / f"{safe_name}.json"

    def save(self, state: SaveState) -> Path:
        """Save game state to disk."""
        path = self._save_path(state.save_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)
        return path

    def load(self, name: str) -> Optional[SaveState]:
        """Load a saved game. Returns None if not found."""
        path = self._save_path(name)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return SaveState.from_dict(data)

    def delete(self, name: str) -> bool:
        """Delete a save. Returns True if deleted."""
        path = self._save_path(name)
        if path.exists():
            path.unlink()
            return True
        return False

    def list_saves(self) -> List[Dict[str, str]]:
        """List all available saves with metadata."""
        saves = []
        for p in self.saves_dir.glob("*.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                saves.append({
                    "name": data.get("save_name", p.stem),
                    "world": data.get("world_name", "?"),
                    "tick": data.get("tick", 0),
                    "location": data.get("player_location", "?"),
                    "updated_at": data.get("updated_at", "?"),
                    "file_size": p.stat().st_size,
                })
            except Exception:
                saves.append({"name": p.stem, "error": "corrupted"})
        return sorted(saves, key=lambda x: x.get("updated_at", ""), reverse=True)

    def autosave(self, state: SaveState) -> Path:
        """Autosave — overwrites the same file each time."""
        return self.save(state)


# ── Global instance ────────────────────────────────────────────────────────
_state_manager = GameStateManager()


def get_state_manager() -> GameStateManager:
    """Get the global state manager singleton."""
    return _state_manager


def create_save_state(
    save_name: str,
    world_name: str,
    player_location: str,
    tick: int,
    history: List[Dict[str, str]],
    inventory: Optional[List[str]] = None,
    player_name: str = "Traveler",
    divergence: float = 0.0,
    visited: Optional[List[str]] = None,
    talked: Optional[List[str]] = None,
    examined: Optional[List[str]] = None,
) -> SaveState:
    """Factory function to create a new save state."""
    return SaveState(
        save_name=save_name,
        world_name=world_name,
        player_location=player_location,
        tick=tick,
        history=history,
        inventory=inventory or [],
        player_name=player_name,
        divergence_score=divergence,
        visited_locations=visited or [],
        talked_characters=talked or [],
        examined_objects=examined or [],
    )
