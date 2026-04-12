import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
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
        fireEvent.click(screen.getByText('Exclude'));
        expect(Client.reports.excludeMatch).toHaveBeenCalled();
        
        window.location = originalLocation;
    });
});
