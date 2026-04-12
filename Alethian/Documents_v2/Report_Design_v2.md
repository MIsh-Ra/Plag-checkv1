# Alethian Report Design Specification v2.0

This document provides a comprehensive design specification for the Alethian plagiarism report — the primary deliverable that faculty interact with. The report is designed to be **more expressive, informative, and actionable than Turnitin**.

---

## 1. Design Philosophy

### 1.1 Goals
1.  **Transparency:** Every finding is accompanied by full evidence — the submitted text AND the matched source text, displayed side-by-side.
2.  **Actionability:** Faculty can exclude false positives, annotate findings, and recalculate scores without leaving the interface.
3.  **Comprehensiveness:** The report presents data at multiple levels of detail — from a single headline score to per-page heatmaps to individual matched sentences.
4.  **Exportability:** The report exists in three formats — interactive web dashboard, printable PDF, and machine-readable JSON.

### 1.2 How We Surpass Turnitin

| Feature | Turnitin | Alethian v2 |
|---|---|---|
| **Originality Score** | ✅ Single % | ✅ Single % + risk level classification |
| **Source Highlighting** | ✅ Color-coded text | ✅ Color-coded text + inline type indicators |
| **Side-by-Side Diff** | ❌ No (click to view source) | ✅ Always visible, live updates |
| **Page Heatmap** | ❌ No | ✅ Visual page-by-page density strip |
| **Source Breakdown Chart** | ✅ Basic list | ✅ Interactive pie chart + bar chart + sortable table |
| **Match Type Filtering** | ❌ No | ✅ Toggle exact/paraphrase/web |
| **Match Exclusion** | ✅ Limited | ✅ Per-match with reason + score recalculation |
| **Faculty Annotations** | ❌ No | ✅ Per-match comments |
| **Internal Archive** | ❌ No (cloud-only) | ✅ Local, private institutional archive |
| **Privacy** | ❌ Cloud-based, data shared | ✅ Local-first, no data leaves the server |
| **PDF Report** | ✅ Basic | ✅ Comprehensive with cover page, charts, match details |
| **JSON Export** | ❌ No | ✅ Full machine-readable export |
| **Digital Signature** | ❌ No | ✅ Faculty review with digital signature |
| **Batch Comparison** | ❌ No direct support | ✅ Course-wide peer comparison |
| **Real-time Progress** | ✅ Basic | ✅ WebSocket with per-stage progress |

---

## 2. Report Data Model

### 2.1 Report JSON Structure (Complete)

```json
{
  "document_id": "uuid",
  "document_title": "Analysis of Deep Learning...",
  "document_author": "J. Doe",
  "page_count": 48,
  "analyzed_at": "2026-04-09T10:05:00Z",
  "processing_time_seconds": 154,

  "scores": {
    "originality_score": 32.0,
    "similarity_score": 68.0,
    "risk_level": "high",
    "internal_contribution": 42.0,
    "web_contribution": 26.0
  },

  "summary_stats": {
    "total_matches": 12,
    "internal_exact": 3,
    "internal_paraphrase": 4,
    "web_matches": 5,
    "unique_sources": 6,
    "avg_match_length_words": 45,
    "longest_match_words": 120,
    "longest_match_page": 12,
    "pages_with_matches": 8,
    "total_pages": 48,
    "excluded_matches": 0,
    "coherent_domains": ["medium.com"]
  },

  "sources": [
    {
      "id": "src-uuid",
      "type": "internal",
      "name": "Thesis_2024_KWest.pdf",
      "document_id": "uuid-of-source-doc",
      "url": null,
      "domain": null,
      "coverage_percent": 18.4,
      "match_count": 3,
      "pages_affected": [12, 14, 30]
    },
    {
      "id": "src-uuid-2",
      "type": "web",
      "name": "medium.com",
      "document_id": null,
      "url": "https://medium.com/...",
      "domain": "medium.com",
      "coverage_percent": 8.2,
      "match_count": 2,
      "pages_affected": [28, 29],
      "is_coherent_source": true
    }
  ],

  "matches": [
    {
      "id": "match-uuid",
      "type": "internal_exact",
      "source_id": "src-uuid",
      "submitted_text": "The data clearly shows a linear trend...",
      "submitted_page": 12,
      "submitted_start_char": 1450,
      "submitted_end_char": 1580,
      "source_text": "The data clearly shows a linear trend...",
      "source_page": 8,
      "similarity_score": 0.95,
      "match_length_words": 45,
      "is_excluded": false,
      "exclude_reason": null,
      "faculty_comment": null,
      "color_code": "#ef4444"
    }
  ],

  "heatmap": [
    {
      "page": 1,
      "match_density": 0.0,
      "internal_density": 0.0,
      "web_density": 0.0,
      "color": "#22c55e",
      "match_count": 0
    },
    {
      "page": 12,
      "match_density": 0.85,
      "internal_density": 0.72,
      "web_density": 0.13,
      "color": "#ef4444",
      "match_count": 5
    }
  ],

  "page_distribution": [
    {"page": 1, "internal_exact": 0, "internal_paraphrase": 0, "web": 0},
    {"page": 12, "internal_exact": 2, "internal_paraphrase": 1, "web": 2}
  ],

  "review": {
    "status": "unreviewed",
    "reviewed_by": null,
    "reviewed_at": null,
    "faculty_notes": null,
    "verdict": null
  }
}
```

---

## 3. Color System

### 3.1 Match Type Colors
| Match Type | Color Name | Hex | Usage |
|---|---|---|---|
| Internal Exact Copy | Red | `#ef4444` | Text overlay, heatmap, match card border |
| Internal Paraphrase | Orange | `#f97316` | Text overlay, heatmap, match card border |
| Web Match | Blue | `#3b82f6` | Text overlay, heatmap, match card border |
| Original/Clean | Green | `#22c55e` | Heatmap clean pages, originality badge |
| Excluded Match | Gray | `#9ca3af` | Struck-through in overlay, dimmed in list |

### 3.2 Risk Level Colors
| Risk Level | Threshold | Color | Badge |
|---|---|---|---|
| HIGH | Originality < 50% | Red `#ef4444` | 🔴 |
| MODERATE | 50% – 80% | Yellow `#eab308` | 🟡 |
| LOW | > 80% | Green `#22c55e` | 🟢 |

### 3.3 Heatmap Gradient
Continuous gradient from Green (0% density) → Yellow (25%) → Orange (50%) → Red (100%):
- `0.00` → `#22c55e`
- `0.25` → `#eab308`
- `0.50` → `#f97316`
- `0.75` → `#ef4444`
- `1.00` → `#dc2626`

---

## 4. Report Components Specification

### 4.1 ScoreHeader Component
**Purpose:** The headline area showing the overall result.

**Elements:**
- Originality Score (large number, color-coded by risk level)
- Risk Level badge (🔴🟡🟢)
- Summary stats row: total matches, unique sources, pages affected
- Internal vs. Web breakdown bar
- Action buttons: Export PDF, Export JSON, Print, Mark Reviewed

### 4.2 Heatmap Component
**Purpose:** Visual page-by-page overview — like a fingerprint of the document.

**Behavior:**
- Displays a horizontal strip of page thumbnails (small rectangles).
- Each rectangle is colored by match density (see gradient above).
- Hovering shows tooltip: "Page 12: 85% match density (3 internal, 2 web)."
- Clicking scrolls the document view to that page.
- Can toggle between "All Matches" / "Internal Only" / "Web Only" views.

### 4.3 TextOverlay Component
**Purpose:** The full document text with inline color highlights.

**Behavior:**
- Renders the submitted PDF text page-by-page.
- Matched segments are highlighted with the appropriate match type color.
- Clicking a highlighted segment selects it in the Findings panel and loads evidence in the Evidence panel.
- Excluded matches shown with strikethrough + gray.
- Current page indicator synced with heatmap.

### 4.4 DiffViewer Component
**Purpose:** Side-by-side comparison of submitted text vs. source text.

**Behavior:**
- Left panel: submitted text with the matched segment highlighted.
- Right panel: source text with the corresponding segment highlighted.
- Word-level alignment showing exact matching words vs. changed words.
- Similarity score badge.
- Source metadata (document name, page, author for internal; URL, domain for web).

### 4.5 SourcePanel Component
**Purpose:** Ranked list of all sources contributing to the similarity score.

**Elements:**
- Sortable table: rank, type icon, source name, coverage %, match count.
- Coverage bar visualization for each source.
- Clicking a source filters the document view to show only that source's matches.
- "Coherent Source" badge for domains with ≥3 matches.

### 4.6 Charts Components
**Pie Chart (Source Breakdown):**
- Slices grouped by source, colored by match type.
- "Original" slice in green.
- Interactive: clicking a slice highlights those matches.

**Bar Chart (Page Distribution):**
- X-axis: page numbers (1–N).
- Y-axis: total match count.
- Stacked bars colored by match type (red/orange/blue).
- Clickable: navigates to that page.

### 4.7 MatchCard Component
**Purpose:** Detailed view of a single match finding.

**Elements:**
- Match type badge + color indicator.
- Submitted text excerpt (≤100 words, with "…" truncation).
- Source text excerpt.
- Page number + similarity score.
- Action buttons: "Exclude Match" (with reason dropdown), "Add Comment."
- Excluded state: dimmed, with "Restore" option.

### 4.8 FilterBar Component
**Purpose:** Toggle visibility of match types.

**Toggles:**
- [x] All
- [ ] Internal Exact (count)
- [ ] Internal Paraphrase (count)
- [ ] Web Match (count)
- [ ] Excluded (count)

---

## 5. PDF Export Specification

### 5.1 Pages

**Page 1 — Cover:**
- University/institution logo (configurable).
- Title: "ALETHIAN PLAGIARISM REPORT."
- Document title, author, date.
- Originality Score (large), Risk Level.
- Summary stats table.
- Review fields (Reviewer, Date, Signature — blank for signing).

**Page 2 — Source Summary:**
- Source Breakdown pie chart (rendered as image).
- Page Distribution bar chart (rendered as image).
- Heatmap strip (rendered as image).
- Full source table.

**Pages 3+ — Match Details:**
- One match per block (2–3 per page).
- Each block: match type, page, similarity score, submitted text, source text, source metadata.
- If the match was excluded: shown with strikethrough + exclusion reason.
- If the match has a faculty comment: shown below the match.

**Last Page — Footer:**
- Report generation timestamp.
- Hash for integrity verification.
- "Generated by Alethian v2.0 — Local-First Plagiarism Detection."

### 5.2 Styling
- Clean, professional, Arial/Helvetica font.
- A4/Letter compatible margins.
- Header on every page: "Alethian Report — [Document Title] — Page X/Y."
- Color-coded inline highlights in match excerpts.
