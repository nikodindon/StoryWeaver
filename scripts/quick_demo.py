"""
Quick Demo — Watch StoryWeaver simulate a world without needing a LLM server.

Loads a pre-compiled world bundle and runs an auto-played demonstration
with rich output showing the tick system, agent activity, and narrative output.

Usage:
    python scripts/quick_demo.py                # Uses examples/worlds/happy_prince
    python scripts/quick_demo.py happy_prince   # Explicit world name
"""
from __future__ import annotations
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Optional

# ── Ensure storyweaver package is importable ───────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ── Rich output ────────────────────────────────────────────────────────────
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.rule import Rule

console = Console()

# ── Paths ──────────────────────────────────────────────────────────────────
EXAMPLES_DIR = PROJECT_ROOT / "examples" / "worlds"


# ── Scene descriptions (hand-crafted narrative for demo mode) ──────────────
# In a full run, the Narrator + LLM would generate these dynamically.
# For the demo, we pre-write them so the output feels alive without a server.

SCENES: Dict[str, Dict[int, str]] = {
    "happy_prince": {
        0: (
            "The last of the swallows had flown south. The autumn wind swept through "
            "the city square as one small bird, left behind for love of a reed that "
            "would not speak to him, came to rest at the feet of a golden statue."
        ),
        1: (
            "\"Swallow, Swallow, little Swallow,\" said the Prince, \"will you not "
            "stay with me for one night?\" — and the bird, who had meant to fly to "
            "Egypt, found himself unable to refuse."
        ),
        2: (
            "Far below, in a dark room at the end of a narrow street, a seamstress "
            "embroidered passion-flowers on a satin gown. Her boy lay burning with "
            "fever, asking for oranges. Through the window came a swallow — and on "
            "the windowsill, the great ruby from a prince's sword-hilt."
        ),
        3: (
            "The seamstress had fallen asleep. The child's fever was breaking. "
            "The swallow returned to the statue, warm despite the cold. "
            "\"It is curious,\" said the swallow. \"Though it is cold, I feel warm inside.\""
        ),
        4: (
            "Above the garret where a young playwright shivered over his unfinished play, "
            "a sapphire fell like a star onto his desk. He looked up, eyes wide, "
            "and thought perhaps the world was not entirely cruel."
        ),
        5: (
            "The swallow carried the second sapphire down to a match-girl in the square. "
            "She was barefoot and crying — her matches had fallen into the gutter. "
            "But there, glowing in the snow, was a stone the color of the evening sky."
        ),
        6: (
            "The Prince was blind now. Both sapphires gone. The ruby gone. "
            "But still he asked: \"Tell me what you see in the city, little swallow. "
            "I want to know about the people I could not reach.\""
        ),
        7: (
            "The swallow could have gone to Egypt. The migration had passed weeks ago. "
            "Instead, he settled on the Prince's shoulder and began to tell stories — "
            "of pyramids, of the Nile, of a reed who had never loved him back."
        ),
        8: (
            "He did not go to Egypt. He never would. "
            "The small bird kissed the Happy Prince on the lips "
            "and fell down dead at his feet.\n\n"
            "At that moment a curious crack sounded from inside the statue. "
            "The Prince's lead heart had broken clean in two."
        ),
        9: (
            "Morning came. The Mayor walked through the square with his dignitaries. "
            "\"How shabby the Happy Prince looks!\" he cried. \"The ruby has fallen out "
            "of his sword, his eyes are gone, and he is no longer golden. "
            "He is little better than a beggar!\"\n\n"
            "And they pulled the statue down."
        ),
    }
}

TICK_ACTIONS: Dict[str, Dict[int, Dict]] = {
    "happy_prince": {
        0: {
            "actor": "swallow",
            "action": "arrives at city_square, takes shelter at the statue",
        },
        1: {
            "actor": "happy_prince",
            "action": "asks swallow to carry the ruby to the seamstress's child",
        },
        2: {
            "actor": "swallow",
            "action": "flies to sewing_room, delivers ruby to sick child",
        },
        3: {
            "actor": "swallow",
            "action": "returns to city_square, reflects on the warmth he feels inside",
        },
        4: {
            "actor": "swallow",
            "action": "flies to garret, drops sapphire on playwright's desk",
        },
        5: {
            "actor": "swallow",
            "action": "delivers second sapphire to match-girl in the square",
        },
        6: {
            "actor": "happy_prince",
            "action": "asks swallow to describe the city — he is blind but still cares",
        },
        7: {
            "actor": "swallow",
            "action": "chooses to stay — tells the Prince stories of Egypt",
        },
        8: {
            "actor": "swallow",
            "action": "dies of cold at the Prince's feet; the Prince's heart breaks",
        },
        9: {
            "actor": "mayor",
            "action": "finds the statue shabby, orders it pulled down",
        },
    }
}


# ── Demo Engine ────────────────────────────────────────────────────────────
def load_bundle(world_name: str):
    """Load a world bundle from examples/worlds/."""
    world_dir = EXAMPLES_DIR / world_name
    bundle_path = world_dir / "bundle.json"

    if not bundle_path.exists():
        console.print(f"[bold red]Error:[/bold red] World '{world_name}' not found.")
        console.print(f"  Looked in: {world_dir}")
        console.print(f"\nAvailable worlds:")
        for d in sorted(EXAMPLES_DIR.iterdir()):
            if d.is_dir() and (d / "bundle.json").exists():
                console.print(f"  • [cyan]{d.name}[/cyan]")
        raise SystemExit(1)

    from storyweaver.world.bundle import WorldBundle
    return WorldBundle.load(world_dir)


def show_world_summary(bundle) -> None:
    """Display a summary of the loaded world."""
    console.print(Panel(
        f"[bold]{bundle.source_title}[/bold] by {bundle.source_author}\n"
        f"[dim]{bundle.compiled_at[:19]}[/dim]",
        title="📖 World Bundle",
        border_style="cyan",
    ))

    # Stats table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Component")
    table.add_column("Count", justify="right")

    table.add_row("Locations", str(len(bundle.locations)))
    table.add_row("Characters", str(len(bundle.characters)))
    table.add_row("Objects", str(len(bundle.objects)))
    table.add_row("Canon Events", str(len(bundle.canon_events)))
    table.add_row("World Rules", str(len(bundle.rules.custom) + 6) if bundle.rules else "6")
    table.add_row("Narrative Gravity", f"{bundle.rules.canon_gravity:.2f}" if bundle.rules else "N/A")

    console.print(table)
    console.print()

    # Location list
    console.print("[bold]🗺️  Locations:[/bold]")
    for loc in bundle.locations.values():
        marker = "★" if loc.symbolic_weight > 0.7 else "·"
        chars = [bundle.characters[c].name for c in loc.characters_present if c in bundle.characters]
        char_str = f"  — {', '.join(chars)}" if chars else ""
        console.print(f"  {marker} [yellow]{loc.name}[/yellow]{char_str}")
    console.print()


def show_canon_timeline(bundle) -> None:
    """Show the canonical event timeline."""
    console.print("[bold]📜 Canon Timeline:[/bold]")
    for event in bundle.canon_events:
        gravity_bar = "█" * int(event.gravity * 10) + "░" * (10 - int(event.gravity * 10))
        console.print(f"  [dim]T{event.tick:02d}[/dim] {event.description}  [dim][{gravity_bar}][/dim]")
    console.print()


def simulate_tick(bundle, tick: int, world_name: str) -> None:
    """Run and display a single simulation tick."""
    bundle.current_tick = tick

    # Get scene narrative
    scenes = SCENES.get(world_name, {})
    actions = TICK_ACTIONS.get(world_name, {})

    scene_text = scenes.get(tick, "Time passes quietly...")
    action_info = actions.get(tick, {})

    # Tick header
    console.print(Rule(f"[bold dim]Tick {tick}[/bold dim]", style="dim cyan"))

    # Agent action
    if action_info:
        actor = action_info.get("actor", "???")
        action_desc = action_info.get("action", "")
        console.print(f"  [bold green]→[/bold green] [bold]{actor}[/bold]: {action_desc}")

    # Narrative
    console.print(f"  {scene_text}")
    console.print()

    # Show state changes
    console.print(f"  [dim]Divergence: {bundle.divergence_score:.2f} | Canon events remaining: "
                  f"{len([e for e in bundle.canon_events if e.tick > tick])}[/dim]")


def run_demo(world_name: str, num_ticks: int = 10) -> None:
    """Run the full demonstration."""
    # Header
    console.print()
    console.print(Panel(
        "[bold cyan]StoryWeaver Engine v0.1[/bold cyan]\n"
        "[dim]Interactive Narrative Simulation — Demo Mode[/dim]",
        title="📚",
        border_style="bold cyan",
    ))
    console.print()

    # Load world
    with console.status("[bold cyan]Loading world bundle...[/bold cyan]"):
        bundle = load_bundle(world_name)
    console.print("[green]✓[/green] World loaded\n")

    # Show summary
    show_world_summary(bundle)
    show_canon_timeline(bundle)

    # Separator
    console.print(Rule("[bold]BEGINNING SIMULATION[/bold]", style="bold cyan"))
    console.print()

    # Run ticks with a slight pause for dramatic effect
    for tick in range(num_ticks):
        simulate_tick(bundle, tick, world_name)
        if tick < num_ticks - 1:
            time.sleep(0.6)

    # Closing
    console.print(Rule("[bold]SIMULATION COMPLETE[/bold]", style="bold cyan"))
    console.print()
    console.print(Panel(
        f"[bold]{bundle.source_title}[/bold] — {len(bundle.canon_events)} canon events tracked\n"
        f"Final divergence: {bundle.divergence_score:.2f}\n"
        f"Final tick: {bundle.current_tick}\n\n"
        f"[dim]This demo runs without a LLM server. In full mode, the Narrator\n"
        f"generates scene descriptions dynamically, and agents make\n"
        f"autonomous decisions based on their psychology and memory.[/dim]",
        title="Demo Complete",
        border_style="dim",
    ))
    console.print()


# ── Entry Point ────────────────────────────────────────────────────────────
def main() -> None:
    world_name = sys.argv[1] if len(sys.argv) > 1 else "happy_prince"
    num_ticks = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    run_demo(world_name, num_ticks)


if __name__ == "__main__":
    main()
