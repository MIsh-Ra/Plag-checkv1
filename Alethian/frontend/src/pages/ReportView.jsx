import { useParams, useNavigate } from 'react-router-dom';
import { ChevronLeft, Loader2 } from 'lucide-react';
import { useReport } from '../hooks/useReport';
import { useWebSocket } from '../hooks/useWebSocket';
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
    const { report, documentData, loading } = useReport(id);
    const wsStatus = useWebSocket(id);
    const { selectedMatchId, filterTypes, setSelectedMatch } = useReportStore();

    if (loading) return <div className="flex items-center justify-center h-screen text-gray-500">Loading Report...</div>;
    
    if (documentData && ['pending', 'ingesting', 'analyzing', 'processing'].includes(documentData.status)) {
        return (
            <div className="flex flex-col items-center justify-center h-screen bg-gray-50">
                <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
                <h2 className="text-xl font-semibold text-gray-800">Processing Document</h2>
                <p className="text-gray-500 mt-2">{wsStatus?.message || `Status: ${documentData.status}`}</p>
                {wsStatus?.progress > 0 && (
                    <div className="w-64 bg-gray-200 rounded-full h-2.5 mt-4">
                        <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${wsStatus.progress}%` }}></div>
                    </div>
                )}
                <button onClick={() => navigate('/dashboard')} className="mt-8 text-blue-600 hover:text-blue-800 font-medium">
                    &larr; Back to Dashboard
                </button>
            </div>
        );
    }

    if (!report) return <div className="flex items-center justify-center h-screen text-gray-500">Report not found</div>;

    const matches = report.matches || [];
    
    // Apply filters
    const filteredMatches = matches.filter(m => {
        if (m.is_excluded && !filterTypes.excluded) return false;
        if (!m.is_excluded) {
            if (m.type === 'internal_exact' && !filterTypes.internal_exact) return false;
            if (m.type === 'internal_paraphrase' && !filterTypes.internal_paraphrase) return false;
            if (m.type === 'web' && !filterTypes.web) return false;
        }
        return true;
    });

    const selectedMatch = filteredMatches.find(m => m.id === selectedMatchId) || filteredMatches[0];

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
                        {filteredMatches.map(m => <MatchCard key={m.id} match={m} />)}
                        {filteredMatches.length === 0 && <p className="text-gray-500 text-sm">No matches found.</p>}
                    </div>
                </aside>

                {/* Center Panel */}
                <main className="flex-1 bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col overflow-hidden">
                    <div className="flex-1 overflow-y-auto p-6 relative">
                        <TextOverlay text={report.document_text || "Document text is unavailable or was not extracted properly."} />
                    </div>
                    {selectedMatch && (
                        <div className="h-1/3 min-h-[300px] border-t border-gray-200 bg-gray-50 flex flex-col p-4 shadow-inner z-20">
                            <div className="flex justify-between items-center mb-3 flex-none">
                                <h3 className="font-semibold text-gray-700">Compare Match</h3>
                                <button onClick={() => setSelectedMatch(null)} className="text-sm text-gray-500 hover:text-gray-700">Close</button>
                            </div>
                            <div className="flex-1 overflow-hidden">
                                <DiffViewer match={selectedMatch} />
                            </div>
                        </div>
                    )}
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
