"""Run compilation with full error capture."""
import sys, traceback
sys.path.insert(0, '.')

# Redirect ALL errors to file
error_log = open("compile_error.txt", "w")

try:
    from storyweaver.ingestion.loader import load_book
    from storyweaver.models.llamacpp_client import LlamaCppClient
    from storyweaver.extraction.pipeline import ExtractionPipeline
    from storyweaver.compiler.world_builder import WorldBuilder
    from pathlib import Path

    log = open("compile_run.log", "w")
    fw = lambda s: (log.write(s + "\n"), log.flush())
    
    fw("=== StoryWeaver Compilation ===")
    fw("1. Ingesting...")
    bd = load_book("examples/books/emperor_new_clothes.txt")
    bm = {"title": bd["title"], "author": bd["author"]}
    fw(f"   {len(bd['segments'])} segments, {len(bd['raw_text'])} chars")
    
    fw("2. LLM client...")
    llm = LlamaCppClient(
        base_url="http://localhost:8090/v1",
        model="Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf",
    )
    
    fw("3. Extraction...")
    cache = Path("data/cache/emperor")
    cfg = {"chunk_size_tokens": 2000, "micro_chunk_size_tokens": 500}
    pipe = ExtractionPipeline(llm, cache, cfg)
    ex = pipe.run(bd["segments"], "emperor")
    
    fw(f"   Structure: {len(ex['structure']['characters'])} chars, {len(ex['structure']['locations'])} locs")
    fw(f"   Relations: {len(ex['relations']['social_graph'])} edges")
    fw(f"   Psychology: {len(ex['psychology'])} profiles")
    fw(f"   Symbolism: {len(ex['symbolism']['themes'])} themes")
    
    fw("4. Building world...")
    builder = WorldBuilder(llm, {})
    bundle, agents = builder.build(ex, bm)
    
    fw(f"   World: {len(bundle.locations)} locs, {len(bundle.characters)} chars")
    
    fw("5. Saving...")
    bundle.save(Path("data/compiled/emperor"))
    fw("=== COMPLETE ===")
    log.close()
    
except Exception as e:
    error_log.write(f"EXCEPTION: {e}\n")
    traceback.print_exc(file=error_log)
    error_log.close()
    print(f"ERROR: {e}")
    raise
