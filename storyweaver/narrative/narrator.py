"""
Narrator — Generates scene descriptions and action results.

The LLM's role here is purely stylistic: it takes structured world state
and renders it as prose. It does NOT decide what happens — the engine does.
"""
from __future__ import annotations
from typing import Dict, List, Optional
from pathlib import Path

from ..models.llm_client import LLMClient
from ..world.bundle import WorldBundle


SCENE_PROMPT = """You are the narrator of a story set in "{world_title}".

Current scene:
- Location: {location_name}
- Description: {location_description}
- Characters present: {characters_present}
- Objects visible: {objects_visible}
- Time: {time_of_day}
- Recent events: {recent_events}

Narrate this scene in 2-3 sentences. Match the style and tone of the original book.
Be atmospheric. Do not invent new events or characters. Only describe what is here.
"""

ACTION_RESULT_PROMPT = """You are the narrator of a story set in "{world_title}".

The player just did: {action_description}
Result: {result_description}

Recent events:
{recent_events}

Narrate the result in 1-3 sentences. Be vivid but concise.
"""


class Narrator:
    def __init__(self, llm: LLMClient, world: WorldBundle):
        self.llm = llm
        self.world = world

    def describe_scene(self, location_id: str, world_snapshot: Dict) -> str:
        location = self.world.locations.get(location_id)
        if not location:
            return "You are somewhere unfamiliar."

        chars = [self.world.characters[c].name
                 for c in location.characters_present
                 if c in self.world.characters]
        objects = [self.world.objects[o].name
                   for o in location.objects
                   if o in self.world.objects]

        prompt = SCENE_PROMPT.format(
            world_title=self.world.source_title,
            location_name=location.name,
            location_description=location.description,
            characters_present=", ".join(chars) if chars else "No one else",
            objects_visible=", ".join(objects) if objects else "Nothing notable",
            time_of_day=location.ambient_state.get("time_of_day", "daytime"),
            recent_events=world_snapshot.get("recent_events_summary", "Nothing notable recently."),
        )

        return self.llm.complete(user=prompt, temperature=0.75, max_tokens=200)

    def describe_action_result(self, action_desc: str, result_desc: str, world_snapshot: Dict) -> str:
        prompt = ACTION_RESULT_PROMPT.format(
            world_title=self.world.source_title,
            action_description=action_desc,
            result_description=result_desc,
            recent_events=world_snapshot.get("recent_events_summary", ""),
        )
        return self.llm.complete(user=prompt, temperature=0.75, max_tokens=150)

    def describe_dialogue(self, character_name: str, dialogue: str) -> str:
        return f'{character_name} says: "{dialogue}"'
