import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../pages/Dashboard';
import Client from '../api/client';

vi.mock('../api/client', () => ({
  default: {
    documents: {
      list: vi.fn(),
    }
  }
}));

// Mock useWebSocket since it tries to open a real WS connection
vi.mock('../hooks/useWebSocket', () => ({
  useWebSocket: () => ({ status: 'idle', stage: null, progress: 0, message: '' })
}));

// Provide localStorage stub for jsdom
beforeEach(() => {
    const store = {};
    vi.stubGlobal('localStorage', {
        getItem: vi.fn((key) => store[key] || null),
        setItem: vi.fn((key, val) => { store[key] = val; }),
        removeItem: vi.fn((key) => { delete store[key]; }),
        clear: vi.fn(() => { Object.keys(store).forEach(k => delete store[k]); }),
    });
});

describe('Dashboard Component', () => {
    it('loads and displays documents', async () => {
        Client.documents.list.mockResolvedValue({
            items: [
                { id: '1', title: 'Doc 1', filename: 'doc1.pdf', status: 'complete', originality_score: 90, upload_date: '2024-01-01T00:00:00' }
            ],
            total: 1
        });

        render(<BrowserRouter><Dashboard /></BrowserRouter>);

        await waitFor(() => {
            expect(screen.getByText('Doc 1')).toBeInTheDocument();
        });
    });
});
