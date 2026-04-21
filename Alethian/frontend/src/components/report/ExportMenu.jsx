import { useState } from 'react';
import { Download, FileJson, Printer, Loader2 } from 'lucide-react';
import { useParams } from 'react-router-dom';
import Client from '../../api/client';

export default function ExportMenu() {
    const { id } = useParams();
    const [exporting, setExporting] = useState(null); // 'pdf' | 'json' | 'print' | null

    const handlePdfExport = async () => {
        if (exporting) return;
        setExporting('pdf');
        try {
            // Call the backend endpoint which returns a proper reportlab PDF
            const blob = await Client.reports.exportPdf(id);
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `alethian_report_${id.substring(0, 8)}.pdf`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(url);
        } catch (err) {
            console.error('PDF export failed:', err);
            alert('PDF export failed. Please try again.');
        } finally {
            setExporting(null);
        }
    };

    const handleJsonExport = async () => {
        if (exporting) return;
        setExporting('json');
        try {
            const data = await Client.reports.exportJson(id);
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `alethian_report_${id.substring(0, 8)}.json`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(url);
        } catch (err) {
            console.error('JSON export failed:', err);
            alert('JSON export failed. Please try again.');
        } finally {
            setExporting(null);
        }
    };

    const handlePrint = () => {
        window.print();
    };

    const btnBase = `inline-flex items-center px-3 py-2 text-xs font-mono font-bold tracking-widest uppercase
        border border-ghost bg-surface-container text-on-surface-variant
        hover:border-outline hover:text-on-surface transition-colors disabled:opacity-50`;

    return (
        <div className="flex items-center space-x-2">
            <button
                id="export-pdf-btn"
                onClick={handlePdfExport}
                disabled={!!exporting}
                title="Export full forensic PDF report"
                className={btnBase}
            >
                {exporting === 'pdf'
                    ? <Loader2 className="w-3 h-3 mr-2 animate-spin" />
                    : <Download className="w-3 h-3 mr-2" />}
                {exporting === 'pdf' ? 'GENERATING...' : 'EXPORT PDF'}
            </button>

            <button
                id="export-json-btn"
                onClick={handleJsonExport}
                disabled={!!exporting}
                title="Export report data as JSON"
                className={btnBase}
            >
                {exporting === 'json'
                    ? <Loader2 className="w-3 h-3 mr-2 animate-spin" />
                    : <FileJson className="w-3 h-3 mr-2" />}
                JSON
            </button>

            <button
                id="print-btn"
                onClick={handlePrint}
                disabled={!!exporting}
                title="Print report"
                className={btnBase}
            >
                <Printer className="w-3 h-3 mr-2" />
                PRINT
            </button>
        </div>
    );
}
