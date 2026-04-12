"""
LLM Narration Engine — Dynamic scene generation for StoryWeaver Web UI.

Uses the local llama-server to generate rich, contextual narration
for player actions instead of static template text.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Optional, List, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── Import LLM client ─────────────────────────────────────────────────────
sys.path.insert(0, str(PROJECT_ROOT))
from storyweaver.models.llamacpp_client import LlamaCppClient


class LLMNarrator:
    """Generates dynamic narration using local LLM."""

    def __init__(
        self,
        llm: Optional[LlamaCppClient] = None,
        world_bundle=None,
        model: str = "Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf",
        base_url: str = "http://localhost:8090/v1",
    ):
        self.llm = llm or LlamaCppClient(base_url=base_url, model=model)
        self.bundle = world_bundle
        self._context_cache = ""

    def set_bundle(self, bundle):
        """Set the world bundle for context."""
        self.bundle = bundle
        self._context_cache = ""

    def _build_world_context(self) -> str:
        """Build a compact context string from the world bundle."""
        if self._context_cache:
            return self._context_cache

        if not self.bundle:
            return ""

        lines = [f"World: {self.bundle.source_title} by {self.bundle.source_author}"]

        # Locations
        lines.append("\nLOCATIONS:")
        for lid, loc in self.bundle.locations.items():
            chars_here = []
            if loc.characters_present:
                for c in loc.characters_present:
                    if c in self.bundle.characters:
                        chars_here.append(self.bundle.characters[c].name)
            char_str = f" [{', '.join(chars_here)}]" if chars_here else ""
            lines.append(f"- {loc.name}: {loc.description or 'Unknown'}{char_str}")

        # Characters
        lines.append("\nCHARACTERS:")
        for cid, char in self.bundle.characters.items():
            loc_name = "?"
            if char.current_location and char.current_location in self.bundle.locations:
                loc_name = self.bundle.locations[char.current_location].name
            lines.append(f"- {char.name} ({'major' if char.is_major else 'minor'}): {char.description or 'A character'} [at {loc_name}]")

        # Events
        if self.bundle.canon_events:
            lines.append(f"\nCANON EVENTS: {len(self.bundle.canon_events)} story beats")
            for i, evt in enumerate(self.bundle.canon_events[:5]):
                evt_text = evt.get("summary", evt.get("description", "")) if isinstance(evt, dict) else str(evt)
                lines.append(f"  {i+1}. {evt_text[:80]}")

        # Themes
        if self.bundle.gravity_map:
            lines.append(f"\nTHEMES: {len(self.bundle.gravity_map)} thematic anchors")

        self._context_cache = "\n".join(lines)
        return self._context_cache

    def _make_system_prompt(self) -> str:
        """Build the system prompt for the narrator LLM."""
        return (
            "You are the narrator of an interactive fiction game based on a classic story. "
            "Write vivid, atmospheric scene descriptions in the style of literary fiction. "
            "Use sensory details, mood, and subtle foreshadowing. "
            "Keep responses concise (2-4 paragraphs, max 300 words). "
            "Write in second person ('you see', 'you hear'). "
            "Do NOT address the player directly as 'the player' — immerse them in the world. "
            "Maintain the tone and themes of the original story."
        )

    def generate_scene(
        self,
        location_id: str,
        action: str = "look",
        context: Optional[Dict] = None,
        temperature: float = 0.75,
        max_tokens: int = 400,
    ) -> str:
        """Generate a dynamic scene description for the player's action.

        Args:
            location_id: The location the player is at
            action: The action taken ("look", "go", "examine", etc.)
            context: Additional context (visited locations, talked characters, etc.)
            temperature: LLM temperature (0.0-1.0)
            max_tokens: Maximum output tokens

        Returns:
            Generated scene text
        """
        world_ctx = self._build_world_context()

        location_name = location_id.replace("_", " ").title()
        if self.bundle and location_id in self.bundle.locations:
            location_name = self.bundle.locations[location_id].name

        # Build contextual info
        context_lines = []
        if context:
            if context.get("visited_locations"):
                context_lines.append(f"You have previously visited: {', '.join(context['visited_locations'][-5:])}")
            if context.get("talked_characters"):
                context_lines.append(f"You have spoken with: {', '.join(context['talked_characters'][-3:])}")
            if context.get("time_of_day"):
                context_lines.append(f"Time: {context['time_of_day']}")

        ctx_str = "\n".join(context_lines) if context_lines else ""

        action_prompts = {
            "look": (
                f"Describe what the player sees at {location_name}. "
                f"Include atmosphere, sounds, any characters present, and notable objects. "
                f"Make it feel alive and immersive.\n\n"
                f"Location context: {location_id}"
            ),
            "go": (
                f"The player arrives at {location_name} for {'the first time' if not context or not context.get('visited_locations') else 'another visit'}. "
                f"Describe the approach, the first impression, and what they see upon arrival.\n\n"
                f"Location: {location_id}"
            ),
            "examine": (
                f"The player examines something closely at {location_name}. "
                f"Describe the details they notice — textures, inscriptions, hidden meanings, "
                f"things missed at first glance. Make the examination reveal something about the world.\n\n"
                f"Location: {location_id}"
            ),
            "talk": (
                f"At {location_name}, the player engages in conversation. "
                f"Write the character's response with voice, gesture, and subtext. "
                f"Make it feel like a real person with their own agenda.\n\n"
                f"Location: {location_id}"
            ),
            "wait": (
                f"Time passes at {location_name}. "
                f"Describe what happens as the world turns — "
                f"ambient activity, distant events, the sense of time flowing.\n\n"
                f"Location: {location_id}"
            ),
            "default": (
                f"Something happens at {location_name}. "
                f"Describe the scene and its atmosphere.\n\n"
                f"Location: {location_id}"
            ),
        }

        user_prompt = action_prompts.get(action, action_prompts["default"])
        if ctx_str:
            user_prompt += f"\n\nPlayer context:\n{ctx_str}"

        user_prompt += f"\n\nWorld context:\n{world_ctx}"

        try:
            result = self.llm.complete(
                system=self._make_system_prompt(),
                user=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return result.strip()
        except Exception as e:
            # Fallback to static description
            if self.bundle and location_id in self.bundle.locations:
                loc = self.bundle.locations[location_id]
                return f"You are at **{loc.name}**.\n\n{loc.description or 'A place in the story.'}"
            return f"You are at {location_name}."

    def generate_dialogue(
        self,
        character_name: str,
        character_description: str,
        location_name: str,
        conversation_history: Optional[List[str]] = None,
        temperature: float = 0.8,
        max_tokens: int = 200,
    ) -> str:
        """Generate a dynamic dialogue response from a character.

        Args:
            character_name: Name of the speaking character
            character_description: Their description/psychology
            location_name: Where the conversation takes place
            conversation_history: Previous exchanges (optional)
            temperature: LLM temperature (higher = more creative)

        Returns:
            Character's response with narration
        """
        system = (
            f"You are {character_name}. {character_description or ''} "
            f"Respond in character — with personality, motivations, and voice. "
            f"You are currently at {location_name}. "
            f"Write your response as a mix of dialogue and action descriptions. "
            f"Use quotes for speech, and describe gestures and expressions. "
            f"Keep it under 150 words."
        )

        user = f"Respond as {character_name}. "
        if conversation_history:
            user += f"Recent conversation:\n{'\n'.join(conversation_history[-4:])}\n\n"
        user += f"What do you say?"

        try:
            result = self.llm.complete(
                system=system,
                user=user,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return result.strip()
        except Exception:
            return f"{character_name} regards you thoughtfully but has nothing to add right now."


# ── Module-level singleton ─────────────────────────────────────────────────
_narrator: Optional[LLMNarrator] = None


def get_narrator(
    llm=None,
    bundle=None,
    model: str = "Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf",
    base_url: str = "http://localhost:8090/v1",
) -> LLMNarrator:
    """Get or create the global narrator singleton."""
    global _narrator
    if _narrator is None:
        _narrator = LLMNarrator(llm=llm, world_bundle=bundle, model=model, base_url=base_url)
    elif bundle and _narrator.bundle is None:
        _narrator.set_bundle(bundle)
    return _narrator


def reset_narrator():
    """Reset the narrator (e.g., when switching worlds)."""
    global _narrator
    _narrator = None
