"""Deterministic GraphRAG Pipeline using TigerGraph and structured graph traversals."""

import re
import time
from typing import Any, Dict, List, Optional, Tuple
from backend.app.core.logging import logger
from backend.app.models.graphrag import GraphRAGResult, GraphPath, GraphEvidence
from backend.app.graph.queries import query_engine
from backend.app.graph.client import graph_client
from backend.app.services.llm_provider import llm_provider, LLMResponse


GRAPHRAG_SYSTEM_PROMPT = """You are a deterministic, knowledge-graph-grounded research assistant.
You answer questions using ONLY the verified facts from the Knowledge Graph provided in the context.

Strict Rules:
1. Base your answer strictly on the Knowledge Graph facts.
2. For counts or aggregations, rely on the exact entity count and evidence facts provided.
3. Cite the source document ID in brackets for each fact, e.g. [Doc ID: QXXXXX].
4. If the graph facts are empty or do not answer the question, state:
   "Insufficient evidence to answer confidently."
5. Be direct, factual, and concise."""


class TigerGraphRAG:
    """Deterministic GraphRAG pipeline."""

    def __init__(self, engine=None):
        self.engine = engine or query_engine

    def link_entities_from_question(self, question: str) -> Dict[str, Any]:
        """Extracts candidate entities and query intent parameters from question."""
        entities = {
            "sports": [],
            "games": None,
            "venues": [],
            "date": None,
            "competitor_threshold": None,
            "is_superlative": False,
            "is_temporal": False,
            "is_aggregation": False,
            "target_year": None,
            "season": "Summer",
        }

        q_lower = question.lower()

        # 1. Sport linking
        all_sports = graph_client.find_vertices("Sport")
        for sp in all_sports:
            s_name = sp.get("name", "")
            if s_name and s_name.lower() in q_lower:
                entities["sports"].append(s_name)

        # 2. Season & Year linking
        if "winter" in q_lower:
            entities["season"] = "Winter"
        elif "summer" in q_lower:
            entities["season"] = "Summer"

        years = re.findall(r"\b(19\d{2}|20\d{2})\b", question)
        if years:
            entities["target_year"] = int(years[-1])
            entities["games"] = f"{entities['target_year']} {entities['season']}"

        # 3. Temporal keyword check
        if "immediately before" in q_lower or "preceding" in q_lower or "prior to" in q_lower:
            entities["is_temporal"] = True

        # 4. Aggregation & Competitor Threshold
        comp_match = re.search(r"more than\s+(\d+)\s+competitors", q_lower)
        if comp_match:
            entities["competitor_threshold"] = int(comp_match.group(1))
            entities["is_aggregation"] = True
        elif "how many" in q_lower:
            entities["is_aggregation"] = True

        # 5. Superlative check
        if "highest number" in q_lower or "most competitors" in q_lower or "maximum" in q_lower:
            entities["is_superlative"] = True

        # 6. Venue linking
        all_venues = graph_client.find_vertices("Venue")
        for vn in all_venues:
            v_name = vn.get("name", "")
            if v_name and v_name.lower() in q_lower:
                entities["venues"].append(v_name)

        # 7. Date linking (e.g. 20 September 1988, 14 February 2010)
        date_match = re.search(
            r"(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{4})?)",
            question,
            re.IGNORECASE,
        )
        if date_match:
            entities["date"] = date_match.group(1)

        return entities

    def execute_graph_traversal(
        self, entities: Dict[str, Any], question: str
    ) -> Tuple[List[GraphEvidence], List[GraphPath], List[str]]:
        """Executes targeted deterministic graph queries based on linked entities."""
        evidence_list: List[GraphEvidence] = []
        path_list: List[GraphPath] = []
        citations: List[str] = []

        sport = entities["sports"][0] if entities["sports"] else None
        games = entities["games"]

        # Strategy 1: Temporal resolution (e.g., Summer Olympics immediately before 2016)
        if entities["is_temporal"] and games:
            prev_games = self.engine.find_preceding_games(games)
            if prev_games:
                path_list.append(GraphPath(source=games, edge="PRECEDED_BY", target=prev_games))
                # Search for matching event in the preceding games
                events, paths = self.engine.find_events_by_sport_and_games(sport or "", prev_games)
                path_list.extend(paths)
                for ev in events:
                    ev_id = ev["id"]
                    doc_id = ev.get("doc_id", ev_id)
                    citations.append(doc_id)
                    # Find medalists
                    medalists = self.engine.find_medalist_for_event(ev_id, "gold")
                    for m_name, m_paths in medalists:
                        path_list.extend(m_paths)
                        evidence_list.append(
                            GraphEvidence(
                                fact=f"In {prev_games}, gold medal was won by {m_name} for event '{ev.get('name')}'",
                                document_id=doc_id,
                                entity_id=ev_id,
                                entity_type="Event",
                                properties={"athlete": m_name, "games": prev_games},
                            )
                        )

        # Strategy 2: Aggregation query (e.g. how many events had > 73 competitors)
        elif entities["is_aggregation"] and sport and games:
            min_comps = entities["competitor_threshold"]
            events, paths = self.engine.find_events_by_sport_and_games(sport, games, min_comps)
            path_list.extend(paths)
            count = len(events)
            evidence_list.append(
                GraphEvidence(
                    fact=f"Knowledge graph query returned exactly {count} {sport} events at {games} with > {min_comps} competitors.",
                    document_id=events[0].get("doc_id", "") if events else "",
                    entity_id=games,
                    entity_type="Games",
                    properties={"count": count, "sport": sport, "min_competitors": min_comps},
                )
            )
            for ev in events:
                doc_id = ev.get("doc_id", ev["id"])
                citations.append(doc_id)
                evidence_list.append(
                    GraphEvidence(
                        fact=f"Event '{ev.get('name')}' had {ev.get('competitors')} competitors at {games}.",
                        document_id=doc_id,
                        entity_id=ev["id"],
                        entity_type="Event",
                        properties=ev,
                    )
                )

        # Strategy 3: Superlative query (e.g. which event had highest competitors)
        elif entities["is_superlative"] and sport and games:
            sup_res = self.engine.find_superlative_event(sport, games)
            if sup_res:
                top_ev, sup_paths = sup_res
                path_list.extend(sup_paths)
                doc_id = top_ev.get("doc_id", top_ev["id"])
                citations.append(doc_id)
                evidence_list.append(
                    GraphEvidence(
                        fact=f"The {sport} event with the highest number of competitors at {games} was '{top_ev.get('name')}' with {top_ev.get('competitors')} competitors.",
                        document_id=doc_id,
                        entity_id=top_ev["id"],
                        entity_type="Event",
                        properties=top_ev,
                    )
                )

        # Strategy 4: Multi-Hop Traversal (Venue + Date -> Event -> Medalist)
        elif entities["venues"] and entities["date"]:
            venue = entities["venues"][0]
            date_val = entities["date"]
            matched_events = self.engine.find_event_by_venue_and_date(venue, date_val)
            for ev, ev_paths in matched_events:
                path_list.extend(ev_paths)
                ev_id = ev["id"]
                doc_id = ev.get("doc_id", ev_id)
                citations.append(doc_id)
                # Find gold medalist
                medalists = self.engine.find_medalist_for_event(ev_id, "gold")
                for m_name, m_paths in medalists:
                    path_list.extend(m_paths)
                    evidence_list.append(
                        GraphEvidence(
                            fact=f"Event '{ev.get('name')}' held at {venue} on {date_val} was won by {m_name}.",
                            document_id=doc_id,
                            entity_id=ev_id,
                            entity_type="Event",
                            properties={"medalist": m_name, "venue": venue, "date": date_val},
                        )
                    )

        # Fallback: General keyword entity search across graph
        if not evidence_list:
            if sport:
                events = graph_client.find_vertices("Event", {"sport": sport})[:5]
                for ev in events:
                    doc_id = ev.get("doc_id", ev["id"])
                    citations.append(doc_id)
                    evidence_list.append(
                        GraphEvidence(
                            fact=f"Event: {ev.get('name')} in {sport} (Competitors: {ev.get('competitors')})",
                            document_id=doc_id,
                            entity_id=ev["id"],
                            entity_type="Event",
                            properties=ev,
                        )
                    )

        return evidence_list, path_list, sorted(list(set(citations)))

    def query(
        self,
        question: str,
        question_id: Optional[str] = None,
        ground_truth: Optional[List[str]] = None,
    ) -> GraphRAGResult:
        """Executes the deterministic GraphRAG pipeline."""
        start_time = time.perf_counter()

        # 1. Entity Linking
        linked_entities = self.link_entities_from_question(question)
        entity_names = [s for s in linked_entities["sports"]]
        if linked_entities["games"]:
            entity_names.append(linked_entities["games"])
        entity_names.extend(linked_entities["venues"])

        # 2. Graph Traversal & Evidence Retrieval
        graph_start = time.perf_counter()
        evidence_list, paths, citations = self.execute_graph_traversal(linked_entities, question)
        graph_latency = (time.perf_counter() - graph_start) * 1000.0

        # 3. Context Construction
        if evidence_list:
            context_facts = "\n".join([f"- {ev.fact} [Doc ID: {ev.document_id}]" for ev in evidence_list])
            context_str = f"=== KNOWLEDGE GRAPH VERIFIED FACTS ===\n{context_facts}\n=== END OF FACTS ==="
        else:
            context_str = "No directly matching graph paths or facts found."

        # 4. LLM Generation
        llm_prompt = f"{context_str}\n\nQuestion: {question}\nAnswer:"
        llm_start = time.perf_counter()
        llm_resp: LLMResponse = llm_provider.generate(
            prompt=llm_prompt,
            system_prompt=GRAPHRAG_SYSTEM_PROMPT,
        )
        llm_latency = (time.perf_counter() - llm_start) * 1000.0
        total_latency = (time.perf_counter() - start_time) * 1000.0

        answer_text = llm_resp.text.strip()
        confidence = 0.95 if evidence_list else 0.0

        # Ground Truth Verification
        is_exact = None
        if ground_truth:
            norm_ans = answer_text.lower()
            is_exact = any(gt.lower() in norm_ans for gt in ground_truth)

        human_paths = [f"{p.source} --[{p.edge}]--> {p.target}" for p in paths]

        return GraphRAGResult(
            question_id=question_id,
            question=question,
            answer=answer_text,
            entities=entity_names,
            graph_paths=human_paths,
            evidence=evidence_list,
            citations=citations,
            input_tokens=llm_resp.input_tokens,
            output_tokens=llm_resp.output_tokens,
            total_tokens=llm_resp.total_tokens,
            latency_ms=round(total_latency, 2),
            graph_latency_ms=round(graph_latency, 2),
            llm_latency_ms=round(llm_latency, 2),
            confidence=confidence,
            ground_truth=ground_truth,
            is_exact_match=is_exact,
            metadata={"entities": linked_entities},
        )


tigergraph_rag = TigerGraphRAG()
