import uuid
from typing import List, Dict, Any

def calculate_originality(matches: List[Dict[str, Any]], doc_word_count: int) -> float:
    if doc_word_count == 0:
        return 100.0
    matched_words = 0
    for m in matches:
        if not m.get('is_excluded'):
            matched_words += len(m.get('submitted_text', '').split())
    coverage = matched_words / doc_word_count
    return max(0.0, min(100.0, (1.0 - coverage) * 100.0))

def generate_heatmap(matches: List[Dict[str, Any]], page_count: int) -> List[Dict[str, Any]]:
    page_data = {}
    for i in range(1, max(2, page_count + 1)):
        page_data[i] = {"internal_words": 0, "web_words": 0, "total_words": 500, "match_count": 0}

    for m in matches:
        if m.get('is_excluded'):
            continue
        page = m.get('submitted_page', 1)
        page = min(page, page_count) if page_count > 0 else 1
        
        words = len(m.get('submitted_text', '').split())
        if page not in page_data:
            page_data[page] = {"internal_words": 0, "web_words": 0, "total_words": 500, "match_count": 0}
            
        page_data[page]["match_count"] += 1
        if m.get('type') == 'web':
            page_data[page]["web_words"] += words
        else:
            page_data[page]["internal_words"] += words

    heatmap = []
    
    def get_color(density):
        if density == 0: return "#22c55e"
        if density <= 0.25: return "#eab308"
        if density <= 0.50: return "#f97316"
        if density <= 0.75: return "#ef4444"
        return "#dc2626"

    for p in range(1, max(2, page_count + 1)):
        data = page_data[p]
        internal_dens = min(1.0, data["internal_words"] / data["total_words"])
        web_dens = min(1.0, data["web_words"] / data["total_words"])
        total_dens = min(1.0, internal_dens + web_dens)
        
        dom = "clean"
        if data["match_count"] > 0:
            dom = "web" if web_dens > internal_dens else "internal"
            
        heatmap.append({
            "page_number": p,
            "density_score": total_dens,
            "internal_density": internal_dens,
            "web_density": web_dens,
            "color": get_color(total_dens),
            "match_count": data["match_count"],
            "dominant_type": dom
        })
    return heatmap

def build_summary_stats(matches: List[Dict[str, Any]], page_count: int) -> Dict[str, Any]:
    stats = {
        "total_matches": len(matches),
        "internal_exact": sum(1 for m in matches if m.get("type") == "internal_exact" and not m.get("is_excluded")),
        "internal_paraphrase": sum(1 for m in matches if m.get("type") == "internal_paraphrase" and not m.get("is_excluded")),
        "web_matches": sum(1 for m in matches if m.get("type") == "web" and not m.get("is_excluded")),
        "unique_sources": len(set(m.get("source_id") for m in matches if m.get("source_id") and not m.get("is_excluded"))),
        "avg_match_length_words": 0,
        "longest_match_words": 0,
        "longest_match_page": None,
        "pages_with_matches": len(set(m.get("submitted_page") for m in matches if not m.get("is_excluded"))),
        "total_pages": page_count,
        "excluded_matches": sum(1 for m in matches if m.get("is_excluded")),
        "coherent_domains": []
    }
    valid_lengths = [m.get("match_length_words", 0) for m in matches if not m.get("is_excluded")]
    if valid_lengths:
        stats["avg_match_length_words"] = float(sum(valid_lengths)) / len(valid_lengths)
        stats["longest_match_words"] = max(valid_lengths)
    
    return stats

def recalculate_after_exclusion(report, match_id: str, db_session) -> float:
    matches_dicts = []
    for m in report.matches:
        matches_dicts.append({
            "is_excluded": m.is_excluded,
            "submitted_text": m.submitted_text
        })
    
    # Simple proxy representation
    score = calculate_originality(matches_dicts, (report.document.page_count or 1) * 500)
    report.score = score
    report.risk_level = "high" if score < 50 else ("moderate" if score < 80 else "low")
    db_session.commit()
    return score

def generate_source_breakdown(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    domains = {}
    for m in matches:
        if m.get('is_excluded'): continue
        if m.get('type') == 'web':
            domain = m.get('source_title') or 'Web Domain'
            domains[domain] = domains.get(domain, 0) + m.get('match_length_words', 10)
        else:
            domains["Archive"] = domains.get("Archive", 0) + m.get('match_length_words', 10)
            
    breakdown = []
    for d, v in domains.items():
        breakdown.append({"name": d, "value": v})
    return breakdown
