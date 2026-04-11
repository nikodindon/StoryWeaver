"""Tests for extraction passes with mock LLM responses."""
import json
import pytest
from storyweaver.extraction.pass_relations import RelationsPass
from storyweaver.extraction.pass_symbolism import SymbolismPass
from storyweaver.extraction.cache import ExtractionCache


# ── Mock LLM client ────────────────────────────────────────────────────────

class MockLLM:
    def complete(self, user: str = "", **kwargs) -> str:
        if "Analyze the relationship between two characters" in user:
            a = "alice" if "alice" in user.lower() else "bob"
            b = "bob" if a == "alice" else "alice"
            return json.dumps({
                "from": a, "to": b,
                "trust": 0.7, "affection": 0.8, "power_dynamic": 0.5,
                "description": f"{a} and {b} are close friends",
                "relationship_type": "ally",
                "secrets": [], "conflicts": [], "key_interactions": ["met once"]
            })
        elif "high-level conflicts, alliances" in user:
            return json.dumps({
                "alliances": [{"members": ["alice", "bob"], "purpose": "survival", "strength": 0.8}],
                "conflicts": [{"sides": [["alice"], ["queen"]], "over": "freedom", "intensity": 0.9}],
                "hierarchies": [{"domain": "political", "top": ["queen"], "bottom": ["alice", "bob"], "type": "formal"}]
            })
        elif "chronological timeline" in user:
            return json.dumps({
                "timeline": [
                    {"order": 1, "description": "alice arrives", "participants": ["alice"], "location": "town", "enables": [], "caused_by": []},
                    {"order": 2, "description": "alice meets bob", "participants": ["alice", "bob"], "location": "town", "enables": [], "caused_by": ["alice arrives"]}
                ]
            })
        elif "deeper symbolic layers" in user:
            return json.dumps({
                "themes": [{"name": "freedom", "weight": 0.9, "evidence": "throughout the story"},
                           {"name": "class inequality", "weight": 0.7, "evidence": "queen vs commoners"}],
                "motifs": [{"name": "birds", "frequency": "frequent", "symbolic_meaning": "freedom"},
                           {"name": "crowns", "frequency": "occasional", "symbolic_meaning": "power"}],
                "tone": "melancholy", "genre": "fairy tale",
                "author_style": ["lyrical", "repetition"]
            })
        elif "implicit rules that govern" in user:
            return json.dumps({
                "physics": {"magic_exists": True, "death_is_permanent": True, "time_travel": False,
                            "supernatural": True, "technology_level": "medieval", "notes": ""},
                "social": {"government_type": "monarchy", "class_mobility": "limited",
                           "gender_roles": "traditional", "information_spreads": True, "notes": ""},
                "narrative": {"poetic_justice": True, "tragic_flaw_matters": True,
                              "love_conquers_all": False, "innocence_lost": True, "notes": ""},
                "custom_rules": {"words_have_power": "Spoken promises cannot be broken"}
            })
        elif "narrative gravity" in user:
            return json.dumps({
                "gravity_map": {"alice meets bob": 0.5, "alice defeats queen": 0.95},
                "reasoning": {"alice meets bob": "inciting incident", "alice defeats queen": "climax"}
            })
        return "{}"


@pytest.fixture
def mock_llm():
    return MockLLM()


@pytest.fixture
def tmp_cache(tmp_path):
    return ExtractionCache(tmp_path / "cache")


@pytest.fixture
def sample_structure():
    return {
        "characters": [
            {"name": "Alice", "description": "A curious girl", "is_major": True},
            {"name": "Bob", "description": "A loyal friend", "is_major": True},
        ],
        "locations": [
            {"name": "Town", "description": "A small town"},
            {"name": "Castle", "description": "The queen's castle"},
        ],
        "events": [
            {"description": "Alice arrives", "participants": ["Alice"], "location": "Town"},
            {"description": "Alice meets Bob", "participants": ["Alice", "Bob"], "location": "Town"},
        ],
        "objects": [],
    }


@pytest.fixture
def sample_segments():
    return [
        {"id": "seg1", "text": "Alice walked into the town and looked around curiously. Bob waved at her from the square.", "chapter": 1},
        {"id": "seg2", "text": "Alice and Bob became fast friends. The Queen watched from her castle with suspicion.", "chapter": 1},
        {"id": "seg3", "text": "They decided to challenge the Queen's rule together. Birds circled overhead as they planned.", "chapter": 2},
    ]


# ── RelationsPass tests ────────────────────────────────────────────────────

def test_relations_pass_returns_social_graph(mock_llm, tmp_cache, sample_structure, sample_segments):
    rel_pass = RelationsPass(mock_llm, tmp_cache, chunk_size=2000)
    result = rel_pass.run(sample_segments, sample_structure, "test_book")

    assert "social_graph" in result
    assert "conflicts" in result
    assert "timeline" in result
    assert len(result["social_graph"]) >= 1
    assert result["social_graph"][0]["trust"] == 0.7


def test_relations_pass_conflicts(mock_llm, tmp_cache, sample_structure, sample_segments):
    rel_pass = RelationsPass(mock_llm, tmp_cache, chunk_size=2000)
    result = rel_pass.run(sample_segments, sample_structure, "test_book")

    conflicts = result["conflicts"]
    assert len(conflicts.get("conflicts", [])) >= 1
    assert len(conflicts.get("alliances", [])) >= 1
    assert len(conflicts.get("hierarchies", [])) >= 1


def test_relations_pass_timeline(mock_llm, tmp_cache, sample_structure, sample_segments):
    rel_pass = RelationsPass(mock_llm, tmp_cache, chunk_size=2000)
    result = rel_pass.run(sample_segments, sample_structure, "test_book")

    timeline = result["timeline"]
    assert len(timeline) >= 2
    assert timeline[0]["order"] == 1
    assert timeline[1]["order"] == 2


def test_relations_pass_empty_characters(tmp_cache):
    rel_pass = RelationsPass(MockLLM(), tmp_cache, chunk_size=2000)
    result = rel_pass.run([], {"characters": [], "events": [], "locations": []}, "empty")
    assert result == {"social_graph": [], "conflicts": [], "timeline": []}


# ── SymbolismPass tests ───────────────────────────────────────────────────

def test_symbolism_pass_themes_and_motifs(mock_llm, tmp_cache, sample_structure, sample_segments):
    sym = SymbolismPass(mock_llm, tmp_cache)
    result = sym.run(sample_segments, sample_structure, "test_book")

    assert "themes" in result
    assert "motifs" in result
    assert len(result["themes"]) >= 2
    assert len(result["motifs"]) >= 2
    assert result["tone"] == "melancholy"
    assert result["genre"] == "fairy tale"


def test_symbolism_pass_world_rules(mock_llm, tmp_cache, sample_structure, sample_segments):
    sym = SymbolismPass(mock_llm, tmp_cache)
    result = sym.run(sample_segments, sample_structure, "test_book")

    rules = result["world_rules"]
    assert rules["physics"]["magic_exists"] is True
    assert rules["physics"]["death_is_permanent"] is True
    assert rules["social"]["government_type"] == "monarchy"


def test_symbolism_pass_gravity_map(mock_llm, tmp_cache, sample_structure, sample_segments):
    sym = SymbolismPass(mock_llm, tmp_cache)
    result = sym.run(sample_segments, sample_structure, "test_book")

    assert "gravity_map" in result
    assert result["gravity_map"]["alice defeats queen"] == 0.95
    assert result["gravity_map"]["alice meets bob"] == 0.5


def test_symbolism_pass_empty_structure(tmp_cache):
    sym = SymbolismPass(MockLLM(), tmp_cache)
    result = sym.run([], {"characters": [], "events": [], "locations": []}, "empty")
    assert result["themes"] == []
    assert result["motifs"] == []
    assert result["gravity_map"] == {}
    assert result["world_rules"] == {}
