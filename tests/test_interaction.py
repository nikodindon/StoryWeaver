"""Tests for the intent parser."""
import pytest
from storyweaver.interaction.parser import IntentParser


@pytest.fixture
def parser():
    return IntentParser(llm_client=None, use_llm_fallback=False)


def test_parse_go_north(parser):
    intent = parser.parse("go north")
    assert intent.action == "go"
    assert intent.target == "north"


def test_parse_talk(parser):
    intent = parser.parse("talk to Gandalf")
    assert intent.action == "talk"
    assert "gandalf" in intent.target.lower()


def test_parse_take(parser):
    intent = parser.parse("take the ring")
    assert intent.action == "take"
    assert "ring" in intent.target.lower()


def test_parse_look(parser):
    intent = parser.parse("look")
    assert intent.action == "look"


def test_parse_shorthand_direction(parser):
    intent = parser.parse("n")
    assert intent.action == "go"


def test_parse_unknown(parser):
    intent = parser.parse("do something completely weird xyz123")
    assert intent.action == "unknown"
    assert intent.confidence == 0.0
