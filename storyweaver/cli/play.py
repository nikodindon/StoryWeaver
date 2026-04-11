"""Interactive game loop — the Zork-style CLI experience."""
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

HEADER = """
╔══════════════════════════════════════════════╗
║           S T O R Y W E A V E R              ║
╚══════════════════════════════════════════════╝
"""


def run_play(world_name: str, session: str = None, mode: str = "canon"):
    """Main interactive game loop."""
    console.print(HEADER, style="bold cyan")
    console.print(f"Loading world: [bold]{world_name}[/bold]")
    console.print(f"Mode: [italic]{mode}[/italic]\n")

    # TODO: Load world bundle + initialize simulation engine
    # For now, print placeholder
    console.print(Panel("World loading not yet implemented. V1 coming soon.", title="StoryWeaver"))

    # Game loop skeleton:
    while True:
        try:
            raw_input = console.input("\n[bold green]>[/bold green] ").strip()
            if not raw_input:
                continue
            if raw_input.lower() in ("quit", "exit", "q"):
                console.print("Farewell.")
                break

            # TODO: parse input → intent → simulation → narration
            console.print(f"[dim]Command received: {raw_input}[/dim]")

        except (KeyboardInterrupt, EOFError):
            console.print("\nFarewell.")
            break
