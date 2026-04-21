import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Client from '../api/client';
import { Save, RefreshCw, Check, AlertCircle, Key, Settings2 } from 'lucide-react';

export default function AdminPanel() {
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);

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

    if (loading) return (
        <div className="h-full flex flex-col justify-center items-center text-on-surface-variant space-y-4">
            <RefreshCw className="w-8 h-8 animate-spin" />
            <span className="text-sm font-medium tracking-widest uppercase">Deciphering Configuration...</span>
        </div>
    );

    return (
        <div className="h-full px-8 py-8 w-full max-w-4xl mx-auto flex flex-col space-y-8">
            <header>
                 <h1 className="text-3xl font-semibold tracking-tight text-on-background">System Configuration</h1>
                 <p className="text-sm text-on-surface-variant mt-1 tracking-wide">Manage API connections and set intelligence thresholds.</p>
            </header>

            {message && (
                <div className={`p-4 rounded-sm flex items-center ${message.type === 'success' ? 'bg-secondary-fixed-dim text-on-secondary-fixed' : 'bg-error-container text-on-error-container'}`}>
                    {message.type === 'success' ? <Check className="w-5 h-5 mr-3" /> : <AlertCircle className="w-5 h-5 mr-3" />}
                    <span className="text-sm font-bold">{message.text}</span>
                </div>
            )}

            <form onSubmit={handleSave} className="space-y-8">

                {/* API Keys Section */}
                <section className="bg-surface-container shadow-sm border border-ghost rounded-md overflow-hidden relative">
                    <div className="px-6 py-5 border-b border-ghost bg-surface-container-low flex justify-between items-center">
                        <h3 className="text-sm tracking-widest font-bold uppercase text-on-surface flex items-center">
                            <Key className="w-4 h-4 mr-2" /> API Mesh Access
                        </h3>
                    </div>
                    <div className="p-8 pb-10">
                        <div>
                            <label className="block text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-3">Serper.dev Gateway (Search)</label>
                            <div className="flex rounded-sm overflow-hidden">
                                <input
                                    type="password"
                                    value={config.serper_key || ''}
                                    onChange={(e) => setConfig({ ...config, serper_key: e.target.value })}
                                    className={`flex-1 block w-full bg-surface-container-highest border text-sm px-4 py-3 text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-outline transition-colors ${config.api_status?.serper !== 'ok' ? 'border-error' : 'border-ghost'}`}
                                    placeholder="Enter authorization key..."
                                />
                                <span className={`inline-flex items-center px-4 border ${config.api_status?.serper !== 'ok' ? 'border-error border-l-0 bg-error-container text-error' : 'border-ghost border-l-0 bg-surface-container-low text-on-surface-variant'} text-xs font-bold tracking-wide`}>
                                    {config.api_status?.serper === 'ok' ? "Vetted" : <span className="flex items-center"><AlertCircle className="w-3 h-3 mr-1" /> Breach/Missing</span>}
                                </span>
                            </div>
                            <p className="mt-3 text-xs font-medium text-on-surface-variant">Required for the Web Dragnet layer to execute external plagiarism reconnaissance.</p>
                        </div>
                    </div>
                </section>

                {/* Thresholds Section */}
                <section className="bg-surface-container shadow-sm border border-ghost rounded-md overflow-hidden">
                    <div className="px-6 py-5 border-b border-ghost bg-surface-container-low">
                         <h3 className="text-sm tracking-widest font-bold uppercase text-on-surface flex items-center">
                            <Settings2 className="w-4 h-4 mr-2" /> Heuristic Sensitivity
                        </h3>
                    </div>
                    <div className="p-8 pb-10">
                        <div>
                            <div className="flex justify-between items-center mb-4">
                                <label className="block text-xs font-bold text-on-surface-variant uppercase tracking-wider">Semantic Cosine Tolerance</label>
                                <span className="text-sm font-bold text-primary">{config.similarity_thresholds?.semantic_cosine || 0.85}</span>
                            </div>
                            
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
                                className="w-full accent-primary h-1 bg-surface-container-highest outline-none rounded-full appearance-none cursor-pointer"
                            />
                            <div className="flex justify-between text-xs font-medium text-on-surface-variant mt-3">
                                <span>0.5 (Strict Inquisition)</span>
                                <span>1.0 (Permissive)</span>
                            </div>
                            <p className="mt-4 text-xs font-medium text-on-surface-variant">Matches below this similarity score will be discarded from reports.</p>
                        </div>
                    </div>
                </section>

                <div className="flex justify-end pt-4">
                    <button
                        type="submit"
                        disabled={saving}
                        className="gradient-btn-primary flex items-center justify-center disabled:opacity-50"
                    >
                        {saving ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                        Commit Configuration
                    </button>
                </div>

            </form>
        </div>
    );
}
