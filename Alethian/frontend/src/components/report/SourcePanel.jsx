import { useReportStore } from '../../stores/reportStore';

export default function SourcePanel({ sources }) {
    const { selectedSourceId, setSelectedSource } = useReportStore();

    if (!sources || sources.length === 0) {
        return <div className="text-sm text-gray-500">No sources matched.</div>;
    }

    return (
        <div>
            <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-gray-600">Identified Sources</h3>
                {selectedSourceId && (
                    <button onClick={() => setSelectedSource(null)} className="text-xs text-blue-600 hover:text-blue-800">Clear Selection</button>
                )}
            </div>
            <div className="space-y-3">
                {sources.map((src, i) => (
                    <div 
                        key={src.id}
                        onClick={() => setSelectedSource(src.id === selectedSourceId ? null : src.id)}
                        className={`p-3 rounded border text-sm cursor-pointer transition-colors ${
                            selectedSourceId === src.id 
                            ? 'border-blue-500 bg-blue-50' 
                            : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
                        }`}
                    >
                        <div className="flex justify-between items-start mb-1">
                            <span className="font-medium text-gray-800 truncate" title={src.title || src.domain}>{i+1}. {src.title || src.domain}</span>
                            <span className="text-xs font-semibold text-gray-500 ml-2">{Math.round(src.coverage_percent || 0)}%</span>
                        </div>
                        <div className="text-xs text-gray-500 mb-2 truncate">
                            {src.type === 'web' ? `🌐 ${src.domain}` : `📄 Internal Archive`}
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5">
                            <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${Math.min(100, Math.max(2, src.coverage_percent || 0))}%` }}></div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
