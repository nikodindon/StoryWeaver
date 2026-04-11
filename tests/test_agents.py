"""Tests for the agent system."""
import pytest
from storyweaver.agents.psychology import PsychologyModel, BigFive, NarrativeTraits
from storyweaver.agents.memory import AgentMemory


def test_psychology_to_prose_high_openness():
    psych = PsychologyModel(
        big_five=BigFive(openness=0.9),
        core_fear="failure",
        core_desire="knowledge",
    )
    prose = psych.to_prose()
    assert "curious" in prose.lower() or "imaginative" in prose.lower()


def test_agent_memory_stores_events():
    mem = AgentMemory("test_agent")
    mem.add_event("Met Gandalf at the inn")
    mem.add_event("Received a mysterious letter")
    retrieved = mem.retrieve_relevant("Gandalf", k=5)
    assert len(retrieved) == 2


def test_agent_memory_compression_triggers():
    mem = AgentMemory("test_agent")
    mem.MAX_EPISODIC_EVENTS = 5
    for i in range(10):
        mem.add_event(f"Event {i}")
    # After 10 events with max=5, compression should have run
    assert len(mem._compressed) > 0
