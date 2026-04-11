"""Infers world rules from symbolism pass + structure data."""
from typing import Dict
from ..world.rules import WorldRules


class RulesBuilder:
    def __init__(self, llm): self.llm = llm

    def build(self, symbolism: Dict, structure: Dict) -> WorldRules:
        raw_rules = symbolism.get("world_rules", {})
        return WorldRules(
            magic_exists=raw_rules.get("magic_exists", False),
            death_is_permanent=raw_rules.get("death_is_permanent", True),
            travel_costs_time=raw_rules.get("travel_costs_time", True),
            custom=raw_rules.get("custom", {}),
        )
