"""TigerGraph schema definitions and GSQL generation."""

from typing import Dict, List, Any


VERTEX_TYPES = {
    "Event": {
        "primary_id": "id",
        "id_type": "STRING",
        "attributes": {
            "name": "STRING",
            "sport": "STRING",
            "date": "STRING",
            "competitors": "INT",
            "nations": "INT",
            "doc_id": "STRING",
        },
    },
    "Games": {
        "primary_id": "id",
        "id_type": "STRING",
        "attributes": {
            "name": "STRING",
            "year": "INT",
            "season": "STRING",
        },
    },
    "Sport": {
        "primary_id": "id",
        "id_type": "STRING",
        "attributes": {
            "name": "STRING",
        },
    },
    "Venue": {
        "primary_id": "id",
        "id_type": "STRING",
        "attributes": {
            "name": "STRING",
        },
    },
    "Athlete": {
        "primary_id": "id",
        "id_type": "STRING",
        "attributes": {
            "name": "STRING",
        },
    },
    "Country": {
        "primary_id": "id",
        "id_type": "STRING",
        "attributes": {
            "noc": "STRING",
            "name": "STRING",
        },
    },
    "Document": {
        "primary_id": "id",
        "id_type": "STRING",
        "attributes": {
            "title": "STRING",
            "url": "STRING",
        },
    },
}

EDGE_TYPES = {
    "PART_OF_GAMES": {
        "from": "Event",
        "to": "Games",
        "is_directed": True,
        "attributes": {},
    },
    "IN_SPORT": {
        "from": "Event",
        "to": "Sport",
        "is_directed": True,
        "attributes": {},
    },
    "HELD_AT": {
        "from": "Event",
        "to": "Venue",
        "is_directed": True,
        "attributes": {},
    },
    "WON_MEDAL": {
        "from": "Athlete",
        "to": "Event",
        "is_directed": True,
        "attributes": {
            "medal_type": "STRING",  # "gold" | "silver" | "bronze"
        },
    },
    "REPRESENTS": {
        "from": "Athlete",
        "to": "Country",
        "is_directed": True,
        "attributes": {},
    },
    "PRECEDES_GAMES": {
        "from": "Games",
        "to": "Games",
        "is_directed": True,
        "attributes": {},
    },
    "DESCRIBES": {
        "from": "Document",
        "to": "Event",
        "is_directed": True,
        "attributes": {},
    },
}


def generate_gsql_schema(graph_name: str = "OlympicGraph") -> str:
    """Generates the full TigerGraph GSQL schema definition script."""
    lines = [f"USE GLOBAL", f"SET sys.data_root = \"/tmp\"", ""]

    # Define Vertices
    for v_name, v_def in VERTEX_TYPES.items():
        attr_strs = [f"{k} {v}" for k, v in v_def["attributes"].items()]
        attrs = (", " + ", ".join(attr_strs)) if attr_strs else ""
        lines.append(f"CREATE VERTEX {v_name}(PRIMARY_ID {v_def['primary_id']} {v_def['id_type']}{attrs});")

    lines.append("")

    # Define Edges
    for e_name, e_def in EDGE_TYPES.items():
        attr_strs = [f"{k} {v}" for k, v in e_def["attributes"].items()]
        attrs = (", " + ", ".join(attr_strs)) if attr_strs else ""
        directed_kw = "DIRECTED" if e_def["is_directed"] else "UNDIRECTED"
        lines.append(
            f"CREATE {directed_kw} EDGE {e_name}(FROM {e_def['from']}, TO {e_def['to']}{attrs});"
        )

    lines.append("")
    # Define Graph
    v_list = ", ".join(VERTEX_TYPES.keys())
    e_list = ", ".join(EDGE_TYPES.keys())
    lines.append(f"CREATE GRAPH {graph_name}({v_list}, {e_list});")

    return "\n".join(lines)
