import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Client from '../api/client';
import { FileText, Upload, Plus, CheckCircle, Clock, AlertTriangle, ArrowRight, Loader2, RefreshCcw } from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';

export default function Dashboard() {
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [latestDocId, setLatestDocId] = useState(null);
    const wsStatus = useWebSocket(latestDocId);
    const navigate = useNavigate();

    const [courseFilter, setCourseFilter] = useState('');

    useEffect(() => {
        loadDocuments();
    }, [courseFilter]);

    const loadDocuments = async () => {
        try {
            const docs = await Client.documents.list({ course_id: courseFilter || undefined });
            setDocuments(docs.items || docs || []);
        } catch (error) {
            console.error("Failed to load documents", error);
        } finally {
            setLoading(false);
        }
    };

    const handleUpload = async (e) => {
        const files = Array.from(e.target.files);
        if (!files.length) return;

        setUploading(true);
        try {
            const uploadPromises = files.map(file => Client.documents.upload(file));
            const newDocs = await Promise.all(uploadPromises);
            
            // Set the most recent doc for WebSocket tracking just in case
            if (newDocs.length > 0) {
                setLatestDocId(newDocs[0].id);
            }
            
            const mockEntries = newDocs.map((newDoc, index) => ({
                ...newDoc,
                title: "Processing: " + files[index].name,
                author: "Unknown",
                upload_date: new Date().toISOString(),
                status: 'pending'
            }));
            
            setDocuments(prevDocs => [...mockEntries, ...prevDocs]);
        } catch (error) {
            alert("One or more uploads failed. Please try again.");
            console.error(error);
        } finally {
            setUploading(false);
            e.target.value = ''; // Reset input to allow re-uploading same files
        }
    };

    const getStatusBadge = (status, score) => {
        const processingStatuses = ['pending', 'ingesting', 'analyzing', 'processing'];
        if (processingStatuses.includes(status)) {
            return (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-sm text-xs font-bold bg-secondary-fixed-dim text-on-secondary-fixed">
                    <Loader2 className="w-3 h-3 mr-1 animate-spin" /> Ingesting
                </span>
            );
        }
        if (status === 'error' || status === 'failed') {
            return (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-sm text-xs font-bold bg-error text-on-error">
                    <AlertTriangle className="w-3 h-3 mr-1" /> Failed
                </span>
            );
        }
        if (status === 'ready') {
            return (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-sm text-xs font-bold bg-surface-container text-on-surface">
                    Ready
                </span>
            );
        }
        // Complete (score is originality score, lower is worse)
        const displayScore = score || 0;
        if (displayScore < 50) return <span className="inline-flex items-center px-2.5 py-0.5 rounded-sm text-xs font-bold bg-error-container text-on-error-container">Critical ({displayScore}%)</span>;
        if (displayScore < 80) return <span className="inline-flex items-center px-2.5 py-0.5 rounded-sm text-xs font-bold bg-tertiary-container text-on-tertiary-container">Review ({displayScore}%)</span>;
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-sm text-xs font-bold bg-secondary-fixed text-on-secondary-fixed">Clear ({displayScore}%)</span>;
    };

    return (
        <div className="h-full px-8 py-8 w-full max-w-7xl mx-auto flex flex-col space-y-8">
            <header className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-semibold tracking-tight text-on-background">Faculty Dashboard</h1>
                    <p className="text-sm text-on-surface-variant mt-1 tracking-wide">Review submitted theses and trigger deep analytics.</p>
                </div>
                <div className="w-72">
                    <label className="block text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2">Filter by Course ID</label>
                    <input
                        type="text"
                        value={courseFilter}
                        onChange={(e) => setCourseFilter(e.target.value)}
                        placeholder="e.g. CS101"
                        className="block w-full px-4 py-2 bg-surface-container-highest ghost-border rounded-sm focus:outline-none focus:border-outline focus:ring-0 text-sm text-on-surface placeholder:text-on-surface-variant/50 transition-all font-medium"
                    />
                </div>
            </header>

            {/* Upload Section */}
            <section className="bg-surface-container-lowest rounded-md p-10 text-center border-2 border-dashed border-outline-variant/30 hover:bg-surface-container-low transition-colors cursor-pointer group relative shadow-sm">
                <input
                    type="file"
                    multiple
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    onChange={handleUpload}
                    disabled={uploading}
                />
                <div className="flex flex-col items-center">
                    <div className="p-4 bg-primary-container rounded-full group-hover:bg-primary transition-colors text-on-primary shadow-ambient">
                        <Upload className="w-8 h-8" />
                    </div>
                    <h3 className="mt-6 text-lg font-bold tracking-tight text-on-surface">
                        {uploading ? "Ingesting Evidence..." : "Start New Forensic Analysis"}
                    </h3>
                    <p className="mt-2 text-sm font-medium text-on-surface-variant max-w-md">Drag and drop student thesis submissions (PDF) here to initialize the Web Dragnet and Internal Similarity pipelines.</p>
                </div>
            </section>

            {/* Recent Analysis List */}
            <section className="flex-1 flex flex-col min-h-0 bg-surface-container shadow-sm p-6 rounded-lg">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-sm font-bold uppercase tracking-widest text-on-surface">Investigation Log</h3>
                    <button aria-label="Refresh Documents List" onClick={loadDocuments} className="text-on-surface-variant hover:text-primary transition-colors">
                        <RefreshCcw className="w-4 h-4" />
                    </button>
                </div>
                
                {loading ? (
                    <div className="p-12 text-center text-on-surface-variant flex flex-col justify-center items-center h-full">
                        <Loader2 className="w-8 h-8 animate-spin mb-4" />
                        <span className="font-medium text-sm">Synchronizing Database...</span>
                    </div>
                ) : (
                    <div className="flex-1 overflow-y-auto pr-2 space-y-4">
                        {documents.map((doc, index) => {
                            const isError = doc.status === 'error' || doc.status === 'failed';
                            const isClear = doc.status === 'complete' && doc.score >= 80;
                            const isCritical = doc.status === 'complete' && doc.score < 50;
                            
                            let accentClass = "bg-primary-container";
                            if (isError) accentClass = "bg-error";
                            else if (isCritical) accentClass = "bg-error-container";
                            else if (isClear) accentClass = "bg-secondary-fixed";

                            return (
                                <div
                                    key={doc.id || index}
                                    onClick={() => navigate(`/report/${doc.id}`)}
                                    className="group relative flex flex-col bg-surface-container-lowest rounded-md shadow-sm hover:shadow-ambient overflow-hidden cursor-pointer transition-all hover:-translate-y-[1px]"
                                >
                                    <div className="flex items-center justify-between p-5">
                                        <div className="flex items-center space-x-5">
                                            {/* Status Accent Bar */}
                                            <div className={`absolute left-0 top-0 bottom-0 w-1 ${accentClass}`}></div>
                                            
                                            <div className="pl-2">
                                                <div className="p-3 bg-surface-container rounded-sm group-hover:bg-primary-container transition-colors group-hover:text-on-primary">
                                                    <FileText className="w-6 h-6 text-on-surface-variant group-hover:text-on-primary transition-colors" />
                                                </div>
                                            </div>
                                            <div className="flex flex-col space-y-1">
                                                <h4 className="text-sm font-bold text-on-surface">{doc.filename || doc.title || 'Unknown Document'}</h4>
                                                <div className="text-xs font-medium text-on-surface-variant flex items-center space-x-2">
                                                    <span>Author: <span className="text-on-surface font-semibold">{doc.author || 'Unknown'}</span></span>
                                                    <span>•</span>
                                                    <span>Uploaded: {new Date(doc.upload_date).toLocaleDateString()}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center space-x-6 pr-2">
                                            {getStatusBadge(doc.status, doc.score)}
                                            <ArrowRight className="w-5 h-5 text-on-surface-variant group-hover:text-primary transition-colors" />
                                        </div>
                                    </div>
                                    
                                    {/* Progress indicator for active ingestion */}
                                    {['pending', 'ingesting', 'analyzing', 'processing'].includes(doc.status) && (
                                        <div className="absolute bottom-0 left-0 right-0 h-1 bg-surface-container-high">
                                            <div className="h-full bg-secondary-fixed animate-pulse" style={{ width: doc.status === 'processing' ? '60%' : '30%' }}></div>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                        {documents.length === 0 && (
                            <div className="p-12 text-center text-on-surface-variant flex flex-col justify-center items-center h-full">
                                <span className="font-medium text-sm">No forensic records found for this criteria.</span>
                            </div>
                        )}
                    </div>
                )}
            </section>
        </div>
    );
}
