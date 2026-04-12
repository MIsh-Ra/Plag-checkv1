import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ExportMenu from '../components/report/ExportMenu';
import Client from '../api/client';

vi.mock('../api/client', () => ({
  default: {
    reports: {
      exportPdf: vi.fn(),
    }
  }
}));

describe('ExportMenu Component', () => {
    it('renders export buttons', () => {
        render(<ExportMenu />);
        expect(screen.getByText('Export PDF')).toBeInTheDocument();
    });

    it('triggers pdf export on click', async () => {
        Client.reports.exportPdf.mockResolvedValue({});
        const alertMock = vi.spyOn(window, 'alert').mockImplementation(() => {});

        render(<ExportMenu />);
        fireEvent.click(screen.getByText('Export PDF'));

        await waitFor(() => {
            expect(Client.reports.exportPdf).toHaveBeenCalled();
        });
        
        alertMock.mockRestore();
    });
    
    it('handles pdf export failure gracefully', async () => {
        Client.reports.exportPdf.mockRejectedValue(new Error("Net error"));
        const alertMock = vi.spyOn(window, 'alert').mockImplementation(() => {});
        const consoleMock = vi.spyOn(console, 'error').mockImplementation(() => {});

        render(<ExportMenu />);
        fireEvent.click(screen.getByText('Export PDF'));

        await waitFor(() => {
            expect(alertMock).toHaveBeenCalledWith('PDF export failed. Please try again.');
        });
        
        alertMock.mockRestore();
        consoleMock.mockRestore();
    });
});
