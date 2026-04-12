import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import ReportView from '../pages/ReportView';
import { useParams, useNavigate } from 'react-router-dom';

vi.mock('react-router-dom', () => ({
  useParams: vi.fn(),
  useNavigate: vi.fn(() => vi.fn()),
}));

// useReport is a NAMED export, not default — the mock must return { useReport }
vi.mock('../hooks/useReport', () => ({
  useReport: vi.fn(),
}));

// Mock the Zustand store
vi.mock('../stores/reportStore', () => ({
  useReportStore: vi.fn(() => ({
    selectedMatchId: null,
    filterTypes: { internal_exact: true, internal_paraphrase: true, web: true, excluded: false },
  })),
}));

// Mock heavy sub-components to keep tests focused
vi.mock('../components/report/DiffViewer', () => ({
  default: () => <div data-testid="diff-viewer" />
}));
vi.mock('../components/report/TextOverlay', () => ({
  default: () => <div data-testid="text-overlay" />
}));
vi.mock('../components/report/ScoreHeader', () => ({
  default: () => <div data-testid="score-header" />
}));
vi.mock('../components/report/Heatmap', () => ({
  default: () => <div data-testid="heatmap" />
}));
vi.mock('../components/report/SourcePanel', () => ({
  default: () => <div data-testid="source-panel" />
}));
vi.mock('../components/report/FilterBar', () => ({
  default: () => <div data-testid="filter-bar" />
}));
vi.mock('../components/report/MatchCard', () => ({
  default: () => <div data-testid="match-card" />
}));
vi.mock('../components/report/PieChart', () => ({
  default: () => <div data-testid="pie-chart" />
}));
vi.mock('../components/report/BarChart', () => ({
  default: () => <div data-testid="bar-chart" />
}));
vi.mock('../components/report/ExportMenu', () => ({
  default: () => <div data-testid="export-menu" />
}));

describe('ReportView Component', () => {
    it('shows loading state initially', async () => {
        useParams.mockReturnValue({ id: '123' });

        // Import the mocked module to control return value
        const { useReport } = await import('../hooks/useReport');
        useReport.mockReturnValue({ report: null, loading: true, setReport: vi.fn() });

        render(<ReportView />);
        expect(screen.getByText(/Loading Report/i)).toBeInTheDocument();
    });

    it('renders report data when loaded', async () => {
        useParams.mockReturnValue({ id: '123' });

        const { useReport } = await import('../hooks/useReport');
        useReport.mockReturnValue({
            report: {
                matches: [],
                scores: { originality_score: 95, risk_level: 'low', similarity_score: 5 },
                heatmap: [],
                source_breakdown: [],
                page_distribution: [],
                summary_stats: {},
            },
            loading: false,
            setReport: vi.fn(),
        });

        render(<ReportView />);
        expect(screen.getByTestId('text-overlay')).toBeInTheDocument();
    });
});
