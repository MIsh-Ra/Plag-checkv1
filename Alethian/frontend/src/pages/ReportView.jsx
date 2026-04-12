import { useParams, useNavigate } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import { useReport } from '../hooks/useReport';
import ScoreHeader from '../components/report/ScoreHeader';
import Heatmap from '../components/report/Heatmap';
import DiffViewer from '../components/report/DiffViewer';
import TextOverlay from '../components/report/TextOverlay';
import SourcePanel from '../components/report/SourcePanel';
import FilterBar from '../components/report/FilterBar';
import MatchCard from '../components/report/MatchCard';
import PieChart from '../components/report/PieChart';
import BarChart from '../components/report/BarChart';
import ExportMenu from '../components/report/ExportMenu';
import { useReportStore } from '../stores/reportStore';

export default function ReportView() {
    const { id } = useParams();
    const navigate = useNavigate();
    const { report, loading } = useReport(id);
    const { selectedMatchId } = useReportStore();

    if (loading) return <div className="flex items-center justify-center h-screen text-gray-500">Loading Report...</div>;
    if (!report) return <div className="flex items-center justify-center h-screen">Report not found</div>;

    const matches = report.matches || [];
    const selectedMatch = matches.find(m => m.id === selectedMatchId) || matches[0];

    return (
        <div className="flex flex-col h-screen bg-gray-50 overflow-hidden">
            <header className="flex-none bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
                <div className="flex items-center space-x-4">
                    <button onClick={() => navigate('/dashboard')} className="text-gray-500 hover:text-gray-900">
                        <ChevronLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <h1 className="text-lg font-bold text-gray-900">Alethian Originality Report</h1>
                        <p className="text-xs text-gray-500">ID: {id}</p>
                    </div>
                </div>
                <ExportMenu />
            </header>

            <div className="flex flex-1 overflow-hidden p-4 space-x-4">
                {/* Left Panel */}
                <aside className="w-1/4 bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col overflow-y-auto p-4">
                    <Heatmap data={report.heatmap} />
                    <FilterBar />
                    <h3 className="font-semibold text-gray-700 mt-4 mb-2">Detailed Matches</h3>
                    <div className="space-y-4">
                        {matches.map(m => <MatchCard key={m.id} match={m} />)}
                        {matches.length === 0 && <p className="text-gray-500 text-sm">No matches found.</p>}
                    </div>
                </aside>

                {/* Center Panel */}
                <main className="flex-1 bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col overflow-y-auto p-6">
                    <TextOverlay text={report.document_text || "Document text is unavailable or was not extracted properly."} />
                    <div className="mt-8">
                        <h3 className="font-semibold text-gray-700 mb-2">Compare</h3>
                        <DiffViewer match={selectedMatch} />
                    </div>
                </main>

                {/* Right Panel */}
                <aside className="w-1/4 bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col overflow-y-auto p-4 space-y-6">
                    <ScoreHeader score={report.scores?.originality_score} summary={report.summary_stats} />
                    <div>
                        <h3 className="text-sm font-medium text-gray-600 mb-2">Source Breakdown</h3>
                        <PieChart data={report.source_breakdown} />
                    </div>
                    <div>
                        <h3 className="text-sm font-medium text-gray-600 mb-2">Risk per Page</h3>
                        <BarChart data={report.page_distribution} />
                    </div>
                    <SourcePanel sources={report.sources} />
                </aside>
            </div>
        </div>
    );
}
