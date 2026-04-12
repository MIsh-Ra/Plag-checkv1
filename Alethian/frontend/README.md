# Alethian Frontend

React 19 single-page application built with Vite, TailwindCSS, and Zustand.

---

## Setup

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## Pages

| Page | Route | Description |
|:-----|:------|:------------|
| **Login** | `/` | Email/password authentication form |
| **Dashboard** | `/dashboard` | Document list with status badges, upload button, filters |
| **Report View** | `/report/:id` | Full originality report with interactive components |
| **Admin Panel** | `/admin` | System configuration (admin-only) |

---

## Component Architecture

### Report View Components

```
ReportView
├── ScoreHeader          # Originality %, risk badge, processing time
├── PieChart             # Source type distribution (internal vs web)
├── FilterBar            # Filter matches by type, severity, page
├── MatchCard[]          # Individual match with submitted ↔ source text
│   └── DiffViewer       # Word-level LCS diff with ins/del highlighting
├── Heatmap              # Page-level density visualization
├── BarChart             # Per-page match distribution
├── SourcePanel          # Source list with coverage details
├── TextOverlay          # Full document with highlighted match regions
└── ExportMenu           # PDF/JSON export + review submission
```

### DiffViewer — Word-Level Diff (M-06)

The `DiffViewer` component uses a **Longest Common Subsequence (LCS)** algorithm to compute word-level differences between submitted and source text:

```
Submitted:  "Data mining involves discovering patterns in large datasets"
Source:     "Data mining is the process of discovering patterns in big datasets"

Left:   Data mining [involves] discovering patterns in [large] datasets
Right:  Data mining [is the process of] discovering patterns in [big] datasets
                     ↑ inserted                              ↑ changed
```

- **`<del>` tags** (red background) — words present in submitted but not source
- **`<ins>` tags** (green background) — words present in source but not submitted
- **Plain text** — words common to both (LCS matches)

---

## State Management

Uses **Zustand** for lightweight global state:

```javascript
// stores/reportStore.js
{
  report: null,           // Full report data from API
  selectedMatchId: null,  // Currently focused match
  filters: {              // Active filter state
    type: 'all',
    severity: 'all',
    page: null
  },
  setReport,
  setSelectedMatch,
  setFilters
}
```

---

## API Client

```javascript
// api/client.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
});

// Automatically attaches JWT from localStorage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
```

---

## WebSocket Integration

The `useWebSocket` hook connects to the backend's real-time status endpoint:

```javascript
// hooks/useWebSocket.js
const ws = new WebSocket(`ws://localhost:8000/api/v1/documents/${docId}/status`);

ws.onmessage = (event) => {
  const { stage, progress, message } = JSON.parse(event.data);
  // stage: "ingesting" | "internal_similarity" | "web_dragnet" | "report_generation" | "complete"
  // progress: 10 | 40 | 60 | 85 | 100
};
```

---

## Testing

```bash
# Run all frontend tests
npm test -- --run

# Watch mode
npm test
```

### Test Files

| Test File | Component | Tests |
|:----------|:----------|------:|
| `Login.test.jsx` | Login page | 2 |
| `Dashboard.test.jsx` | Dashboard | 1 |
| `ReportView.test.jsx` | Report view | 2 |
| `MatchCard.test.jsx` | Match card | 2 |
| `FilterBar.test.jsx` | Filter bar | 1 |
| `ExportMenu.test.jsx` | Export menu | 1 |
| `reportStore.test.js` | Zustand store | 2 |
| `client.test.js` | API client | 1 |
| **Total** | | **12** |

---

## Build for Production

```bash
npm run build
# Output in dist/
# Serve with any static file server (Nginx, Caddy, etc.)
```
