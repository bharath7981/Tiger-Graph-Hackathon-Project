"""LangGraph StateGraph definition and execution harness for Agentic GraphRAG."""

from typing import Any, Dict, Optional
from langgraph.graph import StateGraph, END
from backend.app.agents.state import InvestigationState
from backend.app.agents.orchestrator import orchestrator_agent
from backend.app.agents.stopping import evaluate_stopping_criteria
from backend.app.agents.tools import execute_tool
from backend.app.core.logging import logger


def orchestrator_node(state: InvestigationState) -> InvestigationState:
    """Executes a single dynamic reasoning and investigation step."""
    return orchestrator_agent.execute_step(state)


def fallback_final_answer_node(state: InvestigationState) -> InvestigationState:
    """Fallback node to guarantee a grounded final answer if loop terminates without one."""
    if not state.get("final_answer"):
        res = execute_tool(
            "final_answer",
            {
                "question": state.get("question", ""),
                "evidence": state.get("evidence", []),
                "retrieved_chunks": state.get("retrieved_chunks", []),
                "citations": state.get("citations", []),
            },
        )
        state["final_answer"] = res.data.get("answer", "")
        state["status"] = "concluded"
        tools = state.get("tools_used", [])
        if "final_answer" not in tools:
            tools.append("final_answer")
        state["tools_used"] = tools
    return state


def route_next_step(state: InvestigationState) -> str:
    """Conditional router determining whether to loop or terminate."""
    status = state.get("status", "investigating")
    if status == "concluded":
        return END

    should_stop, reason = evaluate_stopping_criteria(state)
    if should_stop or status in ["sufficient", "stopped"]:
        logger.info(f"LangGraph routing to final answer: {reason}")
        return "fallback_final_answer"

    # Continue the dynamic investigation loop
    return "orchestrator"


def build_investigation_graph():
    """Builds and compiles the LangGraph StateGraph."""
    graph = StateGraph(InvestigationState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("fallback_final_answer", fallback_final_answer_node)

    graph.set_entry_point("orchestrator")

    graph.add_conditional_edges(
        "orchestrator",
        route_next_step,
        {
            "orchestrator": "orchestrator",
            "fallback_final_answer": "fallback_final_answer",
            END: END,
        },
    )

    graph.add_edge("fallback_final_answer", END)

    return graph.compile()


# Compiled agent state machine
investigation_app = build_investigation_graph()


def run_agentic_investigation(
    question: str,
    question_id: Optional[str] = None,
    max_iterations: int = 6,
    token_budget: int = 8000,
) -> Dict[str, Any]:
    """Runs the Agentic GraphRAG investigation harness to completion."""
    initial_state: InvestigationState = {
        "question": question,
        "question_id": question_id,
        "entities": [],
        "sub_questions": [],
        "evidence": [],
        "retrieved_chunks": [],
        "graph_results": [],
        "citations": [],
        "missing_information": [],
        "contradictions": [],
        "actions_taken": [],
        "agents_used": ["Orchestrator"],
        "tools_used": [],
        "current_plan": "Start investigation",
        "confidence": 0.0,
        "iteration": 0,
        "max_iterations": max_iterations,
        "token_budget": token_budget,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "latency_ms": 0.0,
        "final_answer": None,
        "status": "investigating",
        "trace": [],
        "next_action": None,
    }

    final_state = investigation_app.invoke(initial_state)

    return {
        "question_id": final_state.get("question_id"),
        "question": final_state.get("question"),
        "answer": final_state.get("final_answer") or "Insufficient evidence to answer confidently.",
        "confidence": round(final_state.get("confidence", 0.0), 3),
        "citations": final_state.get("citations", []),
        "trace": final_state.get("trace", []),
        "tools_used": final_state.get("tools_used", []),
        "agents_used": final_state.get("agents_used", []),
        "steps": len(final_state.get("trace", [])),
        "tokens": final_state.get("total_tokens", 0),
        "latency_ms": round(final_state.get("latency_ms", 0.0), 2),
    }
