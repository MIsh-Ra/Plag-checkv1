import { useReportStore } from '../../stores/reportStore';

export default function SourcePanel({ sources }) {
    const { selectedSourceId, setSelectedSource } = useReportStore();

    if (!sources || sources.length === 0) {
        return <div className="text-xs font-mono tracking-widest text-on-surface-variant italic p-5">NO VECTORS IDENTIFIED.</div>;
    }

    return (
        <div className="p-5">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-bold uppercase tracking-widest text-on-surface">Source Index</h3>
                {selectedSourceId && (
                    <button aria-label="Clear Source Selection" onClick={() => setSelectedSource(null)} className="text-xs font-mono text-secondary hover:text-secondary-fixed transition-colors">CLEAR</button>
                )}
            </div>
            <div className="space-y-4">
                {sources.map((src, i) => (
                    <div 
                        key={src.id}
                        onClick={() => setSelectedSource(src.id === selectedSourceId ? null : src.id)}
                        className={`p-4 rounded-none border text-sm cursor-pointer transition-colors border-l-4 ${
                            selectedSourceId === src.id 
                            ? 'border-y-ghost border-r-ghost border-l-primary bg-surface-container-high shadow-ambient' 
                            : 'border-y-ghost border-r-ghost border-l-surface hover:border-l-primary-fixed bg-surface-container hover:bg-surface-container-high'
                        }`}
                    >
                        <div className="flex justify-between items-start mb-2">
                            <span className="font-mono text-xs font-bold text-on-surface truncate tracking-wider" title={src.title || src.domain}>{String(i+1).padStart(2, '0')} // {src.title || src.domain}</span>
                            <span className="text-xs font-bold text-on-surface-variant ml-3">{Math.round(src.coverage_percent || 0)}%</span>
                        </div>
                        <div className="text-[10px] font-mono uppercase tracking-widest text-on-surface-variant mb-3 truncate">
                            {src.type === 'web' ? `WEB // ${src.domain}` : `ARCHIVE // INTERNAL DATABASE`}
                        </div>
                        <div className="w-full bg-surface-container-highest h-1 rounded-none overflow-hidden relative">
                            <div className="absolute top-0 left-0 bottom-0 bg-primary h-full" style={{ width: `${Math.min(100, Math.max(2, src.coverage_percent || 0))}%` }}></div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
