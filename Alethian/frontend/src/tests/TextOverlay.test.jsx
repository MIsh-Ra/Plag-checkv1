import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import TextOverlay from '../components/report/TextOverlay';
import * as ReportStore from '../stores/reportStore';

vi.mock('../stores/reportStore', () => ({
  useReportStore: vi.fn(),
}));

describe('TextOverlay Component', () => {
    it('renders exact spans and handles clicks correctly', () => {
        const setSelectedMatch = vi.fn();
        ReportStore.useReportStore.mockReturnValue({
            currentPage: 1,
            setSelectedMatch,
            selectedMatchId: null
        });

        const text = "This is the source document text that we will test.";
        const matches = [
            { id: '1', submitted_start_char: 12, submitted_text: "source document", type: "internal_exact" }
        ];

        const { container } = render(<TextOverlay text={text} matches={matches} />);
        
        // Assert full text exists
        expect(screen.getByText(/This is the/)).toBeInTheDocument();
        
        // Assert mark generated
        const marks = container.querySelectorAll('mark');
        expect(marks.length).toBe(1);
        expect(marks[0].textContent).toBe('source document');
        expect(marks[0].className).toContain('bg-error-container/30'); // Exact match color (forensic design system)
        
        // Assert click behavior
        fireEvent.click(marks[0]);
        expect(setSelectedMatch).toHaveBeenCalledWith('1');
    });
});
