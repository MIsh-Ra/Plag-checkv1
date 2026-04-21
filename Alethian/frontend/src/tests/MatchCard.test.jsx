import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import MatchCard from '../components/report/MatchCard';
import Client from '../api/client';
import { BrowserRouter } from 'react-router-dom';

vi.mock('../api/client', () => ({
  default: {
    reports: {
      excludeMatch: vi.fn().mockResolvedValue({}),
      commentMatch: vi.fn().mockResolvedValue({}),
    }
  }
}));

describe('MatchCard Component', () => {
    const mockMatch = {
        id: 'match-1',
        type: 'web',
        similarity: 85,
        submitted_text: 'Matched text',
        submitted_page: 1,
        is_excluded: false
    };

    it('renders match details correctly', () => {
        render(<BrowserRouter><MatchCard match={mockMatch} /></BrowserRouter>);
        expect(screen.getByText(/Matched text/i)).toBeInTheDocument();
        expect(screen.getByText('85%')).toBeInTheDocument();
    });

    it('handles exclude interaction', () => {
        // mock window.location.reload
        const originalLocation = window.location;
        delete window.location;
        window.location = { reload: vi.fn() };

        render(<BrowserRouter><MatchCard match={mockMatch} /></BrowserRouter>);
        fireEvent.click(screen.getByText('EXCLUDE'));
        expect(Client.reports.excludeMatch).toHaveBeenCalled();
        
        window.location = originalLocation;
    });

    it('handles inline comment interaction and display', async () => {
        const originalLocation = window.location;
        delete window.location;
        window.location = { reload: vi.fn() };

        // Test display of existing comment
        const matchWithComment = { ...mockMatch, comment: "Needs review" };
        const { rerender } = render(<BrowserRouter><MatchCard match={matchWithComment} /></BrowserRouter>);
        expect(screen.getByText('Needs review')).toBeInTheDocument();

        // Test opening the editor
        fireEvent.click(screen.getByText('COMMENT'));
        const textarea = screen.getByPlaceholderText('ENTER TRIAGE LOG...');
        expect(textarea).toBeInTheDocument();

        // Test typing and saving
        fireEvent.change(textarea, { target: { value: 'This is my new comment' } });
        fireEvent.click(screen.getByText('SAVE LOG'));

        await waitFor(() => {
            expect(Client.reports.commentMatch).toHaveBeenCalledWith(undefined, 'match-1', 'This is my new comment');
        });
        
        window.location = originalLocation;
    });
});
