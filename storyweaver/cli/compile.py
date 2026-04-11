"""CLI compile command — turns a book into a playable world."""
from __future__ import annotations
from pathlib import Path
from typing import Optional

import yaml
from loguru import logger
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def run_compile(book_path: str, model: str, output_name: Optional[str] = None) -> None:
    """Compile a book into a playable world bundle."""
    from ..ingestion.loader import BookLoader
    from ..ingestion.cleaner import TextCleaner
    from ..ingestion.segmenter import Segmenter
    from ..models.llamacpp_client import LlamaCppClient
    from ..extraction.pipeline import ExtractionPipeline
    from ..compiler.world_builder import WorldBuilder

    book_file = Path(book_path)
    if not book_file.exists():
        console.print(f"[bold red]Error:[/bold red] Book not found: {book_file}")
        raise SystemExit(1)

    # Load config
    config_dir = Path(__file__).parent.parent.parent / "configs"
    with open(config_dir / "default.yaml") as f:
        default_config = yaml.safe_load(f)
    with open(config_dir / "models.yaml") as f:
        models_config = yaml.safe_load(f)

    # Derive output name
    if output_name is None:
        output_name = book_file.stem

    world_dir = Path("data") / "compiled" / output_name
    processed_dir = Path("data") / "processed" / output_name
    cache_dir = Path("data") / "cache" / output_name

    console.print(f"\n[bold cyan]╔══════════════════════════════════════╗[/bold cyan]")
    console.print(f"[bold cyan]║  StoryWeaver — World Compiler v0.1  ║[/bold cyan]")
    console.print(f"[bold cyan]╚══════════════════════════════════════╝[/bold cyan]\n")
    console.print(f"Book:     [bold]{book_file.name}[/bold]")
    console.print(f"Model:    [bold]{model}[/bold]")
    console.print(f"Output:   [bold]{world_dir}[/bold]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:

        # Step 1: Ingest
        task = progress.add_task("[cyan]Ingesting book...", total=None)
        logger.info(f"Ingesting book: {book_file}")
        book_meta, raw_text = BookLoader.load(book_file)
        cleaner = TextCleaner()
        cleaned = cleaner.clean(raw_text)
        segmenter = Segmenter(chunk_size=default_config.get("extraction", {}).get("chunk_size_tokens", 2000))
        segments = segmenter.segment(cleaned)

        # Save processed text and segments
        processed_dir.mkdir(parents=True, exist_ok=True)
        with open(processed_dir / "cleaned.txt", "w") as f:
            f.write(cleaned)
        with open(processed_dir / "segments.json", "w") as f:
            import json
            json.dump(segments, f, indent=2)

        logger.info(f"  Ingested: {len(segments)} segments, {len(cleaned)} chars")
        progress.update(task, description=f"[green]✓ Ingested ({len(segments)} segments, {len(cleaned)} chars)[/green]")

        # Step 2: Extract
        progress.update(task, description="[cyan]Running extraction... (this may take a while)")
        logger.info("Starting extraction pipeline")
        base_url = models_config.get("llamacpp", {}).get("base_url", "http://localhost:8080/v1")
        llm = LlamaCppClient(base_url=base_url)
        pipeline = ExtractionPipeline(llm, cache_dir, default_config.get("extraction", {}))
        extraction = pipeline.run(segments, output_name)
        progress.update(task, description="[green]✓ Extraction complete[/green]")

        # Step 3: Compile
        progress.update(task, description="[cyan]Compiling world...")
        logger.info("Compiling world")
        builder = WorldBuilder(llm, default_config)
        bundle, agents = builder.build(extraction, book_meta)
        progress.update(task, description="[green]✓ World compiled[/green]")

        # Step 4: Save
        progress.update(task, description="[cyan]Saving bundle...")
        bundle.save(world_dir)
        logger.info(f"World saved to {world_dir}")
        progress.update(task, description="[green]✓ Bundle saved[/green]")

    console.print(f"\n[bold green]✓[/bold green] World compiled successfully!")
    console.print(f"  Locations:  {len(bundle.locations)}")
    console.print(f"  Characters: {len(bundle.characters)}")
    console.print(f"  Objects:    {len(bundle.objects)}")
    console.print(f"  Events:     {len(bundle.canon_events)}")
    console.print(f"\nPlay it with: [bold]storyweaver play {output_name}[/bold]")
