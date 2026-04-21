"""
Unit tests for report_engine module.
Pure math/logic — no infrastructure dependencies.
"""
import pytest
from app.core.report_engine import (
    calculate_originality,
    generate_heatmap,
    build_summary_stats,
    generate_source_breakdown
)


class TestCalculateOriginality:
    def test_full_originality_no_matches(self):
        score = calculate_originality([], doc_word_count=1000)
        assert score == 100.0

    def test_zero_word_count_returns_100(self):
        score = calculate_originality([{"submitted_text": "some text"}], doc_word_count=0)
        assert score == 100.0

    def test_partial_match_reduces_score(self):
        matches = [{
            "submitted_text": "one two three four five", 
            "submitted_start_char": 0,
            "submitted_end_char": 30, 
            "is_excluded": False
        }]
        score = calculate_originality(matches, doc_word_count=10)
        # 5 matched words out of 10 → 50% original
        assert score == pytest.approx(50.0, abs=1.0)

    def test_excluded_matches_ignored(self):
        matches = [
            {"submitted_text": "one two three four five", "is_excluded": True},
            {"submitted_text": "six seven", "submitted_start_char": 0, "submitted_end_char": 12, "is_excluded": False}
        ]
        score = calculate_originality(matches, doc_word_count=10)
        # Only 2 words matched (excluded one ignored) → 80%
        assert score == pytest.approx(80.0, abs=1.0)


class TestGenerateHeatmap:
    def test_produces_pages(self):
        matches = [
            {"submitted_text": "words " * 50, "submitted_page": 1, "type": "internal_exact", "is_excluded": False}
        ]
        heatmap = generate_heatmap(matches, page_count=3)
        assert len(heatmap) == 3
        assert heatmap[0]["page_number"] == 1
        assert heatmap[0]["density_score"] > 0

    def test_empty_matches_all_green(self):
        heatmap = generate_heatmap([], page_count=2)
        assert len(heatmap) == 2
        for page in heatmap:
            assert page["color"] == "#22c55e"
            assert page["dominant_type"] == "clean"

    def test_color_thresholds(self):
        # Heavy match on page 1 should be red
        matches = [
            {"submitted_text": "word " * 400, "submitted_page": 1, "type": "web", "is_excluded": False}
        ]
        heatmap = generate_heatmap(matches, page_count=1)
        assert heatmap[0]["color"] in ("#ef4444", "#dc2626")  # Red shades
        assert heatmap[0]["dominant_type"] == "web"


class TestBuildSummaryStats:
    def test_counts_match_types(self):
        matches = [
            {"type": "internal_exact", "is_excluded": False, "source_id": "s1", "submitted_page": 1, "match_length_words": 20},
            {"type": "internal_paraphrase", "is_excluded": False, "source_id": "s2", "submitted_page": 2, "match_length_words": 15},
            {"type": "web", "is_excluded": False, "source_id": "s3", "submitted_page": 1, "match_length_words": 30},
            {"type": "web", "is_excluded": True, "source_id": "s4", "submitted_page": 3, "match_length_words": 10},
        ]
        stats = build_summary_stats(matches, page_count=5)
        assert stats["total_matches"] == 4
        assert stats["internal_exact"] == 1
        assert stats["internal_paraphrase"] == 1
        assert stats["web_matches"] == 1  # Excluded one not counted
        assert stats["unique_sources"] == 3
        assert stats["excluded_matches"] == 1
        assert stats["pages_with_matches"] == 2  # Pages 1 and 2 (excluded not counted)
        assert stats["total_pages"] == 5
        assert stats["avg_match_length_words"] == pytest.approx(21.67, abs=0.1)
        assert stats["longest_match_words"] == 30


class TestGenerateSourceBreakdown:
    def test_groups_by_domain_and_archive(self):
        matches = [
            {"type": "web", "source_title": "example.com", "is_excluded": False, "match_length_words": 50},
            {"type": "web", "source_title": "example.com", "is_excluded": False, "match_length_words": 30},
            {"type": "internal_exact", "source_title": "Doc A", "is_excluded": False, "match_length_words": 20},
        ]
        breakdown = generate_source_breakdown(matches)
        names = [b["name"] for b in breakdown]
        assert "example.com" in names
        assert "Archive" in names
        # example.com value should be 80 (50+30)
        for b in breakdown:
            if b["name"] == "example.com":
                assert b["value"] == 80

    def test_excludes_excluded_matches(self):
        matches = [
            {"type": "web", "source_title": "site.com", "is_excluded": True, "match_length_words": 100},
        ]
        breakdown = generate_source_breakdown(matches)
        assert len(breakdown) == 0
