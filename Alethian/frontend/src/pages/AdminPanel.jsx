import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Client from '../api/client';
import { Save, RefreshCw, Check, AlertCircle, Shield, Key } from 'lucide-react';

export default function AdminPanel() {
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        loadConfig();
    }, []);

    const loadConfig = async () => {
        try {
            const data = await Client.admin.getConfig();
            setConfig(data);
        } catch (error) {
            console.error("Failed to load config", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async (e) => {
        e.preventDefault();
        setSaving(true);
        setMessage(null);
        try {
            const result = await Client.admin.updateConfig(config);
            setMessage({ type: 'success', text: result.message });
            setTimeout(() => setMessage(null), 3000);
        } catch (error) {
            setMessage({ type: 'error', text: "Failed to update settings" });
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="p-8 text-center text-gray-500">Loading Configuration...</div>;

    return (
        <div className="min-h-screen bg-gray-50">
            <nav className="bg-slate-900 border-b border-slate-800">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex items-center space-x-3">
                            <Shield className="w-6 h-6 text-blue-400" />
                            <span className="text-xl font-bold text-white">Alethian Admin</span>
                        </div>
                        <div className="flex items-center space-x-4">
                            <button onClick={() => navigate('/login')} className="text-sm font-medium text-slate-300 hover:text-white">Logout</button>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-4xl mx-auto py-10 px-4">

                <div className="mb-6">
                    <h1 className="text-2xl font-bold text-gray-900">System Configuration</h1>
                    <p className="text-gray-500">Manage API connections and analysis thresholds.</p>
                </div>

                {message && (
                    <div className={`mb-6 p-4 rounded-md flex items-center ${message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
                        {message.type === 'success' ? <Check className="w-5 h-5 mr-2" /> : <AlertCircle className="w-5 h-5 mr-2" />}
                        {message.text}
                    </div>
                )}

                <form onSubmit={handleSave} className="space-y-6">

                    {/* API Keys Section */}
                    <div className="bg-white shadow rounded-lg overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
                            <h3 className="text-lg font-medium text-gray-900 flex items-center">
                                <Key className="w-4 h-4 mr-2 text-gray-500" /> API Mesh Configuration
                            </h3>
                        </div>
                        <div className="p-6 space-y-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Serper.dev API Key (Google Search)</label>
                                <div className="mt-1 flex rounded-md shadow-sm">
                                    <input
                                        type="password"
                                        value={config.serper_key || ''}
                                        onChange={(e) => setConfig({ ...config, serper_key: e.target.value })}
                                        className={`flex-1 block w-full rounded-md border px-3 py-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${config.api_status?.serper !== 'ok' ? 'border-red-300' : 'border-gray-300'}`}
                                        placeholder="Enter key to update"
                                    />
                                    <span className="inline-flex items-center px-3 rounded-r-md border border-l-0 border-gray-300 bg-gray-50 text-gray-500 text-sm">
                                        {config.api_status?.serper === 'ok' ? "Active" : <span className="text-red-600 flex items-center"><AlertCircle className="w-3 h-3 mr-1" /> Missing/Error</span>}
                                    </span>
                                </div>
                                <p className="mt-1 text-xs text-gray-500">Used for the Web Dragnet layer to detect internet plagiarism.</p>
                            </div>
                        </div>
                    </div>

                    {/* Thresholds Section */}
                    <div className="bg-white shadow rounded-lg overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                            <h3 className="text-lg font-medium text-gray-900">Analysis Sensitivity</h3>
                        </div>
                        <div className="p-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Similarity Threshold: {config.similarity_thresholds?.semantic_cosine || 0.85}</label>
                                <input
                                    type="range"
                                    min="0.5"
                                    max="0.99"
                                    step="0.01"
                                    value={config.similarity_thresholds?.semantic_cosine || 0.85}
                                    onChange={(e) => setConfig({ 
                                        ...config, 
                                        similarity_thresholds: { 
                                            ...config.similarity_thresholds, 
                                            semantic_cosine: parseFloat(e.target.value) 
                                        } 
                                    })}
                                    className="w-full mt-2"
                                />
                                <div className="flex justify-between text-xs text-gray-500 mt-1">
                                    <span>0.5 (Strict)</span>
                                    <span>1.0 (Lenient)</span>
                                </div>
                                <p className="mt-2 text-sm text-gray-500">Local document matches below this similarity score will be ignored.</p>
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-end">
                        <button
                            type="submit"
                            disabled={saving}
                            className="flex items-center justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                        >
                            {saving ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                            Save Configuration
                        </button>
                    </div>

                </form>
            </main>
        </div>
    );
}
