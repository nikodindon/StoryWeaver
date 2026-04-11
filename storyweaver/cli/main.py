"""
StoryWeaver CLI — Main entry point.

Usage:
  storyweaver compile <book_path>
  storyweaver play <world_name>
  storyweaver inspect <world_name> [--show characters|locations|events]
"""
import typer
from rich.console import Console

app = typer.Typer(
    name="storyweaver",
    help="Transform any book into a living, playable world.",
    rich_markup_mode="rich",
)
console = Console()


@app.command()
def compile(
    book_path: str = typer.Argument(..., help="Path to book file (EPUB, TXT, PDF)"),
    model: str = typer.Option("mistral-22b", help="LLM model to use for extraction"),
    output_name: str = typer.Option(None, help="World name (defaults to book filename)"),
):
    """Compile a book into a playable world. This may take a while."""
    from .compile import run_compile
    run_compile(book_path, model, output_name)


@app.command()
def play(
    world_name: str = typer.Argument(..., help="Name of the compiled world to play"),
    session: str = typer.Option(None, help="Resume a saved session"),
    mode: str = typer.Option("canon", help="Game mode: canon | sandbox"),
):
    """Enter a compiled world and play."""
    from .play import run_play
    run_play(world_name, session, mode)


@app.command()
def inspect(
    world_name: str = typer.Argument(..., help="Name of the compiled world"),
    show: str = typer.Option("summary", help="What to show: summary | characters | locations | events"),
    character: str = typer.Option(None, help="Inspect a specific character"),
):
    """Inspect a compiled world's contents."""
    from .inspect import run_inspect
    run_inspect(world_name, show, character)


if __name__ == "__main__":
    app()
