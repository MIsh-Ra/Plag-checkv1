# Alethian UI Wireframes v2.0

This document contains low-fidelity ASCII wireframes for the core user interfaces of the Alethian v2 Plagiarism Detection System, with a heavy focus on the **Report View** — designed to be more expressive and thorough than Turnitin.

## 1. Landing / Login Page
**Goal:** Clean, institutional entry point emphasizing privacy.

```text
+--------------------------------------------------------------------------+
|  [Alethian Logo]         Local-First Plagiarism Detection                 |
+--------------------------------------------------------------------------+
|                                                                          |
|          +----------------------------------------------------+          |
|          |                                                    |          |
|          |             Sign in to Alethian                    |          |
|          |                                                    |          |
|          |   +--------------------------------------------+   |          |
|          |   |  Email Address                             |   |          |
|          |   +--------------------------------------------+   |          |
|          |                                                    |          |
|          |   +--------------------------------------------+   |          |
|          |   |  Password                                  |   |          |
|          |   +--------------------------------------------+   |          |
|          |                                                    |          |
|          |   [ Sign In ]                                      |          |
|          |                                                    |          |
|          |   ---------------- OR ------------------           |          |
|          |                                                    |          |
|          |   [ Continue with Institutional SSO (SAML) ]       |          |
|          |                                                    |          |
|          +----------------------------------------------------+          |
|                                                                          |
|   🔒 Your documents never leave this server.                             |
|                                                                          |
+--------------------------------------------------------------------------+
|  Alethian v2.0   |   Privacy Policy   |   Documentation                  |
+--------------------------------------------------------------------------+
```

## 2. Faculty Dashboard (Home)
**Goal:** Overview of submissions, quick upload, at-a-glance risk assessment.

```text
+--------------------------------------------------------------------------+
| Alethian    [Dashboard]   [Archive]   [Admin]         (Prof. X ▼)        |
+--------------------------------------------------------------------------+
|                                                                          |
|  +--------------------------------------------------------------------+  |
|  |  New Submission                                                    |  |
|  |  +--------------------------------------------------------------+  |  |
|  |  |                                                              |  |  |
|  |  |         [ Icon: File Upload ]                                |  |  |
|  |  |                                                              |  |  |
|  |  |   Drag and drop PDF thesis here, or click to browse          |  |  |
|  |  |   Max 100MB  •  PDF only                                     |  |  |
|  |  |                                                              |  |  |
|  |  |   Course ID (optional): [________________]                   |  |  |
|  |  |                                                              |  |  |
|  |  +--------------------------------------------------------------+  |  |
|  +--------------------------------------------------------------------+  |
|                                                                          |
|  Recent Analyses                                    [Filter: All ▼]      |
|  +--------------------------------------------------------------------+  |
|  | Risk  | Title                     | Author     | Score  | Status   |  |
|  +--------------------------------------------------------------------+  |
|  | [🔴] | Analysis of Deep Learning.| J. Doe     | [32%]  | COMPLETE |  |
|  |       | 12 matches • 6 sources    |            |        | [View >] |  |
|  +--------------------------------------------------------------------+  |
|  | [🟡] | Modern History of...      | A. Smith   | [78%]  | COMPLETE |  |
|  |       | 4 matches • 2 sources     |            |        | [View >] |  |
|  +--------------------------------------------------------------------+  |
|  | [⏳] | Quantum Computing...      | B. Wayne   | [---]  | ANALYZING|  |
|  |       | [========>.......] Internal Similarity 65%       |          |  |
|  +--------------------------------------------------------------------+  |
|  | [🟢] | Machine Learning in...    | C. Kent    | [96%]  | REVIEWED |  |
|  |       | 1 match (excluded)        |            |        | [View >] |  |
|  +--------------------------------------------------------------------+  |
|                                                                          |
+--------------------------------------------------------------------------+
```

### Risk Level Legend
```text
🔴 HIGH RISK    (Originality < 50%)   — Requires immediate review
🟡 MODERATE     (50% - 80%)          — Some matches found
🟢 LOW RISK     (> 80%)              — Mostly original
⏳ PROCESSING   — Analysis in progress
```

## 3. Report View — The Workspace (Better-Than-Turnitin)
**Goal:** Forensic-grade analysis. Three-panel layout with heatmap, charts, and deep evidence.

### 3.1 Report Header

```text
+--------------------------------------------------------------------------+
| < Back  |  Analysis of Deep Learning.. (J. Doe)                          |
|         |                                                                |
|         |  +----------------------------------------------------------+  |
|         |  |  ORIGINALITY SCORE         RISK LEVEL        MATCHES    |  |
|         |  |      [ 32% ]               [🔴 HIGH]       12 total    |  |
|         |  |                                                          |  |
|         |  |  Internal: 7 (3 exact, 4 paraphrase)  •  Web: 5         |  |
|         |  |  Unique Sources: 6  •  Pages Affected: 8/48             |  |
|         |  +----------------------------------------------------------+  |
|         |                                                                |
|         |  [ Export PDF ▼ ]  [ Export JSON ]  [ Print ]  [ Mark Reviewed ]|
+--------------------------------------------------------------------------+
```

### 3.2 Page Heatmap Strip

```text
+--------------------------------------------------------------------------+
|  DOCUMENT HEATMAP  (click to jump)                                       |
|  +----+----+----+----+----+----+----+----+----+----+----+----+           |
|  | p1 | p2 | p3 | p4 | p5 | p6 | p7 | p8 | p9 |p10 |p11 |p12 |  ...  |
|  |    |████|    |    |████|    |    |    |    |    |    |████|           |
|  |    |RED |    |    |ORG |    |    |    |    |    |    |BLU |           |
|  +----+----+----+----+----+----+----+----+----+----+----+----+           |
|                                                                          |
|  Legend: ██ High Density  ▓▓ Medium  ░░ Low  [  ] Clean                  |
|  Color:  Red=Internal Exact  Orange=Paraphrase  Blue=Web Match           |
+--------------------------------------------------------------------------+
```

### 3.3 Main Three-Panel Layout

```text
+------------------------+--------------------------+----------------------+
| FINDINGS               | DOCUMENT TEXT             | EVIDENCE CONTEXT     |
| (Filter & Navigate)    | (Color Overlay)          | (Source Detail)       |
+------------------------+--------------------------+----------------------+
|                        |                          |                      |
| Filter:                | Page 12 of 48            |                      |
| [x] All (12)           |                          |                      |
| [ ] Internal Exact (3) | ...rapid advances in     |                      |
| [ ] Paraphrase (4)     | machine learning have    |                      |
| [ ] Web Match (5)      | led to transformative    |                      |
|                        | changes across industry. |                      |
| MATCH LIST ----------- |                          |                      |
|                        | >>>HIGHLIGHT (RED)<<<    | [Internal Archive]   |
| [🔴] Exact Match       | The data clearly shows   | Source: Thesis_2024  |
| pg 12 — 95% match     | a linear trend in user   | Author: K. West      |
| vs Thesis_2024         | adoption. This specific  | Page: 8              |
| "The data clearly..."  | pattern was previously   | Sim: 95%             |
|                        | observed in early mobile | Type: Exact Copy     |
| [🟠] Paraphrase        | era studies that were    |                      |
| pg 14 — 87% match     | conducted by several     | "The data clearly    |
| vs Report_2023         | independent research     | shows a linear trend |
| "studies demonstrate..." | groups across...        | in user adoption.    |
|                        | >>>END HIGHLIGHT<<<      | This specific        |
| [🔵] Web Match          |                          | pattern was..."      |
| pg 28 — 91% match     | The researchers then     |                      |
| medium.com/article     | applied novel techniques | [👁 View Full Source] |
| "novel techniques..."   | to the dataset,         | [✗ Exclude Match]    |
|                        | achieving unprecedented  | [💬 Add Comment]     |
| [🟠] Paraphrase        | levels of accuracy. This |                      |
| pg 30 — 86% match     | methodology was first    |                      |
| vs Thesis_2022         | pioneered by the work of |                      |
|                        | several teams who...     |                      |
|                        |                          |                      |
+------------------------+--------------------------+----------------------+
```

### 3.4 Source Summary Panel (Collapsible)

```text
+--------------------------------------------------------------------------+
|  📊 SOURCE BREAKDOWN                                           [Collapse] |
|                                                                          |
|  +----------------------------------+  +-------------------------------+ |
|  | Source Pie Chart                 |  | Match Distribution (bar)      | |
|  |                                  |  |                               | |
|  |         ████                     |  | p1  |                         | |
|  |       ██    ██  Thesis_2024:18%  |  | p2  |████████ (3)            | |
|  |     ██ Other  ██ medium.com: 8%  |  | p5  |████ (2)               | |
|  |     ██ 68%   ██  Report_2023:6%  |  | p12 |██████████████ (5)     | |
|  |       ██    ██                   |  | p14 |██████ (3)             | |
|  |         ████                     |  | p28 |████████ (3)            | |
|  |                                  |  |                               | |
|  +----------------------------------+  +-------------------------------+ |
|                                                                          |
|  +--------------------------------------------------------------------+  |
|  | SOURCE TABLE                                                       |  |
|  +----+-----------+----------------------+----------+--------+--------+  |
|  | #  | Type      | Source Name          | Coverage | Matches| Pages  |  |
|  +----+-----------+----------------------+----------+--------+--------+  |
|  | 1  | Internal  | Thesis_2024_KWest    | 18.4%    | 3      | 3      |  |
|  | 2  | Web       | medium.com/article   | 8.2%     | 2      | 2      |  |
|  | 3  | Internal  | Report_2023_JSmith   | 6.1%     | 2      | 2      |  |
|  | 4  | Web       | stackoverflow.com    | 3.5%     | 2      | 1      |  |
|  | 5  | Internal  | Thesis_2022_BDoe     | 2.8%     | 2      | 2      |  |
|  | 6  | Web       | geeksforgeeks.org    | 1.0%     | 1      | 1      |  |
|  +----+-----------+----------------------+----------+--------+--------+  |
|                                                                          |
+--------------------------------------------------------------------------+
```

### 3.5 Summary Statistics Bar

```text
+--------------------------------------------------------------------------+
|  📈 ANALYSIS SUMMARY                                                      |
|                                                                          |
|  Total Matches:  12           Avg Match Length:  45 words                 |
|  Unique Sources: 6            Longest Match:     120 words (pg 12)       |
|  Internal:       7 (58%)      Web Matches:       5 (42%)                 |
|  Excluded:       0            Faculty Comments:  0                       |
|  Pages Affected: 8/48 (17%)   Processing Time:   2m 34s                  |
|                                                                          |
+--------------------------------------------------------------------------+
```

## 4. Report PDF Export Layout
**Goal:** Professional, branded, printable multi-page PDF.

```text
Page 1 (Cover):
+--------------------------------------------+
|                                            |
|   [University Logo]                        |
|                                            |
|   ALETHIAN PLAGIARISM REPORT               |
|                                            |
|   Document: Analysis of Deep Learning...   |
|   Author:   J. Doe                         |
|   Date:     April 9, 2026                  |
|                                            |
|   ┌──────────────────────────┐             |
|   │  ORIGINALITY SCORE: 32% │             |
|   │  RISK LEVEL: HIGH       │             |
|   └──────────────────────────┘             |
|                                            |
|   Total Matches: 12                        |
|   Unique Sources: 6                        |
|   Internal Matches: 7                      |
|   Web Matches: 5                           |
|                                            |
|   Reviewed by: ___________________         |
|   Date:        ___________________         |
|   Signature:   ___________________         |
|                                            |
+--------------------------------------------+

Page 2 (Source Summary):
+--------------------------------------------+
|   SOURCE SUMMARY                           |
|                                            |
|   [Pie Chart]        [Bar Chart]           |
|                                            |
|   Source Table (full table)                 |
|                                            |
|   [Heatmap Strip]                          |
|                                            |
+--------------------------------------------+

Pages 3+ (Match Details):
+--------------------------------------------+
|   MATCH DETAIL #1                          |
|   Type: Internal Exact Copy                |
|   Page: 12  |  Similarity: 95%             |
|   Source: Thesis_2024_KWest (Page 8)       |
|                                            |
|   Submitted Text:                          |
|   "The data clearly shows a linear         |
|   trend in user adoption..."               |
|                                            |
|   Source Text:                              |
|   "The data clearly shows a linear         |
|   trend in user adoption..."               |
|                                            |
|   Faculty Comment: (none)                  |
|   Status: Active                           |
|                                            |
|   ---                                      |
|                                            |
|   MATCH DETAIL #2                          |
|   ...                                      |
+--------------------------------------------+
```

## 5. Admin Configuration Panel
**Goal:** Simplified config for the reduced scope.

```text
+--------------------------------------------------------------------------+
| Alethian Admin Panel                                     [ Save Changes ]|
+--------------------------------------------------------------------------+
| [ General ]  [ API Keys ]  [ Thresholds ]  [ Users ]                     |
|                                                                          |
| Serper.dev API Key (Web Dragnet)                                         |
| +----------------------------------------------------------------------+ |
| | [ .............................................. ] [ Test ] [✅ OK ]  | |
| +----------------------------------------------------------------------+ |
|                                                                          |
| Similarity Thresholds                                                    |
| +----------------------------------------------------------------------+ |
| | MinHash Jaccard Threshold:     [====|========] 0.50                  | |
| | Semantic Cosine Threshold:     [========|====] 0.85                  | |
| | Web Match Threshold:           [======|======] 0.70                  | |
| +----------------------------------------------------------------------+ |
|                                                                          |
| Web Dragnet Settings                                                     |
| +----------------------------------------------------------------------+ |
| | [x] Enable Web Dragnet                                               | |
| | Max Queries per Document:  [ 20 ]                                    | |
| | Rate Limit (requests/min): [ 60 ]                                    | |
| +----------------------------------------------------------------------+ |
|                                                                          |
| Archive Statistics                                                       |
| +----------------------------------------------------------------------+ |
| | Total Archived Documents: 1,250                                      | |
| | Total Shingles Indexed:   450,000                                    | |
| | Last Indexed:             2026-04-08 22:00 UTC                       | |
| +----------------------------------------------------------------------+ |
|                                                                          |
+--------------------------------------------------------------------------+
```

## 6. Mobile / Tablet View (Responsive)
**Goal:** Quick status check on the go — no full report editing.

```text
+-----------------------------+
| [=] Alethian                |
+-----------------------------+
| Welcome, Prof. X            |
|                             |
| Recent Activity             |
| +-------------------------+ |
| | 🔴 Analysis of Deep...  | |
| | Score: 32%  [Review >]  | |
| +-------------------------+ |
|                             |
| +-------------------------+ |
| | 🟡 Modern History       | |
| | Score: 78%  [Review >]  | |
| +-------------------------+ |
|                             |
| +-------------------------+ |
| | 🟢 Machine Learning     | |
| | Score: 96%  [Done >]    | |
| +-------------------------+ |
|                             |
| [ + New Scan ]              |
|                             |
+-----------------------------+
```
