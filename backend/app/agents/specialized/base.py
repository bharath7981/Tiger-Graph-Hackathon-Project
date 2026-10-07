"""Base interface and return types for specialized investigation agents."""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentResult(BaseModel):
    """Normalized structured return value from a specialized agent."""
    agent_name: str
    status: str = "success"  # success | error
    data: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    evidence_ids: List[str] = Field(default_factory=list)
    tokens: int = 0
    latency_ms: float = 0.0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.status == "success"


class BaseSpecializedAgent(ABC):
    """Abstract base class for all specialized domain investigation agents."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, params: Dict[str, Any]) -> AgentResult:
        """Executes the specialized agent logic."""
        pass
