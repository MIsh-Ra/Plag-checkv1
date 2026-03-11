import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Client from '../api/client';
import { ChevronLeft, FileText, Globe, AlertTriangle, Check, X, Printer, Search } from 'lucide-react';

export default function ReportView() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(true);
    const [selectedFinding, setSelectedFinding] = useState(null);

    useEffect(() => {
        loadReport();
    }, [id]);

    const loadReport = async () => {
        try {
            const data = await Client.reports.get(id);
            setReport(data);
        } catch (error) {
            console.error("Failed to load report", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="flex items-center justify-center h-screen text-gray-500">Loading Analysis...</div>;
    if (!report) return <div className="flex items-center justify-center h-screen">Report not found</div>;

    return (
        <div className="flex flex-col h-screen bg-gray-50 overflow-hidden">
            {/* Header */}
            <header className="flex-none bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
                <div className="flex items-center space-x-4">
                    <button onClick={() => navigate('/dashboard')} className="text-gray-500 hover:text-gray-900">
                        <ChevronLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <h1 className="text-lg font-bold text-gray-900">Analysis Report</h1>
                        <p className="text-xs text-gray-500">ID: {id}</p>
                    </div>
                </div>
                <div className="flex items-center space-x-4">
                    <div className="flex flex-col items-end">
                        <span className="text-xs text-gray-500">Overall Similarity</span>
                        <span className={`text-xl font-bold ${report.total_score > 50 ? 'text-red-600' : 'text-green-600'}`}>
                            {report.total_score}%
                        </span>
                    </div>
                    <button className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700">
                        <Printer className="w-4 h-4 mr-2" />
                        Export PDF
                    </button>
                </div>
            </header>

            <div className="flex flex-1 overflow-hidden">
                {/* Sidebar Findings */}
                <aside className="w-80 bg-white border-r border-gray-200 overflow-y-auto flex-none z-10">
                    <div className="p-4 border-b border-gray-100">
                        <h2 className="font-semibold text-gray-700">Findings</h2>
                        <div className="flex space-x-2 mt-2">
                            <span className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded-full">{report.citations.filter(c => c.status === 'hallucinated').length} Hallucinations</span>
                            <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full">{report.segments.length} Matches</span>
                        </div>
                    </div>

                    <div className="divide-y divide-gray-100">
                        {report.citations.map((cite) => (
                            <div
                                key={cite.id}
                                onClick={() => setSelectedFinding({ type: 'citation', data: cite })}
                                className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors border-l-4 ${cite.status === 'hallucinated' ? 'border-red-500' : 'border-green-500'} ${selectedFinding?.data?.id === cite.id ? 'bg-blue-50' : ''}`}
                            >
                                <div className="flex items-start justify-between">
                                    <span className="text-xs font-mono text-gray-400">Page {cite.page}</span>
                                    {cite.status === 'hallucinated' ? (
                                        <AlertTriangle className="w-4 h-4 text-red-500" />
                                    ) : (
                                        <Check className="w-4 h-4 text-green-500" />
                                    )}
                                </div>
                                <p className="mt-1 text-sm font-medium text-gray-900 line-clamp-2">"{cite.text}"</p>
                                <p className="mt-1 text-xs text-gray-500">{cite.status.toUpperCase()}</p>
                            </div>
                        ))}

                        {report.segments.map((seg) => (
                            <div
                                key={seg.id}
                                onClick={() => setSelectedFinding({ type: 'segment', data: seg })}
                                className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors border-l-4 border-blue-500 ${selectedFinding?.data?.id === seg.id ? 'bg-blue-50' : ''}`}
                            >
                                <div className="flex items-start justify-between">
                                    <span className="text-xs font-mono text-gray-400">Page {seg.page}</span>
                                    {seg.type === 'web_dragnet' ? <Globe className="w-4 h-4 text-blue-500" /> : <FileText className="w-4 h-4 text-purple-500" />}
                                </div>
                                <p className="mt-1 text-sm font-medium text-gray-900">
                                    {seg.type === 'web_dragnet' ? 'Web Match' : 'Internal Match'} ({Math.round(seg.score * 100)}%)
                                </p>
                                <p className="mt-1 text-xs text-gray-500 truncate">{seg.source}</p>
                            </div>
                        ))}
                    </div>
                </aside>

                {/* Diff View Area */}
                <main className="flex-1 flex overflow-hidden bg-gray-100 p-4 space-x-4">

                    {/* Left: Document View */}
                    <div className="flex-1 bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col">
                        <div className="p-3 border-b border-gray-200 bg-gray-50 font-medium text-sm text-gray-600">Student Document</div>
                        <div className="flex-1 p-8 overflow-y-auto font-serif text-lg leading-relaxed text-gray-800">
                            {/* Simulation of Document Content rendering */}
                            {selectedFinding ? (
                                <>
                                    <p className="mb-4 text-gray-300 blur-[1px]">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
                                    <p className="mb-4 bg-yellow-100 border-l-4 border-yellow-400 pl-4 py-2">
                                        {selectedFinding.type === 'citation' ? selectedFinding.data.context : selectedFinding.data.text_content}
                                    </p>
                                    <p className="text-gray-300 blur-[1px]">Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
                                </>
                            ) : (
                                <div className="flex flex-col items-center justify-center h-full text-gray-400">
                                    <Search className="w-12 h-12 mb-2 opacity-20" />
                                    <p>Select a finding from the sidebar to view details</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Right: Evidence View */}
                    <div className="flex-1 bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col">
                        <div className="p-3 border-b border-gray-200 bg-gray-50 font-medium text-sm text-gray-600">Evidence / Context</div>
                        <div className="flex-1 p-6 overflow-y-auto">
                            {selectedFinding ? (
                                <div className="space-y-6">
                                    <div className="bg-blue-50 p-4 rounded-md border border-blue-100">
                                        <h3 className="font-bold text-blue-900 mb-1">Source Match</h3>
                                        <p className="text-sm text-blue-700 font-mono break-all">{selectedFinding.type === 'citation' ? 'Semantic Scholar API' : selectedFinding.data.source}</p>
                                    </div>

                                    {selectedFinding.type === 'citation' ? (
                                        selectedFinding.data.status === 'hallucinated' ? (
                                            <div className="text-center p-8">
                                                <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
                                                <h3 className="text-xl font-bold text-gray-900">Potential Hallucination</h3>
                                                <p className="mt-2 text-gray-600">This citation does not appear in the global scholarly record (Semantic Scholar / Crossref).</p>
                                            </div>
                                        ) : (
                                            <div className="text-center p-8">
                                                <Check className="w-16 h-16 text-green-500 mx-auto mb-4" />
                                                <h3 className="text-xl font-bold text-gray-900">Verified Citation</h3>
                                                <p className="mt-2 text-gray-600">Source confirmed via API Mesh.</p>
                                            </div>
                                        )
                                    ) : (
                                        <div>
                                            <h4 className="font-semibold text-gray-700 mb-2">Matched Content</h4>
                                            <div className="p-4 bg-gray-100 rounded text-sm text-gray-800 font-serif border-l-4 border-gray-400">
                                                {selectedFinding.data.match_content}
                                            </div>
                                            <div className="mt-4 flex justify-between text-xs text-gray-500">
                                                <span>Similarity Score: </span>
                                                <span className="font-bold">{Math.round(selectedFinding.data.score * 100)}%</span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="flex flex-col items-center justify-center h-full text-gray-400 bg-gray-50/50">
                                    <p>No segment selected</p>
                                </div>
                            )}
                        </div>
                    </div>

                </main>
            </div>
        </div>
    );
}
