import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ExportMenu from '../components/report/ExportMenu';
import Client from '../api/client';

vi.mock('../api/client', () => ({
  default: {
    reports: {
      exportPdf: vi.fn(),
      exportJson: vi.fn(),
    }
  }
}));

const { mockHtml2Canvas, mockJsPdfSave, mockJsPdfAddImage } = vi.hoisted(() => ({
    mockHtml2Canvas: vi.fn().mockResolvedValue({
        toDataURL: vi.fn().mockReturnValue('data:image/jpeg;base64,...'),
        width: 800,
        height: 600
    }),
    mockJsPdfSave: vi.fn(),
    mockJsPdfAddImage: vi.fn()
}));

vi.mock('html2canvas', () => ({ default: mockHtml2Canvas }));

vi.mock('jspdf', () => ({
  jsPDF: vi.fn().mockImplementation(function() {
    this.internal = { pageSize: { getWidth: () => 210, getHeight: () => 297 } };
    this.getImageProperties = vi.fn().mockReturnValue({ width: 800, height: 600 });
    this.addImage = mockJsPdfAddImage;
    this.addPage = vi.fn();
    this.save = mockJsPdfSave;
    return this;
  })
}));

describe('ExportMenu Component', () => {
    it('renders export buttons', () => {
        render(<ExportMenu />);
        expect(screen.getByText('EXPORT PDF')).toBeInTheDocument();
    });

    it('triggers pdf export on click', async () => {
        // Mock the DOM element
        const mockElement = document.createElement('div');
        mockElement.id = 'alethian-report-container';
        document.body.appendChild(mockElement);

        render(<ExportMenu />);
        fireEvent.click(screen.getByText('EXPORT PDF'));

        await waitFor(() => {
            expect(mockHtml2Canvas).toHaveBeenCalledWith(mockElement, expect.any(Object));
            expect(mockJsPdfSave).toHaveBeenCalled();
        });
        
        document.body.removeChild(mockElement);
    });
    
    it('handles pdf export failure gracefully', async () => {
        const mockElement = document.createElement('div');
        mockElement.id = 'alethian-report-container';
        document.body.appendChild(mockElement);
        
        mockHtml2Canvas.mockRejectedValueOnce(new Error("Render error"));
        const alertMock = vi.spyOn(window, 'alert').mockImplementation(() => {});
        const consoleMock = vi.spyOn(console, 'error').mockImplementation(() => {});

        render(<ExportMenu />);
        fireEvent.click(screen.getByText('EXPORT PDF'));

        await waitFor(() => {
            expect(alertMock).toHaveBeenCalledWith('PDF export failed. Please try again.');
        });
        
        alertMock.mockRestore();
        consoleMock.mockRestore();
        document.body.removeChild(mockElement);
    });
});
