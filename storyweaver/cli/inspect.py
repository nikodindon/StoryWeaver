"""CLI inspect command — explore a compiled world's contents."""
from __future__ import annotations
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

console = Console()


def run_inspect(world_name: str, show: str, character: Optional[str] = None) -> None:
    """Inspect a compiled world's contents."""
    from ..world.bundle import WorldBundle

    world_dir = Path("data") / "compiled" / world_name
    bundle_path = world_dir / "bundle.json"

    if not bundle_path.exists():
        console.print(f"[bold red]Error:[/bold red] World not found: {world_name}")
        console.print(f"  Looked for: {bundle_path}")
        console.print(f"\nCompile it first: [bold]storyweaver compile <book>[/bold]")
        raise SystemExit(1)

    bundle = WorldBundle.load(world_dir)

    console.print(f"\n[bold cyan]╔══════════════════════════════════════╗[/bold cyan]")
    console.print(f"[bold cyan]║  StoryWeaver — World Inspector       ║[/bold cyan]")
    console.print(f"[bold cyan]╚══════════════════════════════════════╝[/bold cyan]\n")
    console.print(f"World: [bold]{bundle.source_title}[/bold] by {bundle.source_author}")
    console.print(f"Compiled: {bundle.compiled_at[:19]}\n")

    if show == "summary" or show == "characters":
        _show_characters(bundle)

    if show == "summary" or show == "locations":
        _show_locations(bundle)

    if show == "summary" or show == "events":
        _show_events(bundle)

    if character:
        _show_character_detail(bundle, character)


def _show_characters(bundle) -> None:
    console.print(f"[bold]👥 Characters ({len(bundle.characters)})[/bold]")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("Location", style="yellow")
    table.add_column("Major", style="green")
    table.add_column("Relationships")

    for cid, char in bundle.characters.items():
        table.add_row(
            cid,
            char.name,
            char.current_location,
            "★" if char.is_major else "·",
            str(len(char.relationships)),
        )
    console.print(table)
    console.print()


def _show_locations(bundle) -> None:
    console.print(f"[bold]🗺️  Locations ({len(bundle.locations)})[/bold]")
    tree = Tree("World Map")
    for lid, loc in bundle.locations.items():
        branch = tree.add(f"[bold]{loc.name}[/bold] ({loc.id})")
        branch.add(f"Connections: {', '.join(loc.connections) if loc.connections else 'none'}")
        branch.add(f"Objects: {len(loc.objects)}")
        branch.add(f"Characters: {', '.join(loc.characters_present) if loc.characters_present else 'none'}")
    console.print(tree)
    console.print()


def _show_events(bundle) -> None:
    console.print(f"[bold]📜 Canon Events ({len(bundle.canon_events)})[/bold]")
    for i, event in enumerate(bundle.canon_events):
        console.print(f"  [dim]{i+1:03d}.[/dim] {event.description}")
    console.print()


def _show_character_detail(bundle, char_id_or_name: str) -> None:
    # Try exact id match first, then name match
    char = bundle.characters.get(char_id_or_name)
    if char is None:
        for c in bundle.characters.values():
            if c.name.lower() == char_id_or_name.lower():
                char = c
                break

    if char is None:
        console.print(f"[bold red]Character not found:[/bold red] {char_id_or_name}")
        return

    console.print(f"[bold]Detail: {char.name}[/bold]\n")
    console.print(f"  ID:       {char.id}")
    console.print(f"  Location: {char.current_location}")
    console.print(f"  Major:    {'Yes' if char.is_major else 'No'}")
    console.print(f"  Tags:     {', '.join(char.tags) if char.tags else '—'}")

    if char.relationships:
        console.print(f"\n  [bold]Relationships:[/bold]")
        for rel_id, rel in char.relationships.items():
            other = bundle.characters.get(rel_id)
            name = other.name if other else rel_id
            console.print(f"    → {name}: trust={rel.trust:.1f}, affection={rel.affection:.1f}")
    console.print()
