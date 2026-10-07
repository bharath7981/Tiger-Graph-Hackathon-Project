"""Specialized Entity Linking Agent for Olympic domain entities and graph seeds."""

import time
import re
from typing import Any, Dict, List
from backend.app.agents.specialized.base import BaseSpecializedAgent, AgentResult
from backend.app.pipelines.graphrag import tigergraph_rag
from backend.app.core.logging import logger


class EntityLinkingAgent(BaseSpecializedAgent):
    """Specialized agent to disambiguate Olympic entities and identify graph seed vertices."""

    def __init__(self):
        super().__init__(name="EntityLinkingAgent")

    def run(self, params: Dict[str, Any]) -> AgentResult:
        start_time = time.perf_counter()
        question = params.get("question", "")

        if not question:
            return AgentResult(
                agent_name=self.name,
                status="error",
                error="Question parameter is required",
            )

        try:
            # 1. Extract entities using TigerGraph entity link logic
            entities = tigergraph_rag.link_entities_from_question(question)

            # 2. Extract specific temporal anchors
            years = re.findall(r"\b(189\d|19\d\d|20\d\d)\b", question)
            if years and not entities.get("games"):
                for y in years:
                    season = "Winter" if "winter" in question.lower() else "Summer"
                    entities["games"] = f"{y} {season}"

            # 3. Compile clean extracted entity tokens
            extracted_list: List[str] = []
            if entities.get("games"):
                extracted_list.append(entities["games"])
            if entities.get("sports"):
                extracted_list.extend(entities["sports"])
            if entities.get("venues"):
                extracted_list.extend(entities["venues"])
            if entities.get("date"):
                extracted_list.append(entities["date"])

            latency = (time.perf_counter() - start_time) * 1000.0
            summary = (
                f"Disambiguated {len(extracted_list)} entities: "
                f"{', '.join(extracted_list) if extracted_list else 'No specific graph entities found'}"
            )

            return AgentResult(
                agent_name=self.name,
                status="success",
                data={
                    "entities": entities,
                    "extracted_list": extracted_list,
                    "years": years,
                    "target_games": entities.get("games"),
                    "target_sports": entities.get("sports", []),
                },
                summary=summary,
                latency_ms=round(latency, 2),
                tokens=25 + len(question.split()),
            )
        except Exception as e:
            logger.error(f"EntityLinkingAgent failed: {e}")
            return AgentResult(
                agent_name=self.name,
                status="error",
                error=str(e),
                latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            )


entity_linking_agent = EntityLinkingAgent()
