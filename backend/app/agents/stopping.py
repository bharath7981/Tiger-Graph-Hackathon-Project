"""Stopping criteria and boundary checks for the agentic investigation."""

from typing import Tuple
from backend.app.agents.state import InvestigationState
from backend.app.core.logging import logger


def evaluate_stopping_criteria(state: InvestigationState) -> Tuple[bool, str]:
    """Evaluates whether the investigation should terminate.
    
    Returns:
        (should_stop: bool, reason: str)
    """
    # 1. Final answer concluded
    if state.get("status") == "concluded" and state.get("final_answer"):
        return True, "Investigation concluded successfully with final answer."

    # 2. Evidence Sufficiency
    if state.get("status") == "sufficient" or state.get("confidence", 0.0) >= 0.90:
        return True, "Sufficient verified evidence collected to answer question."

    # 3. Max Iterations Exceeded
    iteration = state.get("iteration", 0)
    max_iter = state.get("max_iterations", 6)
    if iteration >= max_iter:
        logger.info(f"Stopping agent: iteration limit {max_iter} reached.")
        return True, f"Maximum iteration limit ({max_iter}) reached."

    # 4. Token Budget Exceeded
    total_tokens = state.get("total_tokens", 0)
    budget = state.get("token_budget", 8000)
    if total_tokens >= budget:
        logger.info(f"Stopping agent: token budget {budget} exceeded ({total_tokens} tokens).")
        return True, f"Token budget limit ({budget}) exceeded."

    # 5. Stall detection (repeating the exact same action)
    actions = state.get("actions_taken", [])
    if len(actions) >= 3 and len(set(actions[-3:])) == 1:
        logger.info(f"Stopping agent: repeated redundant action detected ({actions[-1]}).")
        return True, f"Investigation stalled on repetitive action: {actions[-1]}"

    return False, "continue"
