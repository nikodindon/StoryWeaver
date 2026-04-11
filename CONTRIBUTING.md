# Contributing to StoryWeaver Engine

StoryWeaver is in early design/prototype phase. Here's where contributions matter most right now.

## High-Value Contribution Areas

### 1. Extraction Prompts (`storyweaver/extraction/prompts/`)
The quality of the entire system depends on extraction quality. If you can write better prompts for character psychology, relation extraction, or world rule inference — that's immediately impactful.

Test your prompts against public domain texts (Project Gutenberg).

### 2. Agent Psychology Research
The `psychology.py` model is a first draft. Improvements to the trait model, goal evaluation logic, or decision engine are welcome. Literature on narrative psychology or computational character models is especially useful here.

### 3. Extraction Pipeline (`storyweaver/extraction/`)
The pipeline architecture needs to be robust to:
- LLM output parsing failures (JSON extraction is messy)
- Long books with thousands of chunks
- Incremental re-runs (only re-process what changed)

### 4. Book Ingestion (`storyweaver/ingestion/`)
EPUB and PDF parsing edge cases are endless. Contributions improving format support are welcome.

## Development Setup

```bash
git clone https://github.com/yourusername/storyweaver-engine
cd storyweaver-engine
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

You'll need a running llama.cpp server:
```bash
./llama-server -m your-model.gguf --port 8080 --ctx-size 8192
```

## Running Tests

```bash
pytest tests/
```

Most tests use mock LLM responses to avoid requiring a live inference server.

## Code Style

- Type hints everywhere
- Pydantic models for all data structures
- Loguru for logging (`from loguru import logger`)
- No silent failures — surface errors early

## Before Submitting a PR

- [ ] Tests pass
- [ ] New functionality has tests
- [ ] Data structures use Pydantic
- [ ] LLM calls go through `LLMClient` abstraction
- [ ] No world-logic in LLM prompt code (keep these layers separate)

## Discussions Welcome

Open an issue for:
- Architecture questions
- Prompt design debates
- Model recommendations
- Use cases you want to support
