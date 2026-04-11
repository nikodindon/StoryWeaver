"""
Gradio Web Interface for StoryWeaver.

Provides a browser-based text adventure interface for playing compiled worlds.

Usage:
    pip install -e ".[web]"
    python scripts/web_ui.py
    # Open http://localhost:7860
"""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Ensure storyweaver package is importable ───────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
import gradio as gr

# ── Import StoryWeaver components ─────────────────────────────────────────
from storyweaver.world.bundle import WorldBundle
from storyweaver.interaction.parser import IntentParser
from storyweaver.agents.base_agent import AgentAction

EXAMPLES_DIR = PROJECT_ROOT / "examples" / "worlds"

# ── Hand-crafted scene narratives for the demo world ───────────────────────
DEMO_SCENES = {
    "happy_prince": {
        "intro": (
            "The last of the swallows had flown south. The autumn wind swept "
            "through the city square as one small bird — left behind for love "
            "of a reed that would not speak to him — came to rest at the feet "
            "of a golden statue.\n\n"
            "You awaken at the base of the tall column. Above you, the Happy "
            "Prince stands gilded and silent, tears of mercury tracking down "
            "his golden cheeks."
        ),
        "look": (
            "A tall column rises from the center of the square. Atop it stands "
            "the statue of the Happy Prince, covered in gold leaf and sapphires. "
            "The square is grand but surrounded by narrow alleys where the poor live.\n\n"
            "The Swallow rests at the statue's feet."
        ),
        "go_city_square": "You are already in the City Square.",
        "go_sewing_room": (
            "You make your way through narrow alleys to a cramped, dark room. "
            "A young seamstress sits hunched over her work, embroidering "
            "passion-flowers on a satin gown. Her sick child lies feverish "
            "on a bed in the corner, asking for oranges."
        ),
        "go_garret": (
            "You climb the stairs to a cold attic under the eaves. A young "
            "playwright huddles over his desk, shivering, trying to finish "
            "a play. No fire has been lit."
        ),
        "go_balcony": (
            "You ascend to an elegant marble balcony. A beautiful young lady "
            "stands here, gazing at the stars with the Professor of "
            "Ornithology beside her. The world is beautiful from up here, "
            "if you don't look down."
        ),
        "talk_swallow": (
            "The Swallow looks up at you. \"I was going to Egypt,\" he says "
            "quietly. \"But the Prince asked me to stay for one night. "
            "And then one night became two, and now... now I find I cannot leave.\""
        ),
        "talk_happy_prince": (
            "The gilded lips move, though you hear no sound with your ears. "
            "A voice speaks in your mind: \"Little one, will you look out over "
            "my city and tell me what you see? From up here, I can see all "
            "the suffering, but I am too heavy to go down and help.\""
        ),
        "talk_seamstress": (
            "The seamstress startles. \"Oh — I'm sorry, I can barely look up "
            "from my work. The Queen needs this gown by tomorrow, and my boy... "
            "he keeps asking for oranges. I don't know where to find any.\""
        ),
        "talk_playwright": (
            "The playwright looks up, ink-stained fingers trembling. \"I'm "
            "frozen — the play is due tomorrow and I can't feel my hands. "
            "The theater manager says if I don't deliver, I'll never write "
            "for this city again.\""
        ),
        "examine_statue": (
            "The Happy Prince is magnificent. Fine gold leaf covers every "
            "surface. Two bright sapphires gleam for eyes, and a great red "
            "ruby glows in his sword-hilt. But up close, you can see the "
            "tracks of tears where the gold has worn thin."
        ),
        "examine_embroidery": (
            "Passion-flowers bloom across the satin — symbols of suffering "
            "embroidered onto a queen's gown. The irony is almost too much "
            "to bear."
        ),
        "examine_manuscript": (
            "Twelve pages of a dramatic play. The writing is vivid, the "
            "dialogue sharp — but it stops mid-scene, as if the writer's "
            "cold hands could hold the pen no longer."
        ),
        "default_narrate": "Nothing notable happens. The world waits.",
    }
}


# ── Game State ─────────────────────────────────────────────────────────────

class GameState:
    def __init__(self):
        self.bundle: Optional[WorldBundle] = None
        self.player_location: str = ""
        self.tick: int = 0
        self.history: List[Tuple[str, str]] = []  # (user_input, output)

    def reset(self):
        self.bundle = None
        self.player_location = ""
        self.tick = 0
        self.history = []


state = GameState()


# ── Helpers ────────────────────────────────────────────────────────────────

def get_available_worlds() -> List[str]:
    worlds = []
    if EXAMPLES_DIR.exists():
        for d in sorted(EXAMPLES_DIR.iterdir()):
            if d.is_dir() and (d / "bundle.json").exists():
                worlds.append(d.name)
    return worlds


def get_scene_text(world_name: str, location_id: str) -> str:
    scenes = DEMO_SCENES.get(world_name, {})
    # Try location-based lookup
    for key, text in scenes.items():
        if key.startswith("go_") and key[3:] == location_id:
            return text
    return scenes.get("look", "You are somewhere unfamiliar.")


def get_location_id_from_name(name: str) -> str:
    if not state.bundle:
        return ""
    name_lower = name.lower()
    for lid, loc in state.bundle.locations.items():
        if loc.name.lower() == name_lower or lid == name_lower:
            return lid
    return name_lower.replace(" ", "_")


def build_world_info(world_name: str) -> str:
    if not state.bundle:
        return "No world loaded."

    bundle = state.bundle
    lines = [f"**{bundle.source_title}** by {bundle.source_author}", ""]
    lines.append(f"**Tick:** {state.tick}  |  **Location:** {state.player_location}")
    lines.append("")

    lines.append("### 🗺️ Locations")
    for loc in bundle.locations.values():
        marker = "📍" if loc.id == state.player_location else "·"
        chars = [bundle.characters[c].name for c in loc.characters_present if c in bundle.characters]
        char_str = f" — {', '.join(chars)}" if chars else ""
        lines.append(f"{marker} **{loc.name}**{char_str}")

    lines.append("")
    lines.append("### 👥 Characters")
    for cid, char in bundle.characters.items():
        loc_name = bundle.locations[char.current_location].name if char.current_location in bundle.locations else "?"
        lines.append(f"· **{char.name}** — at {loc_name}")

    lines.append("")
    lines.append("### 🎒 Objects")
    for oid, obj in bundle.objects.items():
        if obj.location_id == state.player_location:
            lines.append(f"· **{obj.name}** — {obj.description[:60]}...")

    return "\n".join(lines)


# ── Core game logic ────────────────────────────────────────────────────────

def process_command(user_input: str) -> Tuple[str, str, str]:
    """Process a player command. Returns (output, world_info, history)."""
    if not user_input.strip():
        history_text = format_history(state.history)
        return "", build_world_info(user_input), history_text

    raw = user_input.strip().lower()
    output = ""

    # Quit
    if raw in ("quit", "exit", "q"):
        output = "The world fades around you...\n\nFarewell."
        state.history.append((user_input, output))
        history_text = format_history(state.history)
        return output, build_world_info(raw), history_text

    # Help
    if raw in ("help", "h", "?"):
        output = (
            "**Available Commands:**\n\n"
            "- `go <place>` — Move to a location\n"
            "- `north`, `south`, `east`, `west`, `n`, `s`, `e`, `w`\n"
            "- `look` / `l` — Look around\n"
            "- `talk to <character>` — Speak with someone\n"
            "- `examine <target>` — Inspect something\n"
            "- `inventory` / `i` — See what's around\n"
            "- `wait` / `w` — Pass time\n"
            "- `help` / `quit`\n"
        )
        state.history.append((user_input, output))
        history_text = format_history(state.history)
        return output, build_world_info(raw), history_text

    # Look
    if raw in ("look", "l"):
        output = get_scene_text("happy_prince", state.player_location) if state.bundle else "No world loaded."
        state.tick += 1
        state.history.append((user_input, output))
        history_text = format_history(state.history)
        return output, build_world_info(raw), history_text

    # Inventory
    if raw in ("inventory", "i", "inv"):
        if not state.bundle:
            output = "No world loaded."
        else:
            objs = [state.bundle.objects[o].name for o in state.bundle.locations.get(state.player_location, type("L", (), {"objects": []})()).objects if o in state.bundle.objects]
            output = f"Objects here: {', '.join(objs)}" if objs else "Nothing notable here."
        state.history.append((user_input, output))
        history_text = format_history(state.history)
        return output, build_world_info(raw), history_text

    # Wait
    if raw in ("wait", "w", "rest"):
        state.tick += 1
        output = "Time passes. The world turns without you."
        state.history.append((user_input, output))
        history_text = format_history(state.history)
        return output, build_world_info(raw), history_text

    # Movement
    go_prefixes = ["go ", "move ", "walk ", "travel ", "head "]
    direction_map = {
        "north": "city_square", "south": "sewing_room",
        "east": "garret", "west": "balcony",
        "n": "city_square", "s": "sewing_room",
        "e": "garret", "w": "balcony",
    }

    for prefix in go_prefixes:
        if raw.startswith(prefix):
            dest = raw[len(prefix):].strip()
            dest_id = get_location_id_from_name(dest)
            if dest_id in (state.bundle.locations if state.bundle else {}):
                state.player_location = dest_id
                state.tick += 1
                output = get_scene_text("happy_prince", dest_id)
                state.history.append((user_input, output))
                history_text = format_history(state.history)
                return output, build_world_info(raw), history_text

    # Directions
    if raw in direction_map:
        dest_id = direction_map[raw]
        if dest_id in (state.bundle.locations if state.bundle else {}):
            state.player_location = dest_id
            state.tick += 1
            output = get_scene_text("happy_prince", dest_id)
            state.history.append((user_input, output))
            history_text = format_history(state.history)
            return output, build_world_info(raw), history_text

    # Talk
    talk_prefixes = ["talk to ", "speak to ", "ask ", "say to "]
    for prefix in talk_prefixes:
        if raw.startswith(prefix):
            target = raw[len(prefix):].strip()
            char_id = get_char_id(target)
            scenes = DEMO_SCENES.get("happy_prince", {})
            talk_key = f"talk_{char_id}" if char_id else None
            if talk_key and talk_key in scenes:
                output = scenes[talk_key]
            else:
                output = f"No one named '{target}' is here."
            state.tick += 1
            state.history.append((user_input, output))
            history_text = format_history(state.history)
            return output, build_world_info(raw), history_text

    # Examine
    examine_prefixes = ["examine ", "look at ", "inspect ", "read "]
    for prefix in examine_prefixes:
        if raw.startswith(prefix):
            target = raw[len(prefix):].strip()
            output = _find_examine_output(target)
            state.tick += 1
            state.history.append((user_input, output))
            history_text = format_history(state.history)
            return output, build_world_info(raw), history_text

    # Default
    output = "I don't understand that command. Try `help` for available commands."
    state.history.append((user_input, output))
    history_text = format_history(state.history)
    return output, build_world_info(raw), history_text


def get_char_id(name: str) -> str:
    if not state.bundle:
        return ""
    name_lower = name.lower()
    for cid, char in state.bundle.characters.items():
        if char.name.lower() == name_lower or cid == name_lower:
            return cid
    return name_lower.replace(" ", "_")


def _find_examine_output(target: str) -> str:
    scenes = DEMO_SCENES.get("happy_prince", {})
    target_lower = target.lower()

    # Check known examine targets
    examine_map = {
        "statue": "examine_statue",
        "prince": "examine_statue",
        "embroidery": "examine_embroidery",
        "manuscript": "examine_manuscript",
        "play": "examine_manuscript",
    }
    for key, scene_key in examine_map.items():
        if key in target_lower:
            return scenes.get(scene_key, scenes.get("default_narrate", "Nothing happens."))

    # Check characters
    char_id = get_char_id(target)
    if char_id and state.bundle:
        char = state.bundle.characters.get(char_id)
        if char:
            return f"You study {char.name}. {char.description}"

    # Check objects
    if state.bundle:
        for oid, obj in state.bundle.objects.items():
            if obj.name.lower() in target_lower or oid in target_lower:
                return f"You examine {obj.name}. {obj.description}"

    return scenes.get("default_narrate", "Nothing notable happens.")


def format_history(history: List[Tuple[str, str]]) -> str:
    parts = []
    for user_in, output in history:
        parts.append(f"**>** {user_in}\n\n{output}\n")
    return "\n---\n".join(parts)


# ── Load world ─────────────────────────────────────────────────────────────

def load_world(world_name: str) -> Tuple[str, str, str]:
    """Load a world and return (intro, world_info, history)."""
    world_dir = EXAMPLES_DIR / world_name
    bundle_path = world_dir / "bundle.json"

    if not bundle_path.exists():
        return f"World '{world_name}' not found.", "", ""

    state.bundle = WorldBundle.load(world_dir)
    state.player_location = "city_square"  # Default start
    state.tick = 0
    state.history = []

    scenes = DEMO_SCENES.get(world_name, {})
    intro = scenes.get("intro", f"You arrive in {world_name}.")

    return intro, build_world_info(world_name), ""


# ── Gradio App ─────────────────────────────────────────────────────────────

def create_app():
    worlds = get_available_worlds()

    with gr.Blocks(title="StoryWeaver", theme=gr.themes.Soft()) as app:
        gr.Markdown("# 📚 StoryWeaver")
        gr.Markdown("*Don't read the story. Enter it.*")

        with gr.Row():
            with gr.Column(scale=3):
                # World selector
                world_dropdown = gr.Dropdown(
                    choices=worlds, value=worlds[0] if worlds else None,
                    label="Select World", interactive=True,
                )
                load_btn = gr.Button("🚀 Load World", variant="primary")

                # Output
                output_box = gr.Textbox(
                    label="Narration", lines=8, interactive=False,
                    show_copy_button=True,
                )

                # Input
                input_box = gr.Textbox(
                    label="Your command", placeholder="Type a command... (try 'help')",
                    lines=2,
                )
                send_btn = gr.Button("Send", variant="primary")

            with gr.Column(scale=1):
                world_info = gr.Markdown("Select and load a world to begin.")

                # Quick actions
                gr.Markdown("### Quick Actions")
                with gr.Row():
                    look_btn = gr.Button("👁 Look")
                    wait_btn = gr.Button("⏳ Wait")
                with gr.Row():
                    go_n_btn = gr.Button("⬆ North")
                    go_s_btn = gr.Button("⬇ South")
                    go_e_btn = gr.Button("➡ East")
                    go_w_btn = gr.Button("⬅ West")

        # Wire up events
        def on_load(world_name):
            return load_world(world_name)

        load_btn.click(on_load, inputs=[world_dropdown], outputs=[output_box, world_info, gr.Textbox(visible=False)])

        def on_load_fixed(world_name):
            intro, info, _ = load_world(world_name)
            return intro, info, ""

        load_btn.click(
            on_load_fixed,
            inputs=[world_dropdown],
            outputs=[output_box, world_info],
        )

        def on_command(cmd):
            output, info, history = process_command(cmd)
            return output, info, "", gr.update(value=history)

        # Use a hidden textbox for history
        history_box = gr.Textbox(visible=False)

        send_btn.click(on_command, inputs=[input_box], outputs=[output_box, world_info, input_box, history_box])
        input_box.submit(on_command, inputs=[input_box], outputs=[output_box, world_info, input_box, history_box])

        # Quick action buttons
        quick_actions = {
            look_btn: "look",
            wait_btn: "wait",
            go_n_btn: "north",
            go_s_btn: "south",
            go_e_btn: "east",
            go_w_btn: "west",
        }
        for btn, cmd in quick_actions.items():
            btn.click(
                lambda c=cmd: on_command(c),
                outputs=[output_box, world_info, input_box, history_box],
            )

    return app


# ── Entry Point ────────────────────────────────────────────────────────────

def main():
    app = create_app()
    app.launch(share=False, server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    main()
