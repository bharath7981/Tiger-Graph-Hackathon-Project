"""Deterministic entity and relationship extractor from corpus documents."""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.app.models.document import DocumentRecord
from backend.app.core.logging import logger


class ExtractedGraphElements(BaseModel):
    """Container for vertices and edges extracted from documents."""
    vertices: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    edges: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)


def clean_int(val: Any) -> Optional[int]:
    """Extracts first integer from a string value."""
    if val is None:
        return None
    if isinstance(val, int):
        return val
    val_str = str(val).replace(",", "").strip()
    match = re.search(r"\d+", val_str)
    return int(match.group()) if match else None


def extract_names_from_field(name_field: str) -> List[str]:
    """Cleans and extracts athlete name(s) from infobox medal fields."""
    if not name_field:
        return []
    # If separated by comma, slash, or newline
    raw_names = re.split(r"[,/;\n]|\band\b", name_field)
    cleaned = []
    for n in raw_names:
        name = re.sub(r"\[\[.*?\]\]", "", n).strip()
        name = re.sub(r"\([A-Z]{3}\)", "", name).strip()
        if len(name) > 2 and not name.isdigit():
            cleaned.append(name)
    return cleaned if cleaned else [name_field.strip()]


class EntityExtractor:
    """Extracts entities and relationships from Olympic corpus documents."""

    def extract_from_document(self, doc: DocumentRecord) -> ExtractedGraphElements:
        vertices: Dict[str, List[Dict[str, Any]]] = {
            "Event": [],
            "Games": [],
            "Sport": [],
            "Venue": [],
            "Athlete": [],
            "Country": [],
            "Document": [],
        }
        edges: Dict[str, List[Dict[str, Any]]] = {
            "PART_OF_GAMES": [],
            "IN_SPORT": [],
            "HELD_AT": [],
            "WON_MEDAL": [],
            "REPRESENTS": [],
            "PRECEDES_GAMES": [],
            "DESCRIBES": [],
        }

        # 1. Document Vertex
        vertices["Document"].append({
            "id": doc.document_id,
            "title": doc.title,
            "url": doc.source,
        })

        # 2. Extract Sport from Title
        sport_name = "Olympic Event"
        if " at the " in doc.title:
            sport_name = doc.title.split(" at the ")[0].strip()

        vertices["Sport"].append({
            "id": sport_name,
            "name": sport_name,
        })

        # 3. Parse Infobox Key-Values
        text = doc.content
        if "[Infobox" in text:
            try:
                ib_section = text.split("[Infobox")[1].split("\n\n")[0]
                ib_data = {}
                for line in ib_section.split("\n")[1:]:
                    if ":" in line:
                        k, v = line.split(":", 1)
                        ib_data[k.strip().lower()] = v.strip()

                event_name = ib_data.get("event") or doc.title
                games_str = ib_data.get("games", "")
                venue_name = ib_data.get("venue", "")
                date_str = ib_data.get("date", "")
                competitors = clean_int(ib_data.get("competitors"))
                nations = clean_int(ib_data.get("nations"))

                # Event Vertex
                event_id = doc.document_id  # Using Wikidata QID as canonical event vertex ID
                vertices["Event"].append({
                    "id": event_id,
                    "name": event_name,
                    "sport": sport_name,
                    "date": date_str,
                    "competitors": competitors or 0,
                    "nations": nations or 0,
                    "doc_id": doc.document_id,
                })

                # Document -> DESCRIBES -> Event
                edges["DESCRIBES"].append({
                    "from_id": doc.document_id,
                    "to_id": event_id,
                })

                # Event -> IN_SPORT -> Sport
                edges["IN_SPORT"].append({
                    "from_id": event_id,
                    "to_id": sport_name,
                })

                # Games Vertex & Edge
                if games_str:
                    # Parse year and season (e.g. '2012 Summer')
                    year_match = re.search(r"\d{4}", games_str)
                    year = int(year_match.group()) if year_match else None
                    season = "Winter" if "Winter" in games_str else "Summer"
                    games_id = games_str

                    vertices["Games"].append({
                        "id": games_id,
                        "name": games_str,
                        "year": year or 0,
                        "season": season,
                    })

                    edges["PART_OF_GAMES"].append({
                        "from_id": event_id,
                        "to_id": games_id,
                    })

                # Venue Vertex & Edge
                if venue_name:
                    vertices["Venue"].append({
                        "id": venue_name,
                        "name": venue_name,
                    })
                    edges["HELD_AT"].append({
                        "from_id": event_id,
                        "to_id": venue_name,
                    })

                # Medalist Winners (Gold, Silver, Bronze)
                medal_types = [
                    ("gold", "goldnoc", "gold"),
                    ("silver", "silvernoc", "silver"),
                    ("bronze", "bronzenoc", "bronze"),
                ]
                for name_k, noc_k, m_type in medal_types:
                    raw_val = ib_data.get(name_k)
                    noc_val = ib_data.get(noc_k)
                    if raw_val:
                        athlete_names = extract_names_from_field(raw_val)
                        for a_name in athlete_names:
                            vertices["Athlete"].append({
                                "id": a_name,
                                "name": a_name,
                            })
                            edges["WON_MEDAL"].append({
                                "from_id": a_name,
                                "to_id": event_id,
                                "medal_type": m_type,
                            })

                            if noc_val:
                                vertices["Country"].append({
                                    "id": noc_val,
                                    "noc": noc_val,
                                    "name": noc_val,
                                })
                                edges["REPRESENTS"].append({
                                    "from_id": a_name,
                                    "to_id": noc_val,
                                })

            except Exception as e:
                logger.debug(f"Infobox extraction failed on doc {doc.document_id}: {e}")

        return ExtractedGraphElements(vertices=vertices, edges=edges)

    def extract_from_documents(self, documents: List[DocumentRecord]) -> ExtractedGraphElements:
        """Extracts and deduplicates vertices and edges across a batch of documents."""
        all_v: Dict[str, Dict[str, Dict[str, Any]]] = {
            "Event": {},
            "Games": {},
            "Sport": {},
            "Venue": {},
            "Athlete": {},
            "Country": {},
            "Document": {},
        }
        all_e: Dict[str, List[Dict[str, Any]]] = {
            "PART_OF_GAMES": [],
            "IN_SPORT": [],
            "HELD_AT": [],
            "WON_MEDAL": [],
            "REPRESENTS": [],
            "PRECEDES_GAMES": [],
            "DESCRIBES": [],
        }

        for doc in documents:
            res = self.extract_from_document(doc)
            for v_type, v_list in res.vertices.items():
                for v in v_list:
                    vid = str(v["id"])
                    # Keep latest / most complete vertex attributes
                    all_v[v_type][vid] = v

            for e_type, e_list in res.edges.items():
                all_e[e_type].extend(e_list)

        # Deduplicate edges
        deduped_edges: Dict[str, List[Dict[str, Any]]] = {}
        for e_type, e_list in all_e.items():
            seen = set()
            clean_list = []
            for e in e_list:
                key = (e.get("from_id"), e.get("to_id"), e.get("medal_type", ""))
                if key not in seen:
                    seen.add(key)
                    clean_list.append(e)
            deduped_edges[e_type] = clean_list

        # Construct chronological PRECEDES_GAMES edges between consecutive Games
        games_nodes = list(all_v["Games"].values())
        summer_games = sorted([g for g in games_nodes if g.get("season") == "Summer"], key=lambda x: x.get("year", 0))
        for i in range(len(summer_games) - 1):
            deduped_edges["PRECEDES_GAMES"].append({
                "from_id": summer_games[i]["id"],
                "to_id": summer_games[i + 1]["id"],
            })

        winter_games = sorted([g for g in games_nodes if g.get("season") == "Winter"], key=lambda x: x.get("year", 0))
        for i in range(len(winter_games) - 1):
            deduped_edges["PRECEDES_GAMES"].append({
                "from_id": winter_games[i]["id"],
                "to_id": winter_games[i + 1]["id"],
            })

        flat_vertices = {v_type: list(v_dict.values()) for v_type, v_dict in all_v.items()}
        return ExtractedGraphElements(vertices=flat_vertices, edges=deduped_edges)


entity_extractor = EntityExtractor()
