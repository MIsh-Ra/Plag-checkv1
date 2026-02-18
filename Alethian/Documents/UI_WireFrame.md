# Alethian UI Wireframes

This document contains low-fidelity ASCII wireframes for the core user interfaces of the Alethian Research Integrity System.

## 1. Landing / Login Page
**Goal:** Clean, institutional entry point. Focus on privacy and simplicity.

```text
+--------------------------------------------------------------------------+
|  [Alethian Logo]                                                         |
+--------------------------------------------------------------------------+
|                                                                          |
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
|                                                                          |
|                                                                          |
+--------------------------------------------------------------------------+
|  Local-First Research Integrity System v1.0   |   Privacy Policy         |
+--------------------------------------------------------------------------+
```

## 2. Faculty Dashboard (Home)
**Goal:** Overview of recent work and quick access to start new analysis.

```text
+--------------------------------------------------------------------------+
| Alethian    [Dashboard]   [Archive]   [Admin]         (User Profile v)   |
+--------------------------------------------------------------------------+
|                                                                          |
|  +--------------------------------------------------------------------+  |
|  |  New Submission                                                    |  |
|  |  +--------------------------------------------------------------+  |  |
|  |  |                                                              |  |  |
|  |  |         [ Icon: File Upload ]                                |  |  |
|  |  |                                                              |  |  |
|  |  |   Drag and drop PDF thesis here, or click to browse          |  |  |
|  |  |                                                              |  |  |
|  |  +--------------------------------------------------------------+  |  |
|  +--------------------------------------------------------------------+  |
|                                                                          |
|  Recent Analyses                                                         |
|  +--------------------------------------------------------------------+  |
|  | Status     | Title                     | Author       | Score | Act|  |
|  +--------------------------------------------------------------------+  |
|  | [COMPLETE] | Analysis of Deep Learning.| J. Doe       | [ 85] | [>]|  |
|  |            | (Found 3 Critical Issues) |              |       |    |  |
|  +--------------------------------------------------------------------+  |
|  | [INGESTING]| Modern History of...      | A. Smith     | [---] |    |  |
|  | [====....] | Parsing PDF Structure...  |              |       |    |  |
|  +--------------------------------------------------------------------+  |
|  | [READY]    | Quantum Computing...      | B. Wayne     | [100] | [>]|  |
|  |            | (No Issues Found)         |              |       |    |  |
|  +--------------------------------------------------------------------+  |
|                                                                          |
+--------------------------------------------------------------------------+
```

## 3. Deep Scan Report (The Workspace)
**Goal:** Detailed forensic analysis. Side-by-side verification is the core feature.

```text
+--------------------------------------------------------------------------+
| < Back  |  Analysis of Deep Learning.. (J. Doe)       [ Export PDF v ]   |
|         |  Score: 85/100 (Suspect)                    [ Mark Reviewed]   |
+--------------------------------------------------------------------------+
| Findings (Filter)      |  Document View           | Evidence Context     |
| [x] All                |                          |                      |
| [ ] Citations (2)      | ...rapid advances in AR  | [Semantic Scholar]   |
| [ ] Internal (1)       | have led to new privacy  |                      |
| [ ] Web (1)            | concerns. As noted by    | Title: AR Privacy    |
| [ ] AI Forensics (0)   | [Wong et al., 2023], the | Authors: Wong, Li    |
|                        | field is evolving.       | Year: 2023           |
| LIST ------------------+                          | Status: [VERIFIED]   |
| [RED] Hallucination    | However, the seminal     |                      |
| pg 12 - "Smith 2029"   | work by [Smith 2029]     | [!] HALLUCINATION    |
|                        | argues that privacy is   | No record found in   |
| [YEL] Paraphrase       | dead. >>> [HIGHLIGHT]    | global database.     |
| pg 45 - vs Local DB    |                          |                      |
|                        +--------------------------+----------------------+ |
| [GRN] Verified         | ...moreover, the data    | [Local Archive]      |
| pg 3 - Wong et al.     | clearly shows a linear   | Match: Thesis_2021   |
|                        | trend in user adoption.  | (Sim: 92%)           |
|                        | This specific pattern    | Student: K. West     |
|                        | was previously observed  |                      |
|                        | in early mobile era...   | "...data shows a     |
|                        | >>> [HIGHLIGHT]          | linear trend..."     |
|                        |                          |                      |
+------------------------+--------------------------+----------------------+
```

## 4. Admin Configuration Panel
**Goal:** System control and transparency.

```text
+--------------------------------------------------------------------------+
| Alethian Admin Panel                                     [ Save Changes ]|
+--------------------------------------------------------------------------+
| [ General ]  [ API Keys ]  [ Thresholds ]  [ Users ]                     |
|                                                                          |
| API Configuration                                                        |
| Manage connections to the external research and search mesh.             |
|                                                                          |
| +----------------------------------------------------------------------+ |
| | Semantic Scholar API Key                                             | |
| | [ sk-........................................... ] [ Test ] [ OK ]   | |
| +----------------------------------------------------------------------+ |
|                                                                          |
| +----------------------------------------------------------------------+ |
| | Serper.dev API Key (Google Search)                                   | |
| | [ .............................................. ] [ Test ] [Fail]   | |
| | (!) Invalid Key or Quota Exceeded                                    | |
| +----------------------------------------------------------------------+ |
|                                                                          |
| +----------------------------------------------------------------------+ |
| | Unpaywall Email (For Good Citizen Policy)                            | |
| | [ admin@university.edu ......................... ]                   | |
| +----------------------------------------------------------------------+ |
|                                                                          |
| Rate Limits                                                              |
| [x] Throttle background jobs to prevent API bans                         |
| Max Requests/Min: [ 60 ]                                                 |
|                                                                          |
+--------------------------------------------------------------------------+
```

## 5. Mobile / Tablet View (Responsive)
**Goal:** Quick status check on the go.

```text
+-----------------------------+
| [=] Alethian                |
+-----------------------------+
| Welcome, Prof. X            |
|                             |
| Recent Activity             |
| +-------------------------+ |
| | Analysis of Deep...     | |
| | [ 85 ] [ Review > ]     | |
| +-------------------------+ |
|                             |
| +-------------------------+ |
| | Quantum Computing       | |
| | [ 100] [ Done >   ]     | |
| +-------------------------+ |
|                             |
| [ + New Scan ]              |
|                             |
+-----------------------------+
```
