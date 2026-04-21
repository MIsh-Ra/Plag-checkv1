import { CheckCircle, AlertTriangle, ShieldAlert } from 'lucide-react';

export default function ScoreHeader({ score, summary }) {
    const riskLevel = score < 50 ? 'high' : score < 80 ? 'moderate' : 'low';

    return (
        <div className="flex flex-col space-y-5">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-1">Index of Originality</h2>
                    <div className="flex items-baseline space-x-3">
                        <span className={`text-6xl font-bold tracking-tighter ${riskLevel === 'high' ? 'text-error' : riskLevel === 'moderate' ? 'text-tertiary-container' : 'text-secondary-fixed'}`}>
                            {score ? Math.round(score) : 0}%
                        </span>
                    </div>
                </div>
                <div className="text-right">
                    {riskLevel === 'high' && <span className="inline-flex items-center px-3 py-1 font-mono text-xs font-bold uppercase tracking-widest bg-error-container text-on-error-container border border-error/50"><ShieldAlert className="w-4 h-4 mr-2" /> Critical Risk</span>}
                    {riskLevel === 'moderate' && <span className="inline-flex items-center px-3 py-1 font-mono text-xs font-bold uppercase tracking-widest bg-tertiary-container text-on-tertiary-container border border-tertiary/50"><AlertTriangle className="w-4 h-4 mr-2" /> Anomalous</span>}
                    {riskLevel === 'low' && <span className="inline-flex items-center px-3 py-1 font-mono text-xs font-bold uppercase tracking-widest bg-secondary-fixed-dim text-on-secondary-fixed border border-secondary/50"><CheckCircle className="w-4 h-4 mr-2"/> Cleared</span>}
                </div>
            </div>

            {summary && (
                <div className="border border-ghost bg-surface-container shadow-sm p-4 relative overflow-hidden">
                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary"></div>
                    <h3 className="text-[10px] font-bold uppercase tracking-widest text-on-surface mb-3 grid grid-cols-2">
                        <span>Forensic Telemetry</span>
                    </h3>
                    <div className="grid grid-cols-2 gap-y-3 gap-x-4">
                        <div>
                            <p className="text-[10px] text-on-surface-variant uppercase tracking-widest">Total Matches</p>
                            <p className="font-mono text-sm font-bold text-on-surface">{summary.total_matches || 0}</p>
                        </div>
                        <div>
                            <p className="text-[10px] text-on-surface-variant uppercase tracking-widest">Unique Vectors</p>
                            <p className="font-mono text-sm font-bold text-on-surface">{summary.unique_sources || 0}</p>
                        </div>
                        <div>
                            <p className="text-[10px] text-on-surface-variant uppercase tracking-widest">Avg Length</p>
                            <p className="font-mono text-sm font-bold text-on-surface">{summary.avg_match_length_words || 0} w</p>
                        </div>
                        <div>
                            <p className="text-[10px] text-on-surface-variant uppercase tracking-widest">Pages Hit</p>
                            <p className="font-mono text-sm font-bold text-on-surface">{summary.pages_with_matches || 0} / {summary.total_pages || 0}</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
