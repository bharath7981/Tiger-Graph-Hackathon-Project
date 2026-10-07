"""Data models for temporal validity, competing claims, and conflict resolution."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TemporalInterval(BaseModel):
    """Represents the temporal validity window of a statement or graph relationship."""
    valid_from: Optional[str] = Field(default=None, description="Start date/year of validity")
    valid_to: Optional[str] = Field(default=None, description="End date/year of validity (None if ongoing)")
    source_date: Optional[str] = Field(default=None, description="Timestamp of the publishing source")
    is_current: bool = Field(default=True, description="Whether this assertion is currently authoritative")


class CompetingClaim(BaseModel):
    """An individual assertion that may conflict with or supersede another assertion."""
    claim_id: str
    entity: str
    attribute: str  # e.g., "gold_medalist", "venue", "competitor_count"
    value: str
    source_doc_id: Optional[str] = None
    source_text: str = ""
    authority_score: float = Field(ge=0.0, le=1.0, default=0.5, description="Source reliability and recency score")
    temporal_interval: Optional[TemporalInterval] = None
    superseded_by: Optional[str] = None
    status: str = "active"  # "active" | "superseded" | "disputed"


class ConflictReport(BaseModel):
    """Report detailing detected contradictions, authority weighting, and resolution."""
    has_conflict: bool = False
    entity: str = ""
    conflict_type: str = "none"  # "medal_reallocation" | "temporal_precedence" | "attribute_discrepancy" | "none"
    competing_claims: List[CompetingClaim] = Field(default_factory=list)
    resolved_claim: Optional[CompetingClaim] = None
    resolution_rationale: str = ""
    residual_uncertainty: float = Field(ge=0.0, le=1.0, default=0.0)
