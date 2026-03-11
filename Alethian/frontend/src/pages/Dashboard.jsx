import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Client from '../api/client';
import { FileText, Upload, Plus, CheckCircle, Clock, AlertTriangle, ArrowRight, Loader2 } from 'lucide-react';

export default function Dashboard() {
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const navigate = useNavigate();
    const user = JSON.parse(localStorage.getItem('alethian_user') || '{}');

    useEffect(() => {
        loadDocuments();
    }, []);

    const loadDocuments = async () => {
        try {
            const docs = await Client.documents.list();
            setDocuments(docs);
        } catch (error) {
            console.error("Failed to load documents", error);
        } finally {
            setLoading(false);
        }
    };

    const handleUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploading(true);
        try {
            const newDoc = await Client.documents.upload(file);
            // In real app, we'd poll for status. Here we just add it to list.
            const mockEntry = {
                ...newDoc,
                title: "Processing: " + file.name,
                author: "Unknown",
                uploaded_at: new Date().toISOString(),
                progress: 10
            };
            setDocuments([mockEntry, ...documents]);
        } catch (error) {
            alert("Upload failed");
        } finally {
            setUploading(false);
        }
    };

    const getStatusBadge = (status, score) => {
        if (status === 'processing') {
            return (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    <Loader2 className="w-3 h-3 mr-1 animate-spin" /> Ingesting
                </span>
            );
        }
        if (status === 'ready') {
            return (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    Ready to Analyze
                </span>
            );
        }
        // Complete
        if (score > 80) return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">High Risk ({score}%)</span>;
        if (score > 40) return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Medium Risk ({score}%)</span>;
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Clean ({score}%)</span>;
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Top Navigation */}
            <nav className="bg-white border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex items-center">
                            <span className="text-xl font-bold text-gray-900">Alethian</span>
                        </div>
                        <div className="flex items-center space-x-4">
                            <span className="text-sm text-gray-500">Welcome, {user.name || 'Faculty'}</span>
                            <button onClick={() => navigate('/login')} className="text-sm font-medium text-gray-900 hover:text-blue-600">Logout</button>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

                {/* Upload Section */}
                <div className="mb-8">
                    <div className="bg-white border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-blue-500 transition-colors cursor-pointer group relative">
                        <input
                            type="file"
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                            onChange={handleUpload}
                            disabled={uploading}
                        />
                        <div className="flex flex-col items-center">
                            <div className="p-4 bg-blue-50 rounded-full group-hover:bg-blue-100 transition-colors">
                                <Upload className="w-8 h-8 text-blue-600" />
                            </div>
                            <h3 className="mt-4 text-lg font-medium text-gray-900">
                                {uploading ? "Uploading..." : "Start New Analysis"}
                            </h3>
                            <p className="mt-1 text-sm text-gray-500">Drag and drop PDF thesis headers, or click to browse</p>
                        </div>
                    </div>
                </div>

                {/* Recent Analysis List */}
                <div className="bg-white shadow rounded-lg overflow-hidden">
                    <div className="px-6 py-5 border-b border-gray-200">
                        <h3 className="text-lg font-medium leading-6 text-gray-900">Recent Submissions</h3>
                    </div>
                    {loading ? (
                        <div className="p-6 text-center text-gray-500">Loading documents...</div>
                    ) : (
                        <ul className="divide-y divide-gray-200">
                            {documents.map((doc) => (
                                <li
                                    key={doc.id}
                                    onClick={() => navigate(`/report/${doc.id}`)}
                                    className="hover:bg-gray-50 transition-colors cursor-pointer"
                                >
                                    <div className="px-6 py-4 flex items-center justify-between">
                                        <div className="flex items-center">
                                            <div className="flex-shrink-0">
                                                <FileText className="w-10 h-10 text-gray-400" />
                                            </div>
                                            <div className="ml-4">
                                                <div className="text-sm font-medium text-gray-900">{doc.title}</div>
                                                <div className="text-sm text-gray-500">Author: {doc.author} • Uploaded: {new Date(doc.uploaded_at).toLocaleDateString()}</div>
                                            </div>
                                        </div>
                                        <div className="flex items-center space-x-6">
                                            {getStatusBadge(doc.status, doc.score)}
                                            <button
                                                className="text-gray-400 hover:text-blue-600 transition-colors"
                                            >
                                                <ArrowRight className="w-5 h-5" />
                                            </button>
                                        </div>
                                    </div>
                                    {doc.status === 'processing' && (
                                        <div className="px-6 pb-2">
                                            <div className="w-full bg-gray-200 rounded-full h-1.5">
                                                <div className="bg-blue-600 h-1.5 rounded-full" style={{ width: '45%' }}></div>
                                            </div>
                                        </div>
                                    )}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </main>
        </div>
    );
}
