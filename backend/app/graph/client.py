"""Graph client abstraction supporting TigerGraph REST++ and Local in-memory graph store."""

from abc import ABC, abstractmethod
import json
import os
from typing import Any, Dict, List, Optional
import httpx

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.graphrag import EntityDetail, NeighborDetail


class GraphStorageEngine(ABC):
    """Abstract interface for knowledge graph storage and querying."""

    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    def upsert_vertices(self, vertex_type: str, vertices: List[Dict[str, Any]]) -> int:
        pass

    @abstractmethod
    def upsert_edges(self, edge_type: str, edges: List[Dict[str, Any]]) -> int:
        pass

    @abstractmethod
    def get_vertex(self, vertex_id: str) -> Optional[EntityDetail]:
        pass

    @abstractmethod
    def get_neighbors(self, vertex_id: str) -> List[NeighborDetail]:
        pass

    @abstractmethod
    def find_vertices(self, vertex_type: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        pass


class LocalGraphStore(GraphStorageEngine):
    """High-performance local graph store with adjacency indices for offline resilience and tests."""

    def __init__(self, persistence_file: str = "data/processed/local_graph.json"):
        self.persistence_file = persistence_file
        self.vertices: Dict[str, Dict[str, Dict[str, Any]]] = {}  # v_type -> {id: props}
        self.id_to_type: Dict[str, str] = {}
        self.outgoing_edges: Dict[str, List[Dict[str, Any]]] = {}  # from_id -> [edge]
        self.incoming_edges: Dict[str, List[Dict[str, Any]]] = {}  # to_id -> [edge]
        self.edge_types: Dict[str, List[Dict[str, Any]]] = {}      # edge_type -> [edge]
        self._load_from_disk()

    def is_connected(self) -> bool:
        return True

    def _save_to_disk(self):
        try:
            os.makedirs(os.path.dirname(self.persistence_file), exist_ok=True)
            data = {
                "vertices": self.vertices,
                "edges": self.edge_types,
            }
            with open(self.persistence_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            logger.debug(f"Could not persist local graph to {self.persistence_file}: {e}")

    def _load_from_disk(self):
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for v_type, v_map in data.get("vertices", {}).items():
                        self.upsert_vertices(v_type, list(v_map.values()))
                    for e_type, e_list in data.get("edges", {}).items():
                        self.upsert_edges(e_type, e_list)
                logger.info(f"Loaded local graph from {self.persistence_file}: {len(self.id_to_type)} vertices.")
            except Exception as e:
                logger.debug(f"Failed to load local graph from {self.persistence_file}: {e}")

    def upsert_vertices(self, vertex_type: str, vertices: List[Dict[str, Any]]) -> int:
        if vertex_type not in self.vertices:
            self.vertices[vertex_type] = {}

        count = 0
        for v in vertices:
            vid = str(v["id"])
            self.vertices[vertex_type][vid] = v
            self.id_to_type[vid] = vertex_type
            count += 1
        return count

    def upsert_edges(self, edge_type: str, edges: List[Dict[str, Any]]) -> int:
        if edge_type not in self.edge_types:
            self.edge_types[edge_type] = []

        count = 0
        for e in edges:
            from_id = str(e["from_id"])
            to_id = str(e["to_id"])
            edge_record = {
                "edge_type": edge_type,
                "from_id": from_id,
                "to_id": to_id,
                "properties": {k: v for k, v in e.items() if k not in ["from_id", "to_id", "edge_type"]},
            }
            self.edge_types[edge_type].append(edge_record)

            if from_id not in self.outgoing_edges:
                self.outgoing_edges[from_id] = []
            self.outgoing_edges[from_id].append(edge_record)

            if to_id not in self.incoming_edges:
                self.incoming_edges[to_id] = []
            self.incoming_edges[to_id].append(edge_record)
            count += 1
        return count

    def get_vertex(self, vertex_id: str) -> Optional[EntityDetail]:
        v_type = self.id_to_type.get(vertex_id)
        if not v_type:
            return None
        props = self.vertices[v_type].get(vertex_id, {})
        return EntityDetail(
            entity_id=vertex_id,
            entity_type=v_type,
            properties=props,
        )

    def get_neighbors(self, vertex_id: str) -> List[NeighborDetail]:
        neighbors: List[NeighborDetail] = []

        # Outgoing edges
        for e in self.outgoing_edges.get(vertex_id, []):
            target_id = e["to_id"]
            target_type = self.id_to_type.get(target_id, "Unknown")
            target_props = self.vertices.get(target_type, {}).get(target_id, {})
            neighbors.append(
                NeighborDetail(
                    neighbor_id=target_id,
                    neighbor_type=target_type,
                    edge_type=e["edge_type"],
                    direction="outgoing",
                    edge_properties=e["properties"],
                    neighbor_properties=target_props,
                )
            )

        # Incoming edges
        for e in self.incoming_edges.get(vertex_id, []):
            source_id = e["from_id"]
            source_type = self.id_to_type.get(source_id, "Unknown")
            source_props = self.vertices.get(source_type, {}).get(source_id, {})
            neighbors.append(
                NeighborDetail(
                    neighbor_id=source_id,
                    neighbor_type=source_type,
                    edge_type=e["edge_type"],
                    direction="incoming",
                    edge_properties=e["properties"],
                    neighbor_properties=source_props,
                )
            )

        return neighbors

    def find_vertices(self, vertex_type: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        v_map = self.vertices.get(vertex_type, {})
        if not filters:
            return list(v_map.values())

        matched = []
        for v in v_map.values():
            match = True
            for k, expected in filters.items():
                if expected is None:
                    continue
                actual = v.get(k)
                if isinstance(expected, str) and isinstance(actual, str):
                    if expected.lower() not in actual.lower():
                        match = False
                        break
                elif actual != expected:
                    match = False
                    break
            if match:
                matched.append(v)
        return matched


class TigerGraphStorageEngine(GraphStorageEngine):
    """Communicates with live TigerGraph REST++ endpoints."""

    def __init__(self, fallback: Optional[LocalGraphStore] = None):
        self.host = settings.TIGERGRAPH_HOST
        self.port = settings.TIGERGRAPH_RESTPP_PORT
        self.graph_name = settings.TIGERGRAPH_GRAPH_NAME
        self.token = settings.TIGERGRAPH_TOKEN
        self.base_url = f"{self.host}:{self.port}"
        self.fallback = fallback or LocalGraphStore()

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def is_connected(self) -> bool:
        try:
            with httpx.Client(timeout=1.5) as client:
                res = client.get(f"{self.base_url}/echo")
                return res.status_code == 200
        except Exception:
            return False

    def upsert_vertices(self, vertex_type: str, vertices: List[Dict[str, Any]]) -> int:
        # Always mirror to local store for hybrid resilience
        self.fallback.upsert_vertices(vertex_type, vertices)

        if not self.is_connected():
            return len(vertices)

        try:
            payload = {
                "vertices": {
                    vertex_type: {
                        str(v["id"]): {k: val for k, val in v.items() if k != "id"}
                        for v in vertices
                    }
                }
            }
            with httpx.Client(timeout=10.0) as client:
                url = f"{self.base_url}/graph/{self.graph_name}"
                res = client.post(url, json=payload, headers=self._headers())
                if res.status_code == 200:
                    return len(vertices)
                logger.warning(f"TigerGraph upsert_vertices returned {res.status_code}: {res.text}")
        except Exception as e:
            logger.debug(f"TigerGraph upsert exception: {e}")

        return len(vertices)

    def upsert_edges(self, edge_type: str, edges: List[Dict[str, Any]]) -> int:
        self.fallback.upsert_edges(edge_type, edges)

        if not self.is_connected():
            return len(edges)

        try:
            edges_payload = {}
            for e in edges:
                from_id = str(e["from_id"])
                to_id = str(e["to_id"])
                if edge_type not in edges_payload:
                    edges_payload[edge_type] = {}
                edges_payload[edge_type][f"{from_id}_{to_id}"] = {
                    "from_id": from_id,
                    "to_id": to_id,
                    "attributes": {k: v for k, v in e.items() if k not in ["from_id", "to_id"]},
                }
            with httpx.Client(timeout=10.0) as client:
                url = f"{self.base_url}/graph/{self.graph_name}"
                res = client.post(url, json={"edges": edges_payload}, headers=self._headers())
                if res.status_code == 200:
                    return len(edges)
        except Exception as e:
            logger.debug(f"TigerGraph edge upsert exception: {e}")

        return len(edges)

    def get_vertex(self, vertex_id: str) -> Optional[EntityDetail]:
        return self.fallback.get_vertex(vertex_id)

    def get_neighbors(self, vertex_id: str) -> List[NeighborDetail]:
        return self.fallback.get_neighbors(vertex_id)

    def find_vertices(self, vertex_type: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return self.fallback.find_vertices(vertex_type, filters)


# Global singleton instance
local_graph_store = LocalGraphStore()
graph_client = TigerGraphStorageEngine(fallback=local_graph_store)
