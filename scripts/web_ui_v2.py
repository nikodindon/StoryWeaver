"""
StoryWeaver Web UI v2 — Rich narration + Save/Load system.

Features:
- Dynamic LLM-generated scenes (falls back to static text if LLM unavailable)
- Save/Load game sessions to disk
- Rich world context panel
- Character dialogue with memory
- Auto-save every N actions

Usage:
    python scripts/web_ui_v2.py
    # Open http://localhost:7860
"""
from __future__ import annotations
import sys
import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# ── Ensure storyweaver package is importable ───────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import gradio as gr

# ── Import StoryWeaver components ─────────────────────────────────────────
from storyweaver.world.bundle import WorldBundle
from storyweaver.memory.game_state_manager import (
    GameStateManager,
    SaveState,
    create_save_state,
    get_state_manager,
)
from storyweaver.narrative.llm_narrator import get_narrator, reset_narrator

# ── Static fallback scenes (used when LLM is unavailable) ─────────────────
STATIC_SCENES = {
    "emperor": {
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
    }
}


# ── Game State ─────────────────────────────────────────────────────────────

class GameSession:
    """Active game session with save/load support."""
    def __init__(self):
        self.bundle: Optional[WorldBundle] = None
        self.world_name: str = ""
        self.player_location: str = ""
        self.tick: int = 0
        self.history: List[Dict[str, str]] = []  # [{"input": "...", "output": "..."}]
        self.inventory: List[str] = []
        self.player_name: str = "Traveler"
        self.visited_locations: List[str] = []
        self.talked_characters: List[str] = []
        self.examined_objects: List[str] = []
        self.divergence_score: float = 0.0
        self.conversation_history: Dict[str, List[str]] = {}  # char_id -> [messages]
        self.save_name: str = ""

    def reset(self):
        self.__init__()

    def to_save_state(self) -> SaveState:
        return create_save_state(
            save_name=self.save_name or f"{self.world_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            world_name=self.world_name,
            player_location=self.player_location,
            tick=self.tick,
            history=self.history,
            inventory=self.inventory,
            player_name=self.player_name,
            divergence=self.divergence_score,
            visited=self.visited_locations,
            talked=self.talked_characters,
            examined=self.examined_objects,
        )

    def load_from_save(self, save: SaveState):
        self.world_name = save.world_name
        self.player_location = save.player_location
        self.tick = save.tick
        self.history = save.history
        self.inventory = save.inventory
        self.player_name = save.player_name
        self.visited_locations = save.visited_locations
        self.talked_characters = save.talked_characters
        self.examined_objects = save.examined_objects
        self.divergence_score = save.divergence_score
        self.save_name = save.save_name


session = GameSession()


# ── Helpers ────────────────────────────────────────────────────────────────

def get_available_worlds() -> List[str]:
    """Find all compiled worlds."""
    worlds = []
    compiled_dir = PROJECT_ROOT / "data" / "compiled"
    if compiled_dir.exists():
        for d in sorted(compiled_dir.iterdir()):
            if d.is_dir() and (d / "bundle.json").exists():
                worlds.append(d.name)
    return worlds


def get_available_saves() -> List[str]:
    """List all save files."""
    mgr = get_state_manager()
    saves = mgr.list_saves()
    return [s["name"] for s in saves]


def build_world_info_markdown() -> str:
    """Build the side panel world info as Markdown."""
    if not session.bundle:
        return "No world loaded."

    bundle = session.bundle
    lines = [f"**{bundle.source_title}** by {bundle.source_author}", ""]
    lines.append(f"**👤 Player:** {session.player_name}")
    lines.append(f"**⏱️ Tick:** {session.tick}")
    lines.append(f"**📍 Location:** {session.player_location.replace('_', ' ').title()}")
    lines.append(f"**🔀 Divergence:** {session.divergence_score:.1%}")
    lines.append("")

    # Visited locations
    if session.visited_locations:
        lines.append("### 🗺️ Visited")
        for loc in session.visited_locations[-5:]:
            marker = "📍" if loc == session.player_location else "·"
            lines.append(f"{marker} {loc.replace('_', ' ').title()}")
        lines.append("")

    # Talked characters
    if session.talked_characters:
        lines.append("### 💬 Spoken with")
        for char in session.talked_characters[-5:]:
            lines.append(f"· {char}")
        lines.append("")

    # All locations in world
    lines.append("### 🌍 World Locations")
    for lid, loc in bundle.locations.items():
        marker = "📍" if lid == session.player_location else "·"
        visited_marker = "✅" if lid in session.visited_locations else ""
        chars = [bundle.characters[c].name for c in loc.characters_present if c in bundle.characters]
        char_str = f" — {', '.join(chars)}" if chars else ""
        lines.append(f"{marker} {visited_marker} **{loc.name}**{char_str}")

    lines.append("")
    lines.append("### 👥 Characters")
    for cid, char in bundle.characters.items():
        talked_marker = "💬" if cid in session.talked_characters else ""
        loc_name = bundle.locations[char.current_location].name if char.current_location in bundle.locations else "?"
        lines.append(f"· {talked_marker} **{char.name}** — at {loc_name}")

    lines.append("")
    lines.append(f"**📦 Objects:** {len(bundle.objects)}")
    lines.append(f"**📜 Canon Events:** {len(bundle.canon_events)}")
    lines.append(f"**🎭 Themes:** {len(bundle.gravity_map)}")

    return "\n".join(lines)


def build_history_markdown() -> str:
    """Build formatted history."""
    if not session.history:
        return "*No actions yet. Type a command to begin!*"

    parts = []
    for entry in session.history[-20:]:  # Last 20 entries
        inp = entry.get("input", "")
        out = entry.get("output", "")
        parts.append(f"**>** {inp}\n\n{out}")
    return "\n\n---\n\n".join(parts)


def get_location_id_from_name(name: str) -> str:
    if not session.bundle:
        return ""
    name_lower = name.lower()
    # Exact match first
    for lid in session.bundle.locations:
        if lid == name_lower:
            return lid
    # Then partial
    for lid in session.bundle.locations:
        if name_lower in lid or lid in name_lower:
            return lid
    # Then by location name
    for lid, loc in session.bundle.locations.items():
        if name_lower in loc.name.lower() or loc.name.lower() in name_lower:
            return lid
    return ""


def get_char_id(name: str) -> str:
    if not session.bundle:
        return ""
    name_lower = name.lower()
    for cid in session.bundle.characters:
        if cid == name_lower or name_lower in cid or cid in name_lower:
            return cid
    # By character name
    for cid, char in session.bundle.characters.items():
        if name_lower in char.name.lower() or char.name.lower() in name_lower:
            return cid
    return ""


# ── Core game logic ────────────────────────────────────────────────────────

def process_command(user_input: str, use_llm: bool = True) -> str:
    """Process a player command. Returns output text."""
    if not user_input.strip():
        return ""

    raw = user_input.strip().lower()
    output = ""

    # ── System commands ──
    if raw in ("quit", "exit", "q"):
        output = "The world fades around you...\n\nFarewell."
        session.history.append({"input": user_input, "output": output})
        return output

    if raw in ("help", "h", "?"):
        output = (
            "**Available Commands:**\n\n"
            "**Movement:**\n"
            "- `go <place>` — Move to a location\n"
            "- `look` / `l` — Look around\n\n"
            "**Interaction:**\n"
            "- `talk to <character>` — Speak with someone\n"
            "- `examine <target>` — Inspect something\n"
            "- `inventory` / `i` — See what you carry\n\n"
            "**Time:**\n"
            "- `wait` / `w` — Pass time\n\n"
            "**System:**\n"
            "- `help` — Show this message\n"
            "- `save <name>` — Save your game\n"
            "- `load <name>` — Load a saved game\n"
            "- `saves` — List available saves\n"
            "- `quit` — Exit the game"
        )
        session.history.append({"input": user_input, "output": output})
        return output

    # ── Save/Load commands ──
    if raw.startswith("save "):
        save_name = user_input.strip()[5:].strip()
        if not save_name:
            output = "Usage: `save <name>` (e.g., `save my_adventure`)"
            session.history.append({"input": user_input, "output": output})
            return output
        mgr = get_state_manager()
        session.save_name = save_name
        save_state = session.to_save_state()
        mgr.save(save_state)
        output = f"💾 Game saved as **'{save_name}'**."
        session.history.append({"input": user_input, "output": output})
        return output

    if raw.startswith("load "):
        save_name = user_input.strip()[5:].strip()
        mgr = get_state_manager()
        save = mgr.load(save_name)
        if not save:
            output = f"❌ No save found named **'{save_name}'**."
            session.history.append({"input": user_input, "output": output})
            return output

        # Load world bundle
        world_dir = PROJECT_ROOT / "data" / "compiled" / save.world_name
        if not (world_dir / "bundle.json").exists():
            output = f"❌ World '{save.world_name}' not found."
            session.history.append({"input": user_input, "output": output})
            return output

        session.reset()
        session.bundle = WorldBundle.load(world_dir)
        session.load_from_save(save)

        # Reinit narrator with new bundle
        reset_narrator()
        get_narrator(bundle=session.bundle)

        output = f"📂 Loaded **'{save_name}'**.\n\n📍 Location: {session.player_location.replace('_', ' ').title()}\n⏱️ Tick: {session.tick}"
        session.history.append({"input": user_input, "output": output})
        return output

    if raw == "saves":
        mgr = get_state_manager()
        saves = mgr.list_saves()
        if not saves:
            output = "📭 No saved games found."
            session.history.append({"input": user_input, "output": output})
            return output
        lines = ["**💾 Available Saves:**", ""]
        for s in saves:
            lines.append(f"· **{s['name']}** — {s['world']} (tick {s['tick']}, {s['location'].replace('_', ' ').title()})")
        output = "\n".join(lines)
        session.history.append({"input": user_input, "output": output})
        return output

    # ── Look ──
    if raw in ("look", "l"):
        if use_llm:
            try:
                narrator = get_narrator()
                context = {
                    "visited_locations": session.visited_locations,
                    "talked_characters": session.talked_characters,
                }
                output = narrator.generate_scene(
                    session.player_location,
                    action="look",
                    context=context,
                )
            except Exception:
                output = _static_look()
        else:
            output = _static_look()

        session.tick += 1
        if session.player_location not in session.visited_locations:
            session.visited_locations.append(session.player_location)
        session.history.append({"input": user_input, "output": output})
        return output

    # ── Inventory ──
    if raw in ("inventory", "i", "inv"):
        if not session.inventory:
            output = "You carry nothing but your wits — and perhaps your vanity."
        else:
            output = "You are carrying:\n" + "\n".join(f"· {item}" for item in session.inventory)
        session.history.append({"input": user_input, "output": output})
        return output

    # ── Wait ──
    if raw in ("wait", "w", "rest"):
        if use_llm:
            try:
                narrator = get_narrator()
                output = narrator.generate_scene(
                    session.player_location,
                    action="wait",
                )
            except Exception:
                output = "Time passes. The world turns without you."
        else:
            output = "Time passes. The world turns without you."

        session.tick += 1
        session.history.append({"input": user_input, "output": output})
        return output

    # ── Movement ──
    go_prefixes = ["go ", "move ", "walk ", "travel ", "head to ", "head "]
    for prefix in go_prefixes:
        if raw.startswith(prefix):
            dest = raw[len(prefix):].strip()
            dest_id = get_location_id_from_name(dest)

            if not dest_id:
                output = f"You cannot find a place called '{dest}'.\n\nAvailable locations:\n" + \
                    "\n".join(f"· {lid.replace('_', ' ').title()}" for lid in session.bundle.locations)
            else:
                is_first_visit = dest_id not in session.visited_locations
                session.player_location = dest_id
                session.tick += 1
                session.divergence_score += 0.02

                if use_llm:
                    try:
                        narrator = get_narrator()
                        context = {
                            "visited_locations": session.visited_locations,
                            "first_visit": is_first_visit,
                        }
                        output = narrator.generate_scene(
                            dest_id,
                            action="go",
                            context=context,
                        )
                    except Exception:
                        output = _static_go(dest_id)
                else:
                    output = _static_go(dest_id)

                if is_first_visit:
                    session.visited_locations.append(dest_id)

            session.history.append({"input": user_input, "output": output})
            return output

    # ── Talk ──
    talk_prefixes = ["talk to ", "speak to ", "talk with ", "ask "]
    for prefix in talk_prefixes:
        if raw.startswith(prefix):
            target = raw[len(prefix):].strip()
            char_id = get_char_id(target)

            if not char_id:
                output = f"No one named '{target}' is here.\n\nCharacters:\n" + \
                    "\n".join(f"· {c.name}" for c in session.bundle.characters.values())
            else:
                char = session.bundle.characters[char_id]
                if char_id not in session.talked_characters:
                    session.talked_characters.append(char_id)

                # Track conversation
                if char_id not in session.conversation_history:
                    session.conversation_history[char_id] = []

                if use_llm:
                    try:
                        narrator = get_narrator()
                        loc_name = "?"
                        if session.player_location in session.bundle.locations:
                            loc_name = session.bundle.locations[session.player_location].name

                        output = narrator.generate_dialogue(
                            character_name=char.name,
                            character_description=char.description or "",
                            location_name=loc_name,
                            conversation_history=session.conversation_history.get(char_id),
                        )
                        session.conversation_history[char_id].append(f"You: [player speaks]\n{char.name}: {output}")
                    except Exception:
                        output = f"{char.name} regards you thoughtfully."
                else:
                    output = f"{char.name} regards you thoughtfully."

                session.tick += 1
                session.divergence_score += 0.05

            session.history.append({"input": user_input, "output": output})
            return output

    # ── Examine ──
    examine_prefixes = ["examine ", "look at ", "inspect ", "read "]
    for prefix in examine_prefixes:
        if raw.startswith(prefix):
            target = raw[len(prefix):].strip()

            # Check objects first
            found_obj = None
            for oid, obj in session.bundle.objects.items():
                if target.lower() in oid.lower() or target.lower() in obj.name.lower():
                    found_obj = obj
                    break

            if found_obj:
                if found_obj.id not in session.examined_objects:
                    session.examined_objects.append(found_obj.id)

                if use_llm:
                    try:
                        narrator = get_narrator()
                        output = narrator.generate_scene(
                            session.player_location,
                            action="examine",
                            context={"target": found_obj.name, "description": found_obj.description},
                        )
                    except Exception:
                        output = f"You examine **{found_obj.name}**.\n\n{found_obj.description}"
                else:
                    output = f"You examine **{found_obj.name}**.\n\n{found_obj.description}"
            else:
                # Check characters
                char_id = get_char_id(target)
                if char_id:
                    char = session.bundle.characters[char_id]
                    output = f"You study **{char.name}**.\n\n{char.description or 'A character of the story.'}"
                else:
                    if use_llm:
                        try:
                            narrator = get_narrator()
                            output = narrator.generate_scene(
                                session.player_location,
                                action="examine",
                                context={"target": target},
                            )
                        except Exception:
                            output = f"You examine {target} carefully, but notice nothing unusual."
                    else:
                        output = f"You examine {target} carefully, but notice nothing unusual."

            session.tick += 1
            session.history.append({"input": user_input, "output": output})
            return output

    # ── Default ──
    output = "I don't understand that command. Try `help` for available commands."
    session.history.append({"input": user_input, "output": output})
    return output


# ── Static fallbacks ──────────────────────────────────────────────────────

def _static_look() -> str:
    if session.bundle and session.player_location in session.bundle.locations:
        loc = session.bundle.locations[session.player_location]
        return f"You are at **{loc.name}**.\n\n{loc.description or 'A place in the story.'}"
    return "You look around, but cannot determine where you are."


def _static_go(location_id: str) -> str:
    if session.bundle and location_id in session.bundle.locations:
        loc = session.bundle.locations[location_id]
        return f"You arrive at **{loc.name}**.\n\n{loc.description or 'A place in the story.'}"
    return f"You travel to {location_id.replace('_', ' ').title()}."


# ── Load world ─────────────────────────────────────────────────────────────

def load_world(world_name: str, use_llm: bool = True) -> Tuple[str, str, str]:
    """Load a world and return (intro, world_info, history)."""
    world_dir = PROJECT_ROOT / "data" / "compiled" / world_name
    bundle_path = world_dir / "bundle.json"

    if not bundle_path.exists():
        return f"❌ World '{world_name}' not found.", "", ""

    session.reset()
    session.bundle = WorldBundle.load(world_dir)
    session.world_name = world_name
    session.player_location = list(session.bundle.locations.keys())[0]
    session.save_name = f"{world_name}_session"

    # Init LLM narrator with this world
    reset_narrator()
    if use_llm:
        try:
            get_narrator(bundle=session.bundle)
        except Exception:
            pass  # Will fall back to static text

    intro = _get_intro(world_name)
    session.history.append({"input": "[Game started]", "output": intro})

    return intro, build_world_info_markdown(), build_history_markdown()


def _get_intro(world_name: str) -> str:
    """Get intro text — static for now, could be LLM-generated."""
    intros = {
        "emperor": (
            "Many years ago, there was an emperor who was so excessively fond of new "
            "clothes that he spent all his money on dress.\n\n"
            "Today, two strangers have arrived in the capital, claiming to be weavers "
            "who can create the most magnificent fabric ever seen — fabric that remains "
            "invisible to anyone unfit for their office or extraordinarily simple in character.\n\n"
            "You find yourself in the emperor's court as the story unfolds..."
        ),
    }
    return intros.get(world_name, f"You arrive in {world_name}. The story awaits.")


# ── Auto-save ──────────────────────────────────────────────────────────────

def autosave_if_needed():
    """Auto-save every 10 actions."""
    if len(session.history) % 10 == 0 and session.history:
        mgr = get_state_manager()
        save_state = session.to_save_state()
        mgr.autosave(save_state)


# ── Gradio App ─────────────────────────────────────────────────────────────

def create_app():
    worlds = get_available_worlds()

    with gr.Blocks(title="StoryWeaver v2") as app:
        gr.Markdown("# 👑 StoryWeaver v2")
        gr.Markdown("*Rich narration + Save/Load system*")

        # ── World selection ──
        with gr.Row():
            world_dropdown = gr.Dropdown(
                choices=worlds, value=worlds[0] if worlds else None,
                label="Select World", interactive=True,
            )
            llm_toggle = gr.Checkbox(
                value=True, label="Use LLM Narration",
                info="Generate dynamic scenes with AI (slower but richer)"
            )
            load_btn = gr.Button("🚀 Load World", variant="primary")

        # ── Main game area ──
        with gr.Row():
            with gr.Column(scale=3):
                # History
                history_box = gr.Markdown(
                    "*Load a world to begin your adventure.*",
                    elem_classes=["history-box"],
                )

                # Input
                input_box = gr.Textbox(
                    label="Your command",
                    placeholder="Type a command... (try 'help')",
                    lines=2,
                )
                with gr.Row():
                    send_btn = gr.Button("Send", variant="primary")
                    clear_btn = gr.Button("Clear History")

                # Quick actions
                gr.Markdown("### ⚡ Quick Actions")
                with gr.Row():
                    look_btn = gr.Button("👁 Look")
                    wait_btn = gr.Button("⏳ Wait")
                    inv_btn = gr.Button("🎒 Inventory")
                    help_btn = gr.Button("❓ Help")

                with gr.Row():
                    save_btn = gr.Button("💾 Save Game")
                    saves_list_btn = gr.Button("📂 List Saves")
                    load_save_btn = gr.Button("📥 Load Save")

            with gr.Column(scale=1):
                world_info = gr.Markdown(
                    "Select and load a world to begin.",
                    elem_classes=["world-info"],
                )

                gr.Markdown("### 🎭 Characters Present")
                char_info = gr.Markdown("*No world loaded*")

        # ── Event handlers ──

        def on_load(world_name, use_llm):
            intro, info, history = load_world(world_name, use_llm=use_llm)
            return intro, info, history

        load_btn.click(
            on_load,
            inputs=[world_dropdown, llm_toggle],
            outputs=[history_box, world_info, history_box],
        )

        def on_command(cmd, use_llm):
            if not session.bundle:
                return "Load a world first!", build_world_info_markdown(), build_history_markdown()

            output = process_command(cmd, use_llm=use_llm)
            autosave_if_needed()
            return output, build_world_info_markdown(), build_history_markdown()

        send_btn.click(
            on_command,
            inputs=[input_box, llm_toggle],
            outputs=[history_box, world_info, history_box],
        )
        input_box.submit(
            on_command,
            inputs=[input_box, llm_toggle],
            outputs=[history_box, world_info, history_box],
        )

        # Quick actions — each button triggers its command with the LLM toggle value
        def make_quick_action(cmd):
            def handler(use_llm):
                if not session.bundle:
                    return "Load a world first!", build_world_info_markdown(), build_history_markdown()
                output = process_command(cmd, use_llm=use_llm)
                autosave_if_needed()
                return output, build_world_info_markdown(), build_history_markdown()
            return handler

        look_btn.click(make_quick_action("look"), inputs=[llm_toggle], outputs=[history_box, world_info, history_box])
        wait_btn.click(make_quick_action("wait"), inputs=[llm_toggle], outputs=[history_box, world_info, history_box])
        inv_btn.click(make_quick_action("inventory"), inputs=[llm_toggle], outputs=[history_box, world_info, history_box])
        help_btn.click(make_quick_action("help"), inputs=[llm_toggle], outputs=[history_box, world_info, history_box])

        # Save/Load buttons
        def do_save():
            if not session.bundle:
                return "No world loaded."
            mgr = get_state_manager()
            save_state = session.to_save_state()
            mgr.save(save_state)
            return f"💾 Saved as **'{session.save_name}'**."

        save_btn.click(do_save, outputs=[history_box])

        def list_saves():
            mgr = get_state_manager()
            saves = mgr.list_saves()
            if not saves:
                return "📭 No saved games."
            lines = ["**💾 Available Saves:**", ""]
            for s in saves:
                lines.append(f"· **{s['name']}** — tick {s['tick']}, at {s['location'].replace('_', ' ').title()}")
            return "\n".join(lines)

        saves_list_btn.click(list_saves, outputs=[history_box])

        def do_load_save():
            # Load most recent save for this world
            mgr = get_state_manager()
            saves = mgr.list_saves()
            if not saves:
                return "📭 No saves found."
            # Find save matching current world
            for s in saves:
                if s.get("world") == session.world_name:
                    save = mgr.load(s["name"])
                    if save:
                        world_dir = PROJECT_ROOT / "data" / "compiled" / save.world_name
                        session.bundle = WorldBundle.load(world_dir)
                        session.load_from_save(save)
                        reset_narrator()
                        get_narrator(bundle=session.bundle)
                        return f"📂 Loaded **{s['name']}**."
            return f"📂 Loaded most recent save: **{saves[0]['name']}**."

        load_save_btn.click(do_load_save, outputs=[history_box])

        clear_btn.click(
            lambda: ("*History cleared.*", build_world_info_markdown(), "*History cleared.*"),
            outputs=[history_box, world_info, history_box],
        )

    return app


# ── Entry Point ────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("  StoryWeaver Web UI v2 — Rich Narration + Save/Load")
    print("=" * 60)
    print("\n  Open http://localhost:7860 in your browser\n")
    print("  Features:")
    print("    🎭  Dynamic LLM-generated scenes")
    print("    💾  Save/Load game sessions")
    print("    📋  Rich world context panel")
    print("    💬  Character dialogue with memory")
    print("    🔄  Auto-save every 10 actions")
    print("\n" + "=" * 60 + "\n")

    app = create_app()
    app.launch(
        share=False, server_name="127.0.0.1", server_port=7860,
        theme=gr.themes.Soft(),
        css="""
        .history-box {
            background: #1e1e2e !important;
            color: #cdd6f4 !important;
            padding: 12px !important;
            border-radius: 8px !important;
            border: 1px solid #45475a !important;
            min-height: 120px !important;
            max-height: 300px !important;
            overflow-y: auto !important;
        }
        .history-box * { color: #cdd6f4 !important; }
        .history-box strong { color: #f9e2af !important; }
        .history-box hr { border-color: #585b70 !important; }

        .world-info {
            background: #1e1e2e !important;
            color: #cdd6f4 !important;
            padding: 12px !important;
            border-radius: 8px !important;
            border: 1px solid #45475a !important;
            max-height: 400px !important;
            overflow-y: auto !important;
            line-height: 1.6 !important;
        }
        .world-info * { color: #cdd6f4 !important; }
        .world-info strong { color: #a6e3a1 !important; }
        .world-info h3 { color: #89b4fa !important; margin-top: 8px !important; }

        .char-box {
            background: #1e1e2e !important;
            color: #cdd6f4 !important;
            padding: 12px !important;
            border-radius: 8px !important;
            border: 1px solid #45475a !important;
        }
        """
    )


if __name__ == "__main__":
    main()
