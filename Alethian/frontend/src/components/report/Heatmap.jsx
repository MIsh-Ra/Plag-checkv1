import { useReportStore } from '../../stores/reportStore';

export default function Heatmap({ data }) {
    const { currentPage, setCurrentPage } = useReportStore();

    if (!data || data.length === 0) return null;

    return (
        <div className="mb-6 bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Document Heatmap</h3>
            <div className="flex flex-wrap gap-1">
                {data.map((page) => (
                    <div
                        key={page.id || page.page_number}
                        onClick={() => setCurrentPage(page.page_number)}
                        className={`w-6 h-8 rounded-sm cursor-pointer transition-all ${currentPage === page.page_number ? 'ring-2 ring-offset-1 ring-blue-500 scale-110' : 'hover:scale-105 hover:shadow-md'}`}
                        style={{ backgroundColor: page.color || '#22c55e' }}
                        title={`Page ${page.page_number}: ${page.match_count} matches (${Math.round(page.density_score * 100)}% density)`}
                    />
                ))}
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-gray-400">
                <div className="flex items-center"><span className="w-2 h-2 rounded-full bg-green-500 mr-1" /> Clean</div>
                <div className="flex items-center"><span className="w-2 h-2 rounded-full bg-red-500 mr-1" /> High Match</div>
            </div>
        </div>
    );
}
