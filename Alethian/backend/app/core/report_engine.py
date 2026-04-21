from typing import List, Dict, Any, Optional


def calculate_originality(matches: List[Dict[str, Any]], doc_word_count: int) -> float:
    if doc_word_count == 0:
        return 100.0

    # Collect character ranges from non-excluded matches
    ranges = []
    for m in matches:
        if not m.get('is_excluded'):
            start = m.get('submitted_start_char', 0)
            end = m.get('submitted_end_char', start + len(m.get('submitted_text', '')))
            if start < end:
                ranges.append((start, end))

    if not ranges:
        return 100.0

    # Merge overlapping ranges to avoid double-counting
    ranges.sort()
    merged = [ranges[0]]
    for start, end in ranges[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    # Count total matched characters, then estimate words (~6 chars/word avg)
    total_matched_chars = sum(end - start for start, end in merged)
    matched_words = total_matched_chars / 6.0
    coverage = matched_words / doc_word_count
    return max(0.0, min(100.0, (1.0 - coverage) * 100.0))


def generate_heatmap(matches: List[Dict[str, Any]], page_count: int,
                     doc_word_count: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Generates per-page density data for heatmap rendering.
    Returns list of page dicts with both 'density_score' (DB field)
    AND 'match_density' (frontend alias) so both sides work.
    """
    from app.core.config import settings
    words_per_page = getattr(settings, 'SHINGLING_WORDS_PER_PAGE', 500)
    if doc_word_count and page_count > 0:
        words_per_page = max(100, doc_word_count // page_count)

    page_data = {}
    for i in range(1, max(2, page_count + 1)):
        page_data[i] = {"internal_words": 0, "web_words": 0,
                        "total_words": words_per_page, "match_count": 0}

    for m in matches:
        if m.get('is_excluded'):
            continue
        page = m.get('submitted_page', 1)
        page = min(max(1, page), max(1, page_count))

        words = len(m.get('submitted_text', '').split())
        if page not in page_data:
            page_data[page] = {"internal_words": 0, "web_words": 0,
                                "total_words": words_per_page, "match_count": 0}

        page_data[page]["match_count"] += 1
        if m.get('type') == 'web':
            page_data[page]["web_words"] += words
        else:
            page_data[page]["internal_words"] += words

    def get_color(density: float) -> str:
        if density == 0:
            return "#22c55e"
        if density <= 0.25:
            return "#eab308"
        if density <= 0.50:
            return "#f97316"
        if density <= 0.75:
            return "#ef4444"
        return "#dc2626"

    heatmap = []
    for p in range(1, max(2, page_count + 1)):
        data = page_data[p]
        total = max(1, data["total_words"])
        internal_dens = min(1.0, data["internal_words"] / total)
        web_dens = min(1.0, data["web_words"] / total)
        total_dens = min(1.0, internal_dens + web_dens)

        dom = "clean"
        if data["match_count"] > 0:
            dom = "web" if web_dens > internal_dens else "internal"

        heatmap.append({
            "page_number": p,
            "density_score": total_dens,       # DB field name
            "match_density": total_dens,        # Frontend alias — fixes BUG-5
            "internal_density": internal_dens,
            "web_density": web_dens,
            "color": get_color(total_dens),
            "match_count": data["match_count"],
            "dominant_type": dom,
        })
    return heatmap


def generate_page_distribution(matches: List[Dict[str, Any]],
                                page_count: int) -> List[Dict[str, Any]]:
    """
    Returns per-page match counts broken down by type.
    Shape: [{page, internal_exact, internal_paraphrase, web}, ...]
    This is what BarChart.jsx expects (BUG-6 fix).
    """
    page_data: Dict[int, Dict[str, int]] = {}
    for p in range(1, max(2, page_count + 1)):
        page_data[p] = {"page": p, "internal_exact": 0, "internal_paraphrase": 0, "web": 0}

    for m in matches:
        if m.get('is_excluded'):
            continue
        page = m.get('submitted_page', 1)
        page = min(max(1, page), max(1, page_count))
        if page not in page_data:
            page_data[page] = {"page": page, "internal_exact": 0,
                                "internal_paraphrase": 0, "web": 0}
        mtype = m.get('type', '')
        if mtype == 'internal_exact':
            page_data[page]["internal_exact"] += 1
        elif mtype == 'internal_paraphrase':
            page_data[page]["internal_paraphrase"] += 1
        elif mtype == 'web':
            page_data[page]["web"] += 1

    return [page_data[p] for p in sorted(page_data.keys())]


def calculate_contributions(matches: List[Dict[str, Any]],
                             doc_word_count: int) -> Dict[str, float]:
    """
    Returns internal_contribution and web_contribution as percentages
    of the total document word count. Fixes GAP-3 (hardcoded 0.0 values).
    """
    if doc_word_count == 0:
        return {"internal_contribution": 0.0, "web_contribution": 0.0}

    internal_chars = 0
    web_chars = 0

    # Collect ranges per type, then merge within type
    internal_ranges = []
    web_ranges = []

    for m in matches:
        if m.get('is_excluded'):
            continue
        start = m.get('submitted_start_char', 0)
        end = m.get('submitted_end_char', start + len(m.get('submitted_text', '')))
        if end <= start:
            continue
        if m.get('type') == 'web':
            web_ranges.append((start, end))
        else:
            internal_ranges.append((start, end))

    def merge_and_count(ranges):
        if not ranges:
            return 0
        ranges.sort()
        merged = [ranges[0]]
        for s, e in ranges[1:]:
            if s <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], e))
            else:
                merged.append((s, e))
        return sum(e - s for s, e in merged)

    internal_chars = merge_and_count(internal_ranges)
    web_chars = merge_and_count(web_ranges)

    internal_words = internal_chars / 6.0
    web_words = web_chars / 6.0

    return {
        "internal_contribution": round(min(100.0, (internal_words / doc_word_count) * 100), 2),
        "web_contribution": round(min(100.0, (web_words / doc_word_count) * 100), 2),
    }


def build_summary_stats(matches: List[Dict[str, Any]], page_count: int) -> Dict[str, Any]:
    active = [m for m in matches if not m.get("is_excluded")]
    stats = {
        "total_matches": len(matches),
        "internal_exact": sum(1 for m in active if m.get("type") == "internal_exact"),
        "internal_paraphrase": sum(1 for m in active if m.get("type") == "internal_paraphrase"),
        "web_matches": sum(1 for m in active if m.get("type") == "web"),
        "unique_sources": len(set(m.get("source_id") for m in active if m.get("source_id"))),
        "avg_match_length_words": 0,
        "longest_match_words": 0,
        "longest_match_page": None,
        "pages_with_matches": len(set(m.get("submitted_page") for m in active if m.get("submitted_page"))),
        "total_pages": page_count,
        "excluded_matches": sum(1 for m in matches if m.get("is_excluded")),
        "coherent_domains": list(set(
            m.get("domain", "") for m in active
            if m.get("is_coherent") and m.get("domain")
        )),
    }
    valid_lengths = [m.get("match_length_words", 0) for m in active]
    if valid_lengths:
        stats["avg_match_length_words"] = round(sum(valid_lengths) / len(valid_lengths), 1)
        stats["longest_match_words"] = max(valid_lengths)
        longest = max(active, key=lambda m: m.get("match_length_words", 0))
        stats["longest_match_page"] = longest.get("submitted_page")
    return stats


def recalculate_after_exclusion(report, match_id: str, db_session) -> float:
    matches_dicts = [
        {
            "is_excluded": m.is_excluded,
            "submitted_text": m.submitted_text,
            "submitted_start_char": m.submitted_start_char,
            "submitted_end_char": m.submitted_end_char,
        }
        for m in report.matches
    ]
    word_count = report.doc_word_count or len((report.document.content or "").split()) or 1
    score = calculate_originality(matches_dicts, word_count)
    report.score = score
    report.risk_level = "high" if score < 50 else ("moderate" if score < 80 else "low")
    db_session.commit()
    return score


def generate_source_breakdown(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregates word counts per source for the PieChart."""
    domains: Dict[str, int] = {}
    for m in matches:
        if m.get('is_excluded'):
            continue
        if m.get('type') == 'web':
            domain = m.get('source_title') or 'Web Domain'
            domains[domain] = domains.get(domain, 0) + m.get('match_length_words', 10)
        else:
            domains["Archive"] = domains.get("Archive", 0) + m.get('match_length_words', 10)

    return [{"name": d, "value": v} for d, v in domains.items()]
