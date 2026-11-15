"""Evaluate retrieved evidence and preserve per-query traces."""
import re
from typing import Any


def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _chunk_has_full_evidence(chunk_text: str, evidence_quote: str) -> bool:
    """Return True if chunk_text contains the entire normalized evidence_quote."""
    norm_chunk = _collapse_ws(chunk_text)
    norm_quote = _collapse_ws(evidence_quote)
    if not norm_quote:
        return False
    return norm_quote in norm_chunk


def _chunk_evidence_coverage(chunk_text: str, evidence_quote: str) -> float:
    """Compute fraction of sentences/clauses of evidence_quote present in chunk_text."""
    norm_chunk = _collapse_ws(chunk_text)
    norm_quote = _collapse_ws(evidence_quote)
    if not norm_quote:
        return 0.0
    if norm_quote in norm_chunk:
        return 1.0
    clauses = [c.strip() for c in re.split(r"(?<=[.!?…:;])\s+", norm_quote) if len(c.strip()) >= 15]
    if not clauses:
        return 1.0 if norm_quote in norm_chunk else 0.0
    matched = sum(1 for c in clauses if c in norm_chunk)
    return round(matched / len(clauses), 4)


def evaluate_query(
    question: dict[str, Any],
    hits: list[dict[str, Any]],
    strategy: str = "",
    applied_filter: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Check source/page and gold evidence for top-3 hits; record Hit@1, Evidence Hit@3, and multi-chunk split."""
    gold_source_id = question["gold_source_id"]
    valid_pages = {int(question["gold_page"])} | {int(p) for p in question.get("alternative_gold_pages", [])}
    evidence_quote = question["evidence_quote"]

    annotated_hits: list[dict[str, Any]] = []
    for h in hits[:3]:
        meta = h.get("metadata", {})
        source_match = meta.get("document_id") == gold_source_id
        page_match = source_match and int(meta.get("page", -1)) in valid_pages
        full_quote_in_chunk = _chunk_has_full_evidence(h.get("text", ""), evidence_quote)
        clause_cov = _chunk_evidence_coverage(h.get("text", ""), evidence_quote)

        # Primary definition per GUIDE.md: chunk belongs to gold source/page AND contains enough evidence (>= 0.85 or full quote)
        is_evidence_hit = bool(page_match and (full_quote_in_chunk or clause_cov >= 0.85))
        filter_compliant = True
        if question.get("filter"):
            for fk, fv in question["filter"].items():
                if meta.get(fk) != fv:
                    filter_compliant = False

        annotated_hits.append(
            {
                **h,
                "source_match": source_match,
                "page_match": page_match,
                "full_quote_in_chunk": full_quote_in_chunk,
                "evidence_clause_coverage": clause_cov,
                "is_evidence_hit": is_evidence_hit,
                "filter_compliant": filter_compliant,
            }
        )

    hit_at_1 = bool(annotated_hits and annotated_hits[0]["is_evidence_hit"])
    hit_at_3 = any(h["is_evidence_hit"] for h in annotated_hits)
    page_hit_at_1 = bool(annotated_hits and annotated_hits[0]["page_match"])
    page_hit_at_3 = any(h["page_match"] for h in annotated_hits)

    # Check if evidence was split across multiple retrieved chunks on the gold page
    gold_page_texts = " ".join(h.get("text", "") for h in annotated_hits if h["page_match"])
    multi_chunk_combined_hit = bool(
        page_hit_at_3
        and (
            _chunk_has_full_evidence(gold_page_texts, evidence_quote)
            or _chunk_evidence_coverage(gold_page_texts, evidence_quote) >= 0.85
        )
    )
    evidence_split_across_chunks = bool((not hit_at_3) and page_hit_at_3)

    has_question_filter = bool(question.get("filter"))
    top3_filter_compliant = all(h["filter_compliant"] for h in annotated_hits) if annotated_hits else False

    return {
        "strategy": strategy,
        "question_id": question["id"],
        "split": question["split"],
        "question_type": question.get("type", ""),
        "question": question["question"],
        "expected_answer": question["expected_answer"],
        "gold_source_id": gold_source_id,
        "gold_page": question["gold_page"],
        "alternative_gold_pages": question.get("alternative_gold_pages", []),
        "evidence_quote": evidence_quote,
        "question_filter": question.get("filter"),
        "applied_filter": applied_filter,
        "hit_at_1": hit_at_1,
        "evidence_hit_at_3": hit_at_3,
        "page_hit_at_1": page_hit_at_1,
        "page_hit_at_3": page_hit_at_3,
        "multi_chunk_combined_hit_at_3": multi_chunk_combined_hit,
        "evidence_split_across_chunks": evidence_split_across_chunks,
        "has_question_filter": has_question_filter,
        "top3_filter_compliant": top3_filter_compliant if has_question_filter else None,
        "hits": annotated_hits,
    }


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Hit@1 and Evidence Hit@3 by strategy and dev/test split with numerator/denominator."""
    summary: dict[str, Any] = {}
    strategies = sorted({t["strategy"] for t in traces})

    for strat in strategies:
        summary[strat] = {}
        for split in ("dev", "test", "all"):
            subset = [
                t for t in traces
                if t["strategy"] == strat and (split == "all" or t["split"] == split)
            ]
            total = len(subset)
            if total == 0:
                continue
            h1 = sum(1 for t in subset if t["hit_at_1"])
            h3 = sum(1 for t in subset if t["evidence_hit_at_3"])
            ph1 = sum(1 for t in subset if t["page_hit_at_1"])
            ph3 = sum(1 for t in subset if t["page_hit_at_3"])
            mc3 = sum(1 for t in subset if t["multi_chunk_combined_hit_at_3"])
            split_err = sum(1 for t in subset if t["evidence_split_across_chunks"])

            filter_qs = [t for t in subset if t["has_question_filter"]]
            f_total = len(filter_qs)
            f_comp = sum(1 for t in filter_qs if t["top3_filter_compliant"])

            summary[strat][split] = {
                "total_questions": total,
                "hit_at_1_count": h1,
                "hit_at_1_fraction": f"{h1}/{total}",
                "hit_at_1_rate": round(h1 / total, 4),
                "evidence_hit_at_3_count": h3,
                "evidence_hit_at_3_fraction": f"{h3}/{total}",
                "evidence_hit_at_3_rate": round(h3 / total, 4),
                "page_hit_at_1_fraction": f"{ph1}/{total}",
                "page_hit_at_3_fraction": f"{ph3}/{total}",
                "multi_chunk_hit_at_3_fraction": f"{mc3}/{total}",
                "evidence_split_error_count": split_err,
                "filter_questions_count": f_total,
                "filter_compliant_fraction": f"{f_comp}/{f_total}" if f_total > 0 else "N/A",
                "filter_compliant_rate": round(f_comp / f_total, 4) if f_total > 0 else None,
            }
    return summary
