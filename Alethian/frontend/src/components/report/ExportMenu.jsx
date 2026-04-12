import { Printer, Download, FileJson } from 'lucide-react';
import Client from '../../api/client';
import { useParams } from 'react-router-dom';

export default function ExportMenu() {
    const { id } = useParams();

    const handlePdfExport = async () => {
        try {
            await Client.reports.exportPdf(id);
        } catch (error) {
            console.error("PDF Export failed", error);
            alert("PDF export failed. Please try again.");
        }
    };

    const handleJsonExport = async () => {
        try {
            const data = await Client.reports.exportJson(id);
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `report_${id}.json`;
            a.click();
        } catch (error) {
            console.error("JSON Export failed", error);
        }
    };

    return (
        <div className="flex items-center space-x-2">
            <button onClick={handlePdfExport} className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-sm font-medium rounded text-gray-700 bg-white hover:bg-gray-50">
                <Download className="w-4 h-4 mr-2" />
                Export PDF
            </button>
            <button onClick={handleJsonExport} className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-sm font-medium rounded text-gray-700 bg-white hover:bg-gray-50">
                <FileJson className="w-4 h-4 mr-2" />
                Export JSON
            </button>
            <button onClick={() => window.print()} className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-sm font-medium rounded text-gray-700 bg-white hover:bg-gray-50">
                <Printer className="w-4 h-4 mr-2" />
                Print
            </button>
        </div>
    );
}
