"""Question data model for evaluation benchmarks."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QuestionRecord(BaseModel):
    """Normalized question model for evaluation datasets."""
    question_id: str = Field(..., description="Unique question identifier")
    question: str = Field(..., description="Question prompt text")
    ground_truth: Optional[List[str]] = Field(default=None, description="Canonical answer(s) if available")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")
