# Name Mappings Configuration

This directory contains per-world name mapping configurations used by the extraction cleaning pipeline.

## Purpose

When LLM extraction produces multiple variants of the same character or location name (e.g., "Harry", "Harry Potter", "the boy"), the cleaning pipeline uses these mappings to resolve them to a single canonical form.

## File Format

Each world should have a file named `<world_name>_names.json` with this structure:

```json
{
  "characters": {
    "variant_name_1": "Canonical Name",
    "variant_name_2": "Canonical Name"
  },
  "locations": {
    "variant_location_1": "Canonical Location",
    "variant_location_2": "Canonical Location"
  }
}
```

## How It Works

1. `clean_extraction.py` loads the mappings for the specified world
2. During cleaning, all character and location names are resolved to their canonical forms
3. If no mapping file exists, the pipeline falls back to fuzzy string matching only
4. Fuzzy matching uses a 0.75 similarity threshold as a fallback

## Creating a New World Config

For a new book, you can either:
- **No config**: The cleaner will use fuzzy matching only (works well for most cases)
- **Create a config**: Add explicit mappings for known name variants (improves accuracy)

To create a config:
1. Run extraction on your book
2. Review `extraction.json` for name variants
3. Create `<world_name>_names.json` in this directory
4. Run `python scripts/clean_extraction.py <world_name>`

## Example

For "The Emperor's New Clothes":
```json
{
  "characters": {
    "the emperor": "The Emperor",
    "emperor": "The Emperor"
  },
  "locations": {
    "the capital": "The Capital",
    "capital": "The Capital",
    "the grand hall": "The Grand Hall"
  }
}
```
