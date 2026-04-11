"""Infers world rules from symbolism pass + structure data + relations."""
from typing import Dict
from ..world.rules import WorldRules


class RulesBuilder:
    def __init__(self, llm): self.llm = llm

    def build(self, symbolism: Dict, structure: Dict, relations: Dict = None) -> WorldRules:
        raw_rules = symbolism.get("world_rules", {})
        physics = raw_rules.get("physics", {})
        social = raw_rules.get("social", {})
        narrative = raw_rules.get("narrative", {})
        custom = raw_rules.get("custom_rules", {})

        # Fold in conflict/relationship data as custom rules
        if relations:
            conflicts_data = relations.get("conflicts", {})
            if isinstance(conflicts_data, dict):
                conflict_list = conflicts_data.get("conflicts", [])
                if conflict_list:
                    custom["major_conflicts"] = [
                        {"over": c.get("over", ""), "intensity": c.get("intensity", 0.5),
                         "sides": c.get("sides", [])}
                        for c in conflict_list
                    ]
                hierarchies = conflicts_data.get("hierarchies", [])
                if hierarchies:
                    custom["hierarchies"] = [
                        {"domain": h.get("domain", ""), "type": h.get("type", "")}
                        for h in hierarchies
                    ]

        return WorldRules(
            magic_exists=physics.get("magic_exists", False),
            death_is_permanent=physics.get("death_is_permanent", True),
            travel_costs_time=raw_rules.get("travel_costs_time", True),
            information_spreads=social.get("information_spreads", True),
            canon_gravity=0.7,  # Default; tuned by gravity_map in bundle
            author_ghost_enabled=True,
            divergence_tracking=True,
            custom=custom,
        )
