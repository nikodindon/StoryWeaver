"""Interactive game loop — the Zork-style CLI experience."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

HEADER = """
[bold cyan]╔══════════════════════════════════════════════╗
║        S T O R Y W E A V E R          ║
╚══════════════════════════════════════════════╝[/bold cyan]
"""


def run_play(world_name: str, session: str = None, mode: str = "canon") -> None:
    """Main interactive game loop."""
    from ..world.bundle import WorldBundle
    from ..simulation.engine import SimulationEngine
    from ..agents.base_agent import AgentAction
    from ..interaction.parser import IntentParser, Intent
    from ..models.llamacpp_client import LlamaCppClient
    from ..narrative.narrator import Narrator

    console.print(HEADER)

    # Load world bundle
    world_dir = Path("data") / "compiled" / world_name
    bundle_path = world_dir / "bundle.json"

    if not bundle_path.exists():
        console.print(f"[bold red]Error:[/bold red] World not found: {world_name}")
        console.print(f"  Looked for: {bundle_path}")
        console.print(f"\nCompile it first: [bold]storyweaver compile <book>[/bold]")
        raise SystemExit(1)

    console.print(f"Loading world: [bold]{world_name}[/bold]")
    world = WorldBundle.load(world_dir)
    console.print(f"  Title: {world.source_title}")
    console.print(f"  Locations: {len(world.locations)} | Characters: {len(world.characters)}\n")

    # Load config
    config_dir = Path(__file__).parent.parent.parent / "configs"
    with open(config_dir / "default.yaml") as f:
        config = yaml.safe_load(f)
    with open(config_dir / "models.yaml") as f:
        models_config = yaml.safe_load(f)

    # Initialize LLM client for narration
    base_url = models_config.get("llamacpp", {}).get("base_url", "http://localhost:8080/v1")
    try:
        llm = LlamaCppClient(base_url=base_url)
        # Test connection
        llm.complete(user="test", max_tokens=5, temperature=0.1)
        llm_enabled = True
        console.print("[dim]LLM connected — narrative descriptions enabled[/dim]\n")
    except Exception:
        llm = None
        llm_enabled = False
        console.print("[dim]LLM not available — using basic descriptions[/dim]\n")

    # Build agents
    from ..compiler.agent_builder import AgentBuilder
    agent_builder = AgentBuilder(llm) if llm else None
    agents: Dict = {}
    if agent_builder:
        psychology_data = {}  # Not available at runtime without extraction
        # Load agents from what we have — use minimal psychology
        for char_id, char in world.characters.items():
            from ..agents.character_agent import CharacterAgent, CharacterGoal
            from ..agents.psychology import PsychologyModel
            from ..agents.memory import AgentMemory

            psych = PsychologyModel()
            system_prompt = f"You are {char.name}. Act in character.\n{char.description}"
            agent = CharacterAgent(
                agent_id=char_id,
                name=char.name,
                psychology=psych,
                canonical_knowledge=[],
                initial_goals=[CharacterGoal(description="Explore and interact", priority=0.5)],
                system_prompt_template=system_prompt,
                llm_client=llm,
            )
            agent.current_location = char.current_location
            agents[char_id] = agent

    # Place characters at their starting locations
    for char_id, char in world.characters.items():
        if char.current_location and char.current_location in world.locations:
            loc = world.locations[char.current_location]
            if char_id not in loc.characters_present:
                loc.characters_present.append(char_id)

    # Initialize simulation engine
    engine = SimulationEngine(world, agents, config.get("simulation", {}))

    # Initialize narrator
    narrator = Narrator(llm, world) if llm else None

    # Initialize intent parser
    intent_parser = IntentParser(llm)

    # Determine player's starting location (first major character's location or first location)
    player_location = _find_player_start(world)
    console.print(f"You awaken at [bold]{world.locations[player_location].name}[/bold]\n")

    # Show opening scene
    _show_scene(world, player_location, narrator)

    # === GAME LOOP ===
    while True:
        try:
            raw_input = console.input("\n[bold green]>[/bold green] ").strip()
            if not raw_input:
                continue
            if raw_input.lower() in ("quit", "exit", "q"):
                console.print("\n[dim]The world fades around you...[/dim]")
                console.print("Farewell.")
                break

            # Parse intent
            snapshot = engine.get_world_snapshot()
            snapshot["scene_description"] = _get_scene_text(world, player_location)
            intent = intent_parser.parse(raw_input, snapshot)

            # Handle meta-commands
            if intent.action == "quit":
                console.print("\nFarewell.")
                break
            elif intent.action == "help":
                _show_help()
                continue
            elif intent.action == "look":
                _show_scene(world, player_location, narrator)
                continue
            elif intent.action == "inventory":
                _show_inventory(world, player_location)
                continue

            # Convert intent → AgentAction → process through engine
            action = _intent_to_action(intent, player_location)
            if action is None:
                console.print("[dim]I don't understand that command. Try 'help' for options.[/dim]")
                continue

            # Process through simulation
            events = engine.process_player_action(action)

            # Update player location if they moved
            if action.action_type == "move" and action.target_id in world.locations:
                player_location = action.target_id

            # Narrate the result
            _narrate_result(world, events, player_location, narrator)

        except (KeyboardInterrupt, EOFError):
            console.print("\nFarewell.")
            break


def _find_player_start(world) -> str:
    """Find a good starting location for the player."""
    # Prefer first location with some symbolic weight
    locations = list(world.locations.values())
    if not locations:
        raise RuntimeError("World has no locations!")
    return max(locations, key=lambda loc: loc.symbolic_weight).id


def _show_scene(world, location_id: str, narrator) -> None:
    """Display the current scene description."""
    loc = world.locations.get(location_id)
    if not loc:
        console.print("You are somewhere unfamiliar.")
        return

    chars_present = [
        world.characters[c].name
        for c in loc.characters_present
        if c in world.characters
    ]
    objects_visible = [
        world.objects[o].name
        for o in loc.objects
        if o in world.objects
    ]

    if narrator:
        try:
            scene_text = narrator.describe_scene(location_id, {
                "scene_description": _get_scene_text(world, location_id),
            })
            console.print(Markdown(scene_text))
        except Exception:
            console.print(f"[italic]{_get_scene_text(world, location_id)}[/italic]")
    else:
        console.print(f"[italic]{_get_scene_text(world, location_id)}[/italic]")

    if chars_present:
        console.print(f"  [yellow]Here:[/yellow] {', '.join(chars_present)}")
    if objects_visible:
        console.print(f"  [yellow]Objects:[/yellow] {', '.join(objects_visible)}")

    # Show exits
    exits = []
    for conn_id in loc.connections:
        conn = world.locations.get(conn_id)
        if conn:
            exits.append(conn.name)
    if exits:
        console.print(f"  [yellow]Exits:[/yellow] {', '.join(exits)}")


def _get_scene_text(world, location_id: str) -> str:
    """Build a basic scene description from world data."""
    loc = world.locations.get(location_id)
    if not loc:
        return "You are somewhere unfamiliar."

    parts = [loc.description or f"You are at {loc.name}."]
    if loc.ambient_state:
        time = loc.ambient_state.get("time_of_day", "")
        if time:
            parts.append(f"It is {time}.")
    return " ".join(parts)


def _show_inventory(world, location_id: str) -> None:
    """Show objects at the player's current location."""
    loc = world.locations.get(location_id)
    if not loc or not loc.objects:
        console.print("You are carrying nothing notable here.")
        return

    obj_names = [
        world.objects[o].name
        for o in loc.objects
        if o in world.objects
    ]
    console.print(f"Objects here: {', '.join(obj_names)}")


def _intent_to_action(intent, player_location: str) -> Optional[AgentAction]:
    """Convert a parsed Intent into an AgentAction for the simulation engine."""
    if intent.action == "go":
        # Resolve target to a location id
        target = _resolve_location(intent.target, player_location)
        if target is None:
            return None
        return AgentAction(
            action_type="move",
            target_id=target,
            parameters={"actor_id": "player"},
            narration=f"You head toward {intent.target}.",
        )
    elif intent.action == "talk":
        target = _resolve_character(intent.target, player_location)
        if target is None:
            return AgentAction(
                action_type="wait",
                narration=f"No one named '{intent.target}' is here.",
            )
        return AgentAction(
            action_type="talk",
            target_id=target,
            parameters={"actor_id": "player"},
            narration=f"You try to speak with {target}.",
        )
    elif intent.action == "take":
        target = _resolve_object(intent.target, player_location)
        if target:
            return AgentAction(
                action_type="take",
                target_id=target,
                parameters={"actor_id": "player"},
                narration=f"You pick up {intent.target}.",
            )
    elif intent.action == "drop":
        target = _resolve_object(intent.target, player_location)
        if target:
            return AgentAction(
                action_type="drop",
                target_id=target,
                parameters={"actor_id": "player"},
                narration=f"You drop {intent.target}.",
            )
    elif intent.action == "examine":
        target = _resolve_any(intent.target, player_location)
        return AgentAction(
            action_type="examine",
            target_id=target,
            parameters={"actor_id": "player"},
            narration=f"You examine {intent.target}.",
        )
    elif intent.action == "wait":
        return AgentAction(action_type="wait", narration="You wait.")
    return None


def _resolve_location(name: str, current_location: str) -> Optional[str]:
    """Resolve a location name/id to its ID. Returns None if not found."""
    from ..world.bundle import WorldBundle
    # This needs world access — we'll do a simpler resolution
    # The caller should handle this; for now return the name as-is
    # and let the state manager validate
    return name.lower().replace(" ", "_") if name else None


def _resolve_character(name: str, current_location: str) -> Optional[str]:
    """Resolve a character name to their ID, only if they're nearby."""
    # Placeholder — the actual resolution needs world access
    # This is handled at the engine level
    return name.lower().replace(" ", "_") if name else None


def _resolve_object(name: str, current_location: str) -> Optional[str]:
    return name.lower().replace(" ", "_") if name else None


def _resolve_any(name: str, current_location: str) -> Optional[str]:
    return name.lower().replace(" ", "_") if name else None


def _narrate_result(world, events, player_location: str, narrator) -> None:
    """Narrate the results of the player's action and background events."""
    if not events:
        console.print("[dim]Nothing notable happens.[/dim]")
        return

    for event in events:
        if narrator and event.metadata.get("action_type") == "talk":
            dialogue = event.metadata.get("dialogue", "")
            if dialogue:
                char_id = event.metadata.get("actor_id", "Someone")
                char = world.characters.get(char_id)
                name = char.name if char else char_id
                try:
                    console.print(narrator.describe_dialogue(name, dialogue))
                except Exception:
                    console.print(f'[yellow]{name}:[/yellow] "{dialogue}"')
                continue

        console.print(f"  [dim]{event.description}[/dim]")

    # Show updated scene if location changed
    move_events = [e for e in events if e.metadata.get("action_type") == "move"]
    if move_events:
        console.print("")
        _show_scene(world, player_location, narrator)


def _show_help() -> None:
    """Show available commands."""
    help_text = """
**Available Commands:**
- `go <place>` / `north` / `south` / `east` / `west` — Move to a location
- `look` / `l` — Look around
- `talk to <character>` — Speak with someone
- `take <object>` / `grab <object>` — Pick something up
- `drop <object>` — Drop something
- `examine <target>` — Inspect something
- `inventory` / `i` — See what's around you
- `wait` / `w` — Pass time
- `help` / `h` — Show this message
- `quit` / `q` — Exit the game
    """
    console.print(Markdown(help_text))
