"""Builds the location graph from extracted location data."""
from typing import Dict, List
import networkx as nx
from ..world.location import Location


class GraphBuilder:
    def build_locations(self, raw_locations: List[Dict]) -> Dict[str, Location]:
        locations = {}
        G = nx.Graph()

        for loc in raw_locations:
            loc_id = loc["name"].lower().replace(" ", "_")
            location = Location(
                id=loc_id,
                name=loc["name"],
                description=loc.get("description", ""),
                connections=[c.lower().replace(" ", "_") for c in loc.get("connected_to", [])],
            )
            locations[loc_id] = location
            G.add_node(loc_id, name=loc["name"])

        # Add edges from connections
        for loc_id, location in locations.items():
            for conn_id in location.connections:
                if conn_id in locations:
                    G.add_edge(loc_id, conn_id)

        return locations
