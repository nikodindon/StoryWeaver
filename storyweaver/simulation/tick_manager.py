"""Controls which agents fire on each tick."""
from typing import Dict, List


TIER_PRIMARY = "primary"
TIER_SECONDARY = "secondary"
TIER_BACKGROUND = "background"


class TickManager:
    def __init__(self, agents: Dict, tier_config: Dict):
        self._agents = agents
        self._tiers = self._assign_tiers(agents)
        self._primary_freq = tier_config.get("primary_frequency", 1)
        self._secondary_freq = tier_config.get("secondary_frequency", 3)
        self._background_freq = tier_config.get("background_frequency", 10)

    def get_agents_for_tick(self, tick: int) -> List:
        """Return agents that should act on this tick."""
        active = []
        for agent_id, tier in self._tiers.items():
            agent = self._agents[agent_id]
            if tier == TIER_PRIMARY and tick % self._primary_freq == 0:
                active.append(agent)
            elif tier == TIER_SECONDARY and tick % self._secondary_freq == 0:
                active.append(agent)
            elif tier == TIER_BACKGROUND and tick % self._background_freq == 0:
                active.append(agent)
        return active

    def _assign_tiers(self, agents: Dict) -> Dict[str, str]:
        tiers = {}
        for agent_id, agent in agents.items():
            # Assign tier based on whether character is major
            is_major = getattr(agent, "is_major", True)
            tiers[agent_id] = TIER_PRIMARY if is_major else TIER_SECONDARY
        return tiers
