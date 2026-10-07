"""TigerGraph integration abstraction layer."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import httpx
from backend.app.core.config import settings
from backend.app.core.logging import logger


class BaseGraphClient(ABC):
    """Abstract base class for knowledge graph storage."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if graph database is reachable."""
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Retrieve graph schema definition."""
        pass

    @abstractmethod
    def run_installed_query(self, query_name: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Run an installed GSQL query."""
        pass


class TigerGraphClient(BaseGraphClient):
    """Client for communicating with TigerGraph REST++ and GSQL endpoints."""

    def __init__(
        self,
        host: Optional[str] = None,
        restpp_port: Optional[int] = None,
        graph_name: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
    ):
        self.host = host or settings.TIGERGRAPH_HOST
        self.restpp_port = restpp_port or settings.TIGERGRAPH_RESTPP_PORT
        self.graph_name = graph_name or settings.TIGERGRAPH_GRAPH_NAME
        self.username = username or settings.TIGERGRAPH_USERNAME
        self.password = password or settings.TIGERGRAPH_PASSWORD
        self.token = token or settings.TIGERGRAPH_TOKEN
        self.base_url = f"{self.host}:{self.restpp_port}"

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def is_connected(self) -> bool:
        """Verify reachability of TigerGraph REST++ API."""
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.base_url}/echo")
                return res.status_code == 200
        except Exception as e:
            logger.debug(f"TigerGraph connection check failed: {e}")
            return False

    def get_schema(self) -> Dict[str, Any]:
        """Fetch schema of the configured graph."""
        if not self.is_connected():
            return {
                "status": "offline",
                "graph_name": self.graph_name,
                "message": "TigerGraph server is offline or unreachable",
            }
        try:
            with httpx.Client(timeout=5.0) as client:
                url = f"{self.base_url}/gsqlserver/gsql/schema?graph={self.graph_name}"
                res = client.get(url, headers=self._get_headers())
                if res.status_code == 200:
                    return res.json()
                return {"error": res.text, "status_code": res.status_code}
        except Exception as e:
            logger.error(f"Error fetching TigerGraph schema: {e}")
            return {"error": str(e)}

    def run_installed_query(self, query_name: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Run an installed GSQL query against the graph."""
        if not self.is_connected():
            logger.warning("TigerGraph is offline; returning empty result.")
            return []
        try:
            with httpx.Client(timeout=10.0) as client:
                url = f"{self.base_url}/query/{self.graph_name}/{query_name}"
                res = client.get(url, params=params or {}, headers=self._get_headers())
                if res.status_code == 200:
                    data = res.json()
                    return data.get("results", [])
                logger.error(f"Query {query_name} failed with status {res.status_code}: {res.text}")
                return []
        except Exception as e:
            logger.error(f"Exception executing query {query_name}: {e}")
            return []


# Default singleton instance
tigergraph_client = TigerGraphClient()
