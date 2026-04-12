"""Compile the Emperor's New Clothes with real LLM."""
import sys
sys.path.insert(0, '.')

from storyweaver.ingestion.loader import load_book
from storyweaver.models.llamacpp_client import LlamaCppClient
from storyweaver.extraction.pipeline import ExtractionPipeline
from storyweaver.compiler.world_builder import WorldBuilder
from pathlib import Path

def main():
    log = open("compile_final.log", "w")
    fw = lambda s: (log.write(s + "\n"), log.flush())
    
    fw("=== StoryWeaver — Real Compilation Test ===")
    fw("")
    fw("1. Ingesting...")
    bd = load_book("examples/books/emperor_new_clothes.txt")
    bm = {"title": bd["title"], "author": bd["author"]}
    fw(f"   {len(bd['segments'])} segments, {len(bd['raw_text'])} chars")
    
    fw("2. LLM client...")
    llm = LlamaCppClient(
        base_url="http://localhost:8090/v1",
        model="Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf",
    )
    
    fw("3. Extraction pipeline...")
    cache = Path("data/cache/emperor")
    cfg = {"chunk_size_tokens": 2000, "micro_chunk_size_tokens": 500}
    pipe = ExtractionPipeline(llm, cache, cfg)
    ex = pipe.run(bd["segments"], "emperor")
    
    fw(f"   Structure: {len(ex['structure']['characters'])} chars, "
       f"{len(ex['structure']['locations'])} locs, "
       f"{len(ex['structure']['objects'])} objs, "
       f"{len(ex['structure']['events'])} events")
    fw(f"   Relations: {len(ex['relations']['social_graph'])} edges")
    fw(f"   Psychology: {len(ex['psychology'])} profiles")
    fw(f"   Symbolism: {len(ex['symbolism']['themes'])} themes, "
       f"{len(ex['symbolism']['gravity_map'])} gravity")
    
    fw("4. Compiling world...")
    builder = WorldBuilder(llm, {})
    bundle, agents = builder.build(ex, bm)
    
    fw(f"   Locations: {len(bundle.locations)}")
    fw(f"   Characters: {len(bundle.characters)}")
    fw(f"   Objects: {len(bundle.objects)}")
    fw(f"   Canon events: {len(bundle.canon_events)}")
    fw(f"   Gravity map: {len(bundle.gravity_map)} entries")
    
    fw("5. Saving bundle...")
    bundle.save(Path("data/compiled/emperor"))
    fw("   Saved to data/compiled/emperor/bundle.json")
    
    fw("")
    fw("=== COMPILATION COMPLETE ===")
    log.close()

if __name__ == "__main__":
    main()
