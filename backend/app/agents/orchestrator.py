"""Orchestrator Agent implementation for dynamic tool selection and state evaluation."""

import time
from typing import Any, Dict, List, Optional
from datetime import datetime

from backend.app.agents.state import InvestigationState, TraceStep
from backend.app.agents.stopping import evaluate_stopping_criteria
from backend.app.agents.tools import execute_tool, ToolResult
from backend.app.agents.prompts import ORCHESTRATOR_SYSTEM_PROMPT
from backend.app.services.llm_provider import llm_provider
from backend.app.core.logging import logger


class OrchestratorAgent:
    """Decides the NEXT action dynamically based on accumulated investigation evidence."""

    def plan_next_action(self, state: InvestigationState) -> Dict[str, Any]:
        """Analyzes state and decides which tool to run next."""
        actions_taken = state.get("actions_taken", [])
        evidence = state.get("evidence", [])
        chunks = state.get("retrieved_chunks", [])
        question = state.get("question", "")
        entities = state.get("entities", [])
        iteration = state.get("iteration", 0)

        # 1. First Step: Always identify and link entities if not done
        if "entity_link" not in actions_taken:
            return {
                "tool": "entity_link",
                "params": {"question": question},
                "reason": "Identify sports, games, dates, and venues from question prompt.",
            }

        # 2. Check if evidence is already determined sufficient
        if state.get("status") == "sufficient" or state.get("confidence", 0.0) >= 0.85:
            return {
                "tool": "final_answer",
                "params": {
                    "question": question,
                    "evidence": evidence,
                    "retrieved_chunks": chunks,
                    "citations": state.get("citations", []),
                },
                "reason": "Verified sufficient evidence exists to formulate final answer.",
            }

        # 3. If entities linked, determine if Graph Traversal or Vector Search is primary
        q_lower = question.lower()
        has_relational_cue = any(
            kw in q_lower for kw in [
                "how many", "more than", "highest", "immediately before",
                "held at", "preceding", "competitors", "gold medal",
            ]
        )

        if has_relational_cue and "graph_traversal" not in actions_taken:
            return {
                "tool": "graph_traversal",
                "params": {
                    "question": question,
                    "entities": state.get("entities_dict", {}),
                    "traversal_type": "query",
                },
                "reason": "Execute structured graph traversal for relational/aggregation constraints.",
            }

        # 4. If graph traversal gave no results or not relational, try vector search
        if "vector_search" not in actions_taken and (not evidence or len(evidence) < 2):
            return {
                "tool": "vector_search",
                "params": {"query": question, "top_k": 4},
                "reason": "Retrieve semantic text chunks from ChromaDB for supplemental evidence.",
            }

        # 5. Evaluate accumulated evidence
        if "evidence_evaluation" not in actions_taken and (evidence or chunks):
            return {
                "tool": "evidence_evaluation",
                "params": {
                    "question": question,
                    "evidence": evidence,
                    "retrieved_chunks": chunks,
                },
                "reason": "Evaluate evidence relevance and verify sufficiency.",
            }

        # 6. If contradictions detected or disputed reallocation cues exist, resolve conflicts
        contradictions = state.get("contradictions", [])
        has_dispute_cue = any(kw in q_lower for kw in ["disqualified", "stripped", "reallocated", "disputed", "originally won"])
        if (contradictions or has_dispute_cue) and "conflict_resolution" not in actions_taken:
            return {
                "tool": "conflict_resolution",
                "params": {
                    "question": question,
                    "evidence": evidence,
                    "retrieved_chunks": chunks,
                },
                "reason": "Adjudicate conflicting claims and retrospective Olympic reallocations.",
            }

        # 7. Default to final answer synthesis
        return {
            "tool": "final_answer",
            "params": {
                "question": question,
                "evidence": evidence,
                "retrieved_chunks": chunks,
                "citations": state.get("citations", []),
            },
            "reason": "Synthesize best grounded answer with current accumulated evidence.",
        }

    def execute_step(self, state: InvestigationState) -> InvestigationState:
        """Executes the chosen next action and updates state and trace."""
        step_start = time.perf_counter()
        iteration = state.get("iteration", 0) + 1
        state["iteration"] = iteration

        # Decide next action
        plan = self.plan_next_action(state)
        tool_name = plan["tool"]
        tool_params = plan["params"]
        reason = plan["reason"]

        logger.info(f"[Step {iteration}] Orchestrator selected tool '{tool_name}': {reason}")

        # Execute registered safe tool
        result: ToolResult = execute_tool(tool_name, tool_params)
        step_latency = (time.perf_counter() - step_start) * 1000.0

        # Update State
        actions_taken = state.get("actions_taken", [])
        actions_taken.append(tool_name)
        state["actions_taken"] = actions_taken

        tools_used = state.get("tools_used", [])
        if tool_name not in tools_used:
            tools_used.append(tool_name)
        state["tools_used"] = tools_used

        # Track specialized agent
        agent_name = result.data.get("agent_name", "Orchestrator")
        agents_used = state.get("agents_used", [])
        if "Orchestrator" not in agents_used:
            agents_used.append("Orchestrator")
        if agent_name and agent_name not in agents_used:
            agents_used.append(agent_name)
        state["agents_used"] = agents_used

        state["total_tokens"] = state.get("total_tokens", 0) + result.tokens
        state["latency_ms"] = state.get("latency_ms", 0.0) + step_latency

        # Process Tool-Specific Data Updates
        if tool_name == "entity_link":
            extracted = result.data.get("extracted_list", [])
            state["entities"] = extracted
            state["entities_dict"] = result.data.get("entities", {})

        elif tool_name == "graph_traversal":
            new_ev = result.data.get("evidence", [])
            current_ev = state.get("evidence", [])
            current_ev.extend(new_ev)
            state["evidence"] = current_ev

            new_cites = result.data.get("citations", [])
            cites = set(state.get("citations", []))
            cites.update(new_cites)
            state["citations"] = sorted(list(cites))

            current_paths = state.get("graph_results", [])
            current_paths.extend(result.data.get("paths", []))
            state["graph_results"] = current_paths

        elif tool_name == "vector_search":
            new_chunks = result.data.get("chunks", [])
            current_chunks = state.get("retrieved_chunks", [])
            current_chunks.extend(new_chunks)
            state["retrieved_chunks"] = current_chunks

            cites = set(state.get("citations", []))
            for c in new_chunks:
                doc_id = c.get("metadata", {}).get("document_id") or c.get("document_id")
                if doc_id:
                    cites.add(doc_id)
            state["citations"] = sorted(list(cites))

        elif tool_name == "evidence_evaluation":
            is_suff = result.data.get("is_sufficient", False)
            conf = result.data.get("confidence", 0.0)
            state["confidence"] = conf
            if is_suff:
                state["status"] = "sufficient"
            state["missing_information"] = result.data.get("missing_information", [])

        elif tool_name == "conflict_resolution":
            resolved = result.data.get("resolved_claim")
            rationale = result.data.get("resolution_rationale", "")
            if resolved:
                current_ev = state.get("evidence", [])
                current_ev.append({
                    "claim": f"[AUTHORITATIVE RESOLUTION]: {rationale}",
                    "document_id": resolved.get("source_doc_id"),
                    "type": "resolved_conflict",
                })
                state["evidence"] = current_ev

        elif tool_name == "final_answer":
            state["final_answer"] = result.data.get("answer", "")
            state["status"] = "concluded"

        # Record structured trace step
        trace_step = TraceStep(
            step_number=iteration,
            action=f"Execute {tool_name}",
            tool=tool_name,
            agent=agent_name,
            input_summary=str(tool_params)[:150],
            output_summary=result.summary,
            latency_ms=round(step_latency, 2),
            tokens=result.tokens,
            reason=reason,
            evidence_ids=result.evidence_ids,
        )

        trace = state.get("trace", [])
        trace.append(trace_step.model_dump())
        state["trace"] = trace

        # Check stopping criteria
        should_stop, stop_reason = evaluate_stopping_criteria(state)
        if should_stop and state.get("status") != "concluded":
            state["status"] = "stopped"
            state["current_plan"] = stop_reason

        return state


orchestrator_agent = OrchestratorAgent()
