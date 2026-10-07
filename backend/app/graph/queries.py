"""Graph retrieval queries for deterministic GraphRAG operations."""

import re
from typing import Any, Dict, List, Optional, Tuple
from backend.app.graph.client import graph_client
from backend.app.models.graphrag import EntityDetail, NeighborDetail, GraphEvidence, GraphPath
from backend.app.core.logging import logger


class GraphQueryEngine:
    """Executes deterministic graph traversal patterns."""

    def __init__(self, client=None):
        self.client = client or graph_client

    def find_event_by_venue_and_date(
        self, venue_query: str, date_query: str
    ) -> List[Tuple[Dict[str, Any], List[GraphPath]]]:
        """Multi-Hop Traversal: Venue + Date -> Event."""
        matched_events = []
        events = self.client.find_vertices("Event")

        for ev in events:
            ev_id = ev["id"]
            neighbors = self.client.get_neighbors(ev_id)
            venue_match = False
            matched_venue_name = ""

            for n in neighbors:
                if n.neighbor_type == "Venue" and venue_query.lower() in n.neighbor_id.lower():
                    venue_match = True
                    matched_venue_name = n.neighbor_id
                    break

            if venue_match:
                # Check date match
                ev_date = ev.get("date", "")
                if date_query.lower() in ev_date.lower() or ev_date.lower() in date_query.lower():
                    paths = [
                        GraphPath(
                            source=ev_id,
                            edge="HELD_AT",
                            target=matched_venue_name,
                            properties={"date": ev_date},
                        )
                    ]
                    matched_events.append((ev, paths))

        return matched_events

    def find_medalist_for_event(
        self, event_id: str, medal_type: str = "gold"
    ) -> List[Tuple[str, List[GraphPath]]]:
        """Finds athlete medalists for an event."""
        neighbors = self.client.get_neighbors(event_id)
        results = []

        for n in neighbors:
            if n.edge_type == "WON_MEDAL":
                m_type = n.edge_properties.get("medal_type", "")
                if medal_type.lower() in m_type.lower():
                    athlete_name = n.neighbor_id
                    path = GraphPath(
                        source=athlete_name,
                        edge=f"WON_MEDAL[{m_type}]",
                        target=event_id,
                        properties=n.edge_properties,
                    )
                    results.append((athlete_name, [path]))

        return results

    def find_events_by_sport_and_games(
        self,
        sport_name: str,
        games_name: str,
        min_competitors: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], List[GraphPath]]:
        """Aggregation Traversal: Sport + Games -> all matching Events."""
        events = self.client.find_vertices("Event")
        matched = []
        paths = []

        for ev in events:
            ev_id = ev["id"]
            neighbors = self.client.get_neighbors(ev_id)
            has_sport = False
            has_games = False

            for n in neighbors:
                if n.neighbor_type == "Sport" and sport_name.lower() in n.neighbor_id.lower():
                    has_sport = True
                if n.neighbor_type == "Games" and games_name.lower() in n.neighbor_id.lower():
                    has_games = True

            if has_sport and has_games:
                comps = ev.get("competitors", 0)
                if min_competitors is not None:
                    if comps > min_competitors:
                        matched.append(ev)
                        paths.append(GraphPath(source=ev_id, edge="PART_OF_GAMES", target=games_name))
                else:
                    matched.append(ev)
                    paths.append(GraphPath(source=ev_id, edge="PART_OF_GAMES", target=games_name))

        return matched, paths

    def find_superlative_event(
        self, sport_name: str, games_name: str
    ) -> Optional[Tuple[Dict[str, Any], List[GraphPath]]]:
        """Superlative Traversal: Sport + Games -> Event with max competitors."""
        events, paths = self.find_events_by_sport_and_games(sport_name, games_name)
        if not events:
            return None

        # Sort by competitors descending
        sorted_events = sorted(events, key=lambda x: x.get("competitors", 0), reverse=True)
        top_event = sorted_events[0]
        ev_id = top_event["id"]
        superlative_path = [
            GraphPath(
                source=ev_id,
                edge="IN_SPORT",
                target=sport_name,
                properties={"competitors": top_event.get("competitors", 0)},
            ),
            GraphPath(source=ev_id, edge="PART_OF_GAMES", target=games_name),
        ]
        return top_event, superlative_path

    def find_preceding_games(self, current_games_name: str) -> Optional[str]:
        """Temporal Traversal: Finds the Olympic Games immediately preceding current_games_name."""
        # Check PRECEDES_GAMES edge incoming to current_games
        neighbors = self.client.get_neighbors(current_games_name)
        for n in neighbors:
            if n.edge_type == "PRECEDES_GAMES" and n.direction == "incoming":
                return n.neighbor_id

        # Fallback by year/season matching
        year_match = re.search(r"\d{4}", current_games_name)
        if not year_match:
            return None
        current_year = int(year_match.group())
        season = "Winter" if "Winter" in current_games_name else "Summer"

        all_games = self.client.find_vertices("Games")
        same_season = [g for g in all_games if g.get("season") == season and g.get("year", 0) < current_year]
        if same_season:
            sorted_prev = sorted(same_season, key=lambda x: x.get("year", 0), reverse=True)
            return sorted_prev[0]["id"]

        return None


query_engine = GraphQueryEngine()
