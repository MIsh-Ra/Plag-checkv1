import { useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { ChevronLeft, Loader2, CheckSquare, Square } from 'lucide-react';
import Client from '../api/client';
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
    const { report, documentData, loading, refetch } = useReport(id);
    const wsStatus = useWebSocket(id);
    const { selectedMatchId, filterTypes, setSelectedMatch } = useReportStore();
    const [reviewed, setReviewed] = useState(report?.review?.status === 'reviewed');
    const [reviewing, setReviewing] = useState(false);
    const [diffDismissed, setDiffDismissed] = useState(false);

    const handleMarkReviewed = async () => {
        if (reviewed || reviewing) return;
        setReviewing(true);
        try {
            const user = JSON.parse(localStorage.getItem('alethian_user') || '{}');
            await Client.reports.review(id, { reviewed_by: user.name || 'Faculty', verdict: 'reviewed' });
            setReviewed(true);
        } catch (e) {
            console.error('Failed to mark as reviewed:', e);
        } finally {
            setReviewing(false);
        }
    };

    // When a match is selected, scroll the doc viewer to that page and open diff
    useEffect(() => {
        if (!selectedMatchId) return;
        setDiffDismissed(false);
        const match = (report?.matches || []).find(m => m.id === selectedMatchId);
        if (match?.submitted_page) {
            setTimeout(() => {
                const el = document.getElementById(`page-${match.submitted_page}`);
                if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 60);
        }
    }, [selectedMatchId]);

    useEffect(() => {
        if (wsStatus?.stage === 'complete') {
            refetch();
        }
    }, [wsStatus?.stage, refetch]);

    if (loading) return (
        <div className="flex flex-col items-center justify-center h-full text-on-surface-variant font-mono tracking-widest text-sm">
            <Loader2 className="w-8 h-8 animate-spin mb-4 text-primary" />
            ACQUIRING FORENSIC DATA...
        </div>
    );
    
    if (documentData && ['pending', 'ingesting', 'analyzing', 'processing'].includes(documentData.status)) {
        return (
            <div className="flex flex-col items-center justify-center h-full bg-surface">
                <Loader2 className="w-12 h-12 text-on-surface animate-spin mb-6" />
                <h2 className="text-xl font-bold tracking-tight text-on-surface uppercase border-b-2 border-primary pb-2 mb-4">Ingesting Evidence</h2>
                <p className="text-on-surface-variant font-mono text-sm uppercase tracking-widest mb-8">{wsStatus?.message || `STATUS: ${documentData.status}`}</p>
                {wsStatus?.progress > 0 && (
                    <div className="w-96 bg-surface-container-highest h-1 overflow-hidden relative">
                        <div className="absolute top-0 left-0 bottom-0 bg-primary transition-all duration-300" style={{ width: `${wsStatus.progress}%` }}></div>
                    </div>
                )}
            </div>
        );
    }

    if (!report) return (
        <div className="flex flex-col items-center justify-center h-full text-on-surface-variant font-mono uppercase tracking-widest text-sm">
            REPORT NOT FOUND
        </div>
    );

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

    const selectedMatch = filteredMatches.find(m => m.id === selectedMatchId) ?? null;
    const showDiff = selectedMatch && !diffDismissed;

    return (
        <div className="flex flex-col h-full bg-surface overflow-hidden" id="alethian-report-container">
                <header className="flex-none bg-surface-container border-b border-ghost px-6 py-4 flex items-center justify-between z-10">
                    <div className="flex items-center space-x-4">
                        <button aria-label="Return to Dashboard" onClick={() => navigate('/dashboard')} className="text-on-surface-variant hover:text-on-surface transition-colors">
                            <ChevronLeft className="w-6 h-6" />
                        </button>
                        <div className="flex items-baseline space-x-4">
                            <h1 className="text-xl font-bold text-on-surface tracking-tight uppercase">Forensic Report</h1>
                            <p className="text-xs text-on-surface-variant font-mono">ID:{id.substring(0,8)}</p>
                        </div>
                    </div>
                    <ExportMenu />
                    <button
                        onClick={handleMarkReviewed}
                        disabled={reviewed || reviewing}
                        aria-label="Mark Report as Reviewed"
                        className={`ml-4 inline-flex items-center px-4 py-2 border text-xs font-mono font-bold tracking-widest uppercase transition-colors ${
                            reviewed
                                ? 'bg-secondary-fixed-dim text-on-secondary-fixed border-secondary/30 cursor-default'
                                : 'bg-surface-container-high border-ghost text-on-surface-variant hover:border-primary hover:text-primary'
                        }`}
                    >
                        {reviewed ? <CheckSquare className="w-4 h-4 mr-2" /> : <Square className="w-4 h-4 mr-2" />}
                        {reviewed ? 'REVIEWED' : reviewing ? 'SIGNING...' : 'MARK REVIEWED'}
                    </button>
                </header>

                <div className="flex flex-1 overflow-hidden p-6 space-x-6">
                    {/* Left Panel */}
                    <aside className="w-1/4 bg-surface-container-lowest flex flex-col overflow-y-auto">
                        <div className="p-5 border-b border-ghost">
                            <Heatmap pages={report.heatmap} />
                        </div>
                        <div className="p-5 border-b border-ghost bg-surface-container-low">
                            <FilterBar />
                        </div>
                        <div className="flex-1 p-5 overflow-y-auto">
                            <h3 className="text-xs font-bold uppercase tracking-widest text-on-surface mb-4">Identified Anomalies</h3>
                            <div className="space-y-4">
                                {filteredMatches.map(m => <MatchCard key={m.id} match={m} onUpdate={refetch} />)}
                                {filteredMatches.length === 0 && <p className="text-on-surface-variant text-xs font-mono uppercase">0 Anomalies Detected</p>}
                            </div>
                        </div>
                    </aside>

                    {/* Center Panel (Document Text & Diff) */}
                    <main className="flex-1 bg-surface-container-lowest border border-ghost flex flex-col overflow-hidden shadow-ambient relative" style={{ background: '#f0f0f0' }}>
                        <div className="flex-1 overflow-hidden relative">
                            <TextOverlay
                                pageTexts={report.page_texts || []}
                                documentText={report.document_text || ""}
                                matches={filteredMatches}
                            />
                        </div>
                        {showDiff && (
                            <div className="h-1/3 min-h-[300px] border-t-2 border-primary bg-surface-container-highest flex flex-col p-6 shadow-ambient z-20">
                                <div className="flex justify-between items-center mb-4 flex-none border-b border-ghost pb-2">
                                    <h3 className="text-sm font-bold uppercase tracking-widest text-on-surface">Comparative Analysis</h3>
                                    <button
                                        onClick={() => { setDiffDismissed(true); setSelectedMatch(null); }}
                                        className="text-xs font-mono tracking-widest text-on-surface-variant hover:text-on-surface transition-colors"
                                    >DISMISS [X]</button>
                                </div>
                                <div className="flex-1 overflow-hidden">
                                    <DiffViewer match={selectedMatch} />
                                </div>
                            </div>
                        )}
                    </main>

                    {/* Right Panel (Analytics) */}
                    <aside className="w-1/4 bg-surface-container-lowest flex flex-col overflow-y-auto">
                        <div className="p-5 border-b border-ghost bg-surface-container-low">
                            <ScoreHeader score={report.scores?.originality_score} summary={report.summary_stats} />
                        </div>
                        <div className="p-5 border-b border-ghost">
                            <h3 className="text-xs font-bold uppercase tracking-widest text-on-surface mb-6">Source Vector</h3>
                            <PieChart data={report.source_breakdown} />
                        </div>
                        <div className="p-5 border-b border-ghost bg-surface-container-low">
                            <h3 className="text-xs font-bold uppercase tracking-widest text-on-surface mb-6">Page Density</h3>
                            <BarChart data={report.page_distribution} />
                        </div>
                        <div className="flex-1 overflow-y-auto bg-surface-container">
                            <SourcePanel sources={report.sources} />
                        </div>
                    </aside>
                </div>
        </div>
    );
}
