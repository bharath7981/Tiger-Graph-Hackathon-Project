"""API endpoints for temporal validity, competing claims, and conflict resolution."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.services.conflict_resolution import conflict_service
from backend.app.agents.specialized.conflict_resolver import conflict_resolution_agent
from backend.app.core.logging import logger

router = APIRouter(prefix="/conflicts", tags=["Temporal & Conflict Resolution"])


class ConflictAnalyzeRequest(BaseModel):
    text: str = Field(..., description="Passage or question text to analyze for conflicts or reallocations")
    entity_name: Optional[str] = Field(default="Olympic Event", description="Target entity identifier")


CURATED_CONFLICT_EXAMPLES = [
    {
        "id": "realloc-1988-weightlifting",
        "title": "1988 Men's 56 kg Weightlifting (Mitko Grablev -> Oksen Mirzoyan)",
        "games": "1988 Summer",
        "event": "Weightlifting Men's 56 kg",
        "context": "Mitko Grablev of Bulgaria originally won the gold medal in the men's 56 kg event. However, he was disqualified after testing positive for furosemide. The gold medal was subsequently reallocated to Oksen Mirzoyan of the Soviet Union.",
        "superseded_winner": "Mitko Grablev",
        "authoritative_winner": "Oksen Mirzoyan",
        "conflict_type": "medal_reallocation",
    },
    {
        "id": "realloc-2008-pistol",
        "title": "2008 Men's 50 metre Pistol (Kim Jong-su -> Tan Zongliang)",
        "games": "2008 Summer",
        "event": "Shooting Men's 50 metre pistol",
        "context": "Kim Jong-su of North Korea initially finished second and was awarded the silver medal. However, he was disqualified and stripped of the medal after testing positive for propranolol. Tan Zongliang of China was promoted to silver.",
        "superseded_winner": "Kim Jong-su",
        "authoritative_winner": "Tan Zongliang",
        "conflict_type": "medal_reallocation",
    },
    {
        "id": "realloc-1988-weightlifting-67",
        "title": "1988 Men's 67.5 kg Weightlifting (Angel Guenchev -> Joachim Kunz)",
        "games": "1988 Summer",
        "event": "Weightlifting Men's 67.5 kg",
        "context": "Angel Guenchev originally won gold in the 67.5 kg category. He was later stripped of the gold medal following a positive doping test, and Joachim Kunz was awarded the gold medal.",
        "superseded_winner": "Angel Guenchev",
        "authoritative_winner": "Joachim Kunz",
        "conflict_type": "medal_reallocation",
    }
]


@router.post("/analyze")
def analyze_conflicts_endpoint(req: ConflictAnalyzeRequest) -> Dict[str, Any]:
    """Analyzes text for competing claims and performs source authority resolution."""
    try:
        claims = conflict_service.extract_claims_from_text(req.text)
        report = conflict_service.resolve_conflicts(claims, entity_name=req.entity_name)
        return report.model_dump()
    except Exception as e:
        logger.error(f"Conflict analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/examples")
def get_conflict_examples() -> List[Dict[str, Any]]:
    """Returns curated Olympic temporal reallocation benchmark cases."""
    return CURATED_CONFLICT_EXAMPLES
