"""
Gradio Web Interface for StoryWeaver — Emperor Demo.

Provides a browser-based text adventure interface for the compiled Emperor world.

Usage:
    python scripts/web_ui_emperor.py
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

# ── Hand-crafted scene narratives for the Emperor world ────────────────────
EMPEROR_SCENES = {
    "intro": (
        "Many years ago, there was an emperor who was so excessively fond of new "
        "clothes that he spent all his money on dress. He cared nothing for his "
        "soldiers, the theater, or hunting — except for opportunities to display "
        "his new outfits.\n\n"
        "Today, two strangers have arrived in the capital, claiming to be weavers "
        "who can create the most magnificent fabric ever seen — fabric that remains "
        "invisible to anyone unfit for their office or extraordinarily simple in character."
    ),
    "look": (
        "The grand hall echoes with the sound of empty looms clacking. The two "
        "weavers gesture proudly at the bare frames, asking for more silk and gold "
        "thread. The emperor's ministers nod approvingly at the magnificent cloth "
        "that only they can see.\n\n"
        "You stand among the courtiers, uncertain whether you can see the fabric or not."
    ),
    "go_throne_room": (
        "You enter the emperor's throne room — though calling it that seems generous. "
        "It's really just a large wardrobe with a mirror. The emperor stands before it, "
        "trying on his seventh coat of the day.\n\n"
        "\"Do I look wise enough for this new cloth?\" he mutters to himself."
    ),
    "go_weavers_hall": (
        "The weavers' workshop is filled with empty looms and piles of stolen silk. "
        "The two impostors work busily, their hands moving through empty air as they "
        "pretend to weave invisible patterns.\n\n"
        "\"Ah, a visitor! Tell us — do you see the beautiful colors?\""
    ),
    "go_city_streets": (
        "The streets of the capital buzz with rumors. Everyone talks of the wonderful "
        "new fabric that will reveal fools from the wise. Shopkeepers peer nervously at "
        "their customers, wondering who among them is unfit for their position."
    ),
    "go_procession_route": (
        "The grand avenue stretches before you, lined with balconies where citizens "
        "will soon gather to see the emperor's new clothes. The canopy poles stand "
        "ready, waiting for someone to carry them."
    ),
    "talk_emperor": (
        "The emperor adjusts his collar nervously. \"I must see the cloth myself, "
        "of course. Though... what if I cannot see it? No, no — I am the emperor! "
        "Surely I am not a simpleton. Still... perhaps I should send the minister first.\""
    ),
    "talk_weavers": (
        "The two weavers exchange a knowing glance. \"Your Excellency, the pattern is "
        "exquisite! The colors — the elegance! Only the most sophisticated eye could "
        "appreciate such subtlety. More silk, please, and the finest gold thread...\""
    ),
    "talk_minister": (
        "The old minister strokes his beard thoughtfully. \"Between us? I saw... well, "
        "I saw what I was expected to see. The looms were empty, but one cannot admit "
        "such a thing. The emperor would think me unfit for office. Best to praise the "
        "fabric loudly and ask no questions.\""
    ),
    "talk_child": (
        "The little tugs at your sleeve. \"What's everyone so excited about? I don't "
        "see any clothes. Is everyone else pretending?\" The child's eyes are wide with "
        "innocent confusion."
    ),
    "examine_looms": (
        "The looms are completely, utterly empty. No thread, no fabric, nothing. "
        "Yet the weavers gesture at them with the enthusiasm of master craftsmen, "
        "and the courtiers nod as if seeing the most beautiful cloth ever woven."
    ),
    "examine_procession_canopy": (
        "The ceremonial canopy stands ready — four poles connected by rich fabric, "
        "meant to be carried above the emperor during the procession. The lords of "
        "the bedchamber practice lifting invisible weight with great concentration."
    ),
    "examine_mirror": (
        "A tall looking glass stands in the corner of the wardrobe-room. Its surface "
        "shows only what is truly there — no invisible cloth, no imaginary splendor. "
        "Perhaps it is the most honest object in the entire empire."
    ),
    "default_narrate": "Nothing notable happens. The procession approaches.",
}


# ── Game State ─────────────────────────────────────────────────────────────

class GameState:
    def __init__(self):
        self.bundle: Optional[WorldBundle] = None
        self.player_location: str = ""
        self.tick: int = 0
        self.history: List[Tuple[str, str]] = []

    def reset(self):
        self.bundle = None
        self.player_location = ""
        self.tick = 0
        self.history = []


state = GameState()


# ── Helpers ────────────────────────────────────────────────────────────────

def get_scene_text(location_id: str) -> str:
    """Get narrative text for a location."""
    if not state.bundle:
        return "No world loaded."
    
    scenes = EMPEROR_SCENES
    # Try direct lookup
    for key, text in scenes.items():
        if key.startswith("go_") and key[3:] == location_id:
            return text
    
    # Fallback: use location description from bundle
    if location_id in state.bundle.locations:
        loc = state.bundle.locations[location_id]
        return f"You are at **{loc.name}**.\n\n{loc.description or 'A place in the emperor\'s realm.'}"
    
    return scenes.get("look", "You are somewhere unfamiliar.")


def get_location_id_from_name(name: str) -> str:
    if not state.bundle:
        return ""
    name_lower = name.lower()
    for lid, loc in state.bundle.locations.items():
        if loc.name.lower() == name_lower or lid == name_lower:
            return lid
    return name_lower.replace(" ", "_")


def build_world_info() -> str:
    if not state.bundle:
        return "No world loaded."

    bundle = state.bundle
    lines = [f"**{bundle.source_title}** by {bundle.source_author}", ""]
    lines.append(f"**Tick:** {state.tick}  |  **Location:** {state.player_location}")
    lines.append("")

    lines.append("### 🗺️ Locations")
    for lid, loc in bundle.locations.items():
        marker = "📍" if lid == state.player_location else "·"
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
        lines.append(f"· **{obj.name}** — {obj.description[:60]}...")

    lines.append("")
    lines.append(f"**Canon Events:** {len(bundle.canon_events)}")
    lines.append(f"**Gravity Map:** {len(bundle.gravity_map)} thematic anchors")

    return "\n".join(lines)


def format_history(history: List[Tuple[str, str]]) -> str:
    parts = []
    for user_in, output in history:
        parts.append(f"**>** {user_in}\n\n{output}\n")
    return "\n---\n".join(parts)


def get_char_id(name: str) -> str:
    if not state.bundle:
        return ""
    name_lower = name.lower()
    for cid, char in state.bundle.characters.items():
        if char.name.lower() == name_lower or cid == name_lower:
            return cid
    return name_lower.replace(" ", "_")


def _find_examine_output(target: str) -> str:
    target_lower = target.lower()

    # Check known examine targets
    for key in EMPEROR_SCENES:
        if key.startswith("examine_") and key[8:] in target_lower:
            return EMPEROR_SCENES[key]

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

    return EMPEROR_SCENES.get("default_narrate", "Nothing notable happens.")


# ── Core game logic ────────────────────────────────────────────────────────

def process_command(user_input: str) -> Tuple[str, str]:
    """Process a player command. Returns (output, world_info)."""
    if not user_input.strip():
        return "", build_world_info()

    raw = user_input.strip().lower()
    output = ""

    # Quit
    if raw in ("quit", "exit", "q"):
        output = "The world fades around you...\n\nFarewell."
        state.history.append((user_input, output))
        return output, build_world_info()

    # Help
    if raw in ("help", "h", "?"):
        output = (
            "**Available Commands:**\n\n"
            "- `go <place>` — Move to a location\n"
            "- `look` / `l` — Look around\n"
            "- `talk to <character>` — Speak with someone\n"
            "- `examine <target>` — Inspect something\n"
            "- `inventory` / `i` — See what's around\n"
            "- `wait` / `w` — Pass time\n"
            "- `help` / `quit`\n"
        )
        state.history.append((user_input, output))
        return output, build_world_info()

    # Look
    if raw in ("look", "l"):
        output = get_scene_text(state.player_location) if state.bundle else "No world loaded."
        state.tick += 1
        state.history.append((user_input, output))
        return output, build_world_info()

    # Inventory
    if raw in ("inventory", "i", "inv"):
        if not state.bundle:
            output = "No world loaded."
        else:
            output = "You carry nothing but your wits — and perhaps your vanity."
        state.history.append((user_input, output))
        return output, build_world_info()

    # Wait
    if raw in ("wait", "w", "rest"):
        state.tick += 1
        output = "Time passes. The weavers continue their empty work."
        state.history.append((user_input, output))
        return output, build_world_info()

    # Movement
    go_prefixes = ["go ", "move ", "walk ", "travel ", "head to "]
    for prefix in go_prefixes:
        if raw.startswith(prefix):
            dest = raw[len(prefix):].strip()
            dest_id = get_location_id_from_name(dest)
            
            # Try partial match
            if dest_id not in state.bundle.locations:
                for lid in state.bundle.locations:
                    if dest in lid or lid in dest:
                        dest_id = lid
                        break
            
            if dest_id in state.bundle.locations:
                state.player_location = dest_id
                state.tick += 1
                output = get_scene_text(dest_id)
                state.history.append((user_input, output))
                return output, build_world_info()
            else:
                output = f"You cannot find a place called '{dest}'. Try `look` to see available locations."
                state.history.append((user_input, output))
                return output, build_world_info()

    # Talk
    talk_prefixes = ["talk to ", "speak to ", "talk with ", "ask "]
    for prefix in talk_prefixes:
        if raw.startswith(prefix):
            target = raw[len(prefix):].strip()
            char_id = get_char_id(target)
            
            # Try partial match
            if char_id not in state.bundle.characters:
                for cid in state.bundle.characters:
                    if target in cid or cid in target:
                        char_id = cid
                        break
            
            talk_key = f"talk_{char_id}"
            if talk_key in EMPEROR_SCENES:
                output = EMPEROR_SCENES[talk_key]
            elif char_id in state.bundle.characters:
                char = state.bundle.characters[char_id]
                output = f"{char.name} regards you carefully. What would you like to ask?"
            else:
                output = f"No one named '{target}' is here."
            
            state.tick += 1
            state.history.append((user_input, output))
            return output, build_world_info()

    # Examine
    examine_prefixes = ["examine ", "look at ", "inspect ", "read "]
    for prefix in examine_prefixes:
        if raw.startswith(prefix):
            target = raw[len(prefix):].strip()
            output = _find_examine_output(target)
            state.tick += 1
            state.history.append((user_input, output))
            return output, build_world_info()

    # Default
    output = "I don't understand that command. Try `help` for available commands."
    state.history.append((user_input, output))
    return output, build_world_info()


# ── Load world ─────────────────────────────────────────────────────────────

def load_world() -> Tuple[str, str, str]:
    """Load the Emperor world and return (intro, world_info, history)."""
    world_dir = PROJECT_ROOT / "data" / "compiled" / "emperor"
    bundle_path = world_dir / "bundle.json"

    if not bundle_path.exists():
        return "World not found. Run the compilation first.", "", ""

    state.bundle = WorldBundle.load(world_dir)
    state.player_location = list(state.bundle.locations.keys())[0]  # Start at first location
    state.tick = 0
    state.history = []

    intro = EMPEROR_SCENES["intro"]
    return intro, build_world_info(), ""


# ── Gradio App ─────────────────────────────────────────────────────────────

def create_app():
    with gr.Blocks(title="StoryWeaver — The Emperor's New Clothes", theme=gr.themes.Soft()) as app:
        gr.Markdown("# 👑 StoryWeaver")
        gr.Markdown("*The Emperor's New Clothes — An Interactive World*")

        with gr.Row():
            with gr.Column(scale=3):
                # Output
                output_box = gr.Textbox(
                    label="Narration", lines=10, interactive=False,
                )

                # Input
                input_box = gr.Textbox(
                    label="Your command", placeholder="Type a command... (try 'help')",
                    lines=2,
                )
                send_btn = gr.Button("Send", variant="primary")

            with gr.Column(scale=1):
                world_info = gr.Markdown("Loading world...")

                # Quick actions
                gr.Markdown("### Quick Actions")
                look_btn = gr.Button("👁 Look")
                help_btn = gr.Button("❓ Help")
                
                gr.Markdown("### Talk To")
                talk_emperor_btn = gr.Button("The Emperor")
                talk_weavers_btn = gr.Button("The Weavers")
                talk_minister_btn = gr.Button("The Minister")
                
                gr.Markdown("### Examine")
                examine_looms_btn = gr.Button("The Looms")
                examine_mirror_btn = gr.Button("The Mirror")

        # Load world
        intro, info, _ = load_world()

        # Wire up events
        def on_command(cmd):
            output, world_inf = process_command(cmd)
            history = format_history(state.history)
            return output, world_inf, "", history

        send_btn.click(
            on_command,
            inputs=[input_box],
            outputs=[output_box, world_info, input_box, gr.Textbox(visible=False)]
        )
        input_box.submit(
            on_command,
            inputs=[input_box],
            outputs=[output_box, world_info, input_box, gr.Textbox(visible=False)]
        )

        # Quick action buttons
        def quick_action(cmd):
            output, world_inf = process_command(cmd)
            history = format_history(state.history)
            return output, world_inf, history

        look_btn.click(lambda: quick_action("look"), outputs=[output_box, world_info, gr.Textbox(visible=False)])
        help_btn.click(lambda: quick_action("help"), outputs=[output_box, world_info, gr.Textbox(visible=False)])
        talk_emperor_btn.click(lambda: quick_action("talk to emperor"), outputs=[output_box, world_info, gr.Textbox(visible=False)])
        talk_weavers_btn.click(lambda: quick_action("talk to weavers"), outputs=[output_box, world_info, gr.Textbox(visible=False)])
        talk_minister_btn.click(lambda: quick_action("talk to minister"), outputs=[output_box, world_info, gr.Textbox(visible=False)])
        examine_looms_btn.click(lambda: quick_action("examine looms"), outputs=[output_box, world_info, gr.Textbox(visible=False)])
        examine_mirror_btn.click(lambda: quick_action("examine mirror"), outputs=[output_box, world_info, gr.Textbox(visible=False)])

        # Set initial state
        app.load(lambda: intro, outputs=[output_box])
        app.load(lambda: info, outputs=[world_info])

    return app


# ── Entry Point ────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("  StoryWeaver Web UI — The Emperor's New Clothes")
    print("="*60)
    print("\n  Open http://localhost:7860 in your browser\n")
    print("  Commands: look, go <place>, talk to <char>, examine <thing>")
    print("  Type 'help' for full command list\n")
    print("="*60 + "\n")
    
    app = create_app()
    app.launch(share=False, server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    main()
