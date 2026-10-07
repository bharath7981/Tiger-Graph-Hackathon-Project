"""Service for detecting factual conflicts, ranking source authority, and resolving retrospective reallocations."""

import re
from typing import Any, Dict, List, Optional
from backend.app.models.temporal import TemporalInterval, CompetingClaim, ConflictReport
from backend.app.core.logging import logger


def clean_person_name(name: str) -> str:
    """Cleans extracted person name by stripping leading conjunctions and trailing nationalities."""
    name = re.sub(r"^(?:and|or|while|then)\s+", "", name.strip(), flags=re.IGNORECASE)
    name = re.sub(r"\s+of\s+(?:the\s+)?[A-Z][A-Za-z\s]+$", "", name.strip())
    return name.strip()


class ConflictResolutionService:
    """Detects, analyzes, and resolves conflicting statements and retrospective Olympic reallocations."""

    def extract_claims_from_text(self, text: str, source_doc_id: Optional[str] = None) -> List[CompetingClaim]:
        """Extracts candidate claims from text passages, specifically looking for winners, medalists, and reallocations."""
        claims: List[CompetingClaim] = []

        # 1. Check for original winner before disqualification
        orig_match = re.search(
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?:\s+of\s+[A-Za-z\s]+)?\s+(?:originally|initially)\s+(?:won|finished|took|received)",
            text,
            re.IGNORECASE,
        )

        # 2. Check for disqualification cues
        disq_match = re.search(
            r"(?:disqualified|stripped\s+of|tested\s+positive|doping)",
            text,
            re.IGNORECASE,
        )

        # 3. Check for reallocated / awarded replacement winner
        realloc_match = re.search(
            r"(?:reallocated\s+to|awarded\s+(?:the\s+gold\s+medal\s+)?to|promoted\s+to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            text,
            re.IGNORECASE,
        )
        if not realloc_match and disq_match:
            after_disq = text[disq_match.end():]
            awarded_match = re.search(
                r"(?:and\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?:\s+of\s+[A-Za-z\s]+)?\s+was\s+awarded\s+(?:the\s+)?gold",
                after_disq,
                re.IGNORECASE,
            )
            if awarded_match:
                realloc_match = awarded_match

        if orig_match and disq_match and realloc_match:
            orig_winner = clean_person_name(orig_match.group(1))
            realloc_winner = clean_person_name(realloc_match.group(1))

            claim_orig = CompetingClaim(
                claim_id=f"claim_{len(claims)+1}",
                entity="Olympic Event",
                attribute="gold_medalist",
                value=orig_winner,
                source_doc_id=source_doc_id,
                source_text=text[:250],
                authority_score=0.45,
                temporal_interval=TemporalInterval(valid_to="Disqualification Date", is_current=False),
                status="superseded",
            )

            claim_realloc = CompetingClaim(
                claim_id=f"claim_{len(claims)+2}",
                entity="Olympic Event",
                attribute="gold_medalist",
                value=realloc_winner,
                source_doc_id=source_doc_id,
                source_text=text[:250],
                authority_score=0.95,
                temporal_interval=TemporalInterval(valid_from="Reallocation Date", is_current=True),
                status="active",
            )

            claims.extend([claim_orig, claim_realloc])
            return claims

        # If no explicit reallocation pattern was found, extract standard medalist assertions
        if not claims:
            medalist_matches = re.finditer(
                r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(?:won\s+the\s+gold\s+medal|won\s+gold|took\s+first\s+place)",
                text,
            )
            for m in medalist_matches:
                winner = m.group(1).strip()
                claims.append(
                    CompetingClaim(
                        claim_id=f"claim_{len(claims)+1}",
                        entity="Olympic Event",
                        attribute="gold_medalist",
                        value=winner,
                        source_doc_id=source_doc_id,
                        source_text=m.group(0),
                        authority_score=0.75,
                        temporal_interval=TemporalInterval(is_current=True),
                        status="active",
                    )
                )

        return claims

    def resolve_conflicts(
        self,
        claims: List[CompetingClaim],
        entity_name: str = "Olympic Event",
    ) -> ConflictReport:
        """Analyzes competing claims, ranks by authority & recency, and outputs a resolved determination."""
        if not claims:
            return ConflictReport(
                has_conflict=False,
                entity=entity_name,
                conflict_type="none",
                resolution_rationale="No claims submitted for evaluation.",
            )

        # Group by attribute
        claims_by_value = set(c.value.lower() for c in claims)
        if len(claims_by_value) <= 1:
            # All claims agree
            c = claims[0]
            return ConflictReport(
                has_conflict=False,
                entity=entity_name,
                conflict_type="none",
                competing_claims=claims,
                resolved_claim=c,
                resolution_rationale=f"Unanimous agreement across sources: {c.value} is verified.",
                residual_uncertainty=0.0,
            )

        # Conflict exists between competing claims!
        # Check if one claim explicitly supersedes another (e.g. doping reallocation)
        superseded_claims = [c for c in claims if c.status == "superseded"]
        active_claims = [c for c in claims if c.status == "active"]

        if superseded_claims and active_claims:
            # Sort active claims by authority
            sorted_active = sorted(active_claims, key=lambda x: x.authority_score, reverse=True)
            top_claim = sorted_active[0]
            superseded_athlete = superseded_claims[0].value

            rationale = (
                f"Retrospective reallocation detected: {superseded_athlete} was originally awarded the medal but "
                f"subsequently disqualified. The medal was reallocated to {top_claim.value}, which is the authoritative "
                f"current record (Authority: {top_claim.authority_score:.2f})."
            )

            return ConflictReport(
                has_conflict=True,
                entity=entity_name,
                conflict_type="medal_reallocation",
                competing_claims=claims,
                resolved_claim=top_claim,
                resolution_rationale=rationale,
                residual_uncertainty=0.05,
            )

        # Standard competing claims: select highest authority score
        sorted_claims = sorted(claims, key=lambda x: x.authority_score, reverse=True)
        top_claim = sorted_claims[0]
        second_claim = sorted_claims[1]

        score_diff = top_claim.authority_score - second_claim.authority_score
        uncertainty = max(0.1, 0.5 - score_diff)

        rationale = (
            f"Competing assertions detected between '{top_claim.value}' (Authority: {top_claim.authority_score:.2f}) "
            f"and '{second_claim.value}' (Authority: {second_claim.authority_score:.2f}). "
            f"Resolved in favor of {top_claim.value} based on source authority weighting."
        )

        return ConflictReport(
            has_conflict=True,
            entity=entity_name,
            conflict_type="attribute_discrepancy",
            competing_claims=claims,
            resolved_claim=top_claim,
            resolution_rationale=rationale,
            residual_uncertainty=round(uncertainty, 3),
        )


conflict_service = ConflictResolutionService()
