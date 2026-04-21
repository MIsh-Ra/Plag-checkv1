import { useReportStore } from '../../stores/reportStore';

const TYPE_COLORS = {
    internal_exact: '#ef4444',
    internal_paraphrase: '#f97316',
    web: '#3b82f6',
    clean: '#22c55e',
};

function getColor(page) {
    const density = page.match_density ?? page.density_score ?? 0;
    if (density === 0) return '#22c55e';
    if (density <= 0.25) return '#eab308';
    if (density <= 0.50) return '#f97316';
    if (density <= 0.75) return '#ef4444';
    return '#dc2626';
}

export default function Heatmap({ pages }) {
    const { currentPage, setCurrentPage } = useReportStore();

    if (!pages || pages.length === 0) {
        return (
            <div className="text-on-surface-variant text-xs font-mono tracking-widest italic uppercase p-4">
                No heatmap data available.
            </div>
        );
    }

    const handlePageClick = (pageNum) => {
        setCurrentPage(pageNum);
        // Scroll document viewer to the selected page
        setTimeout(() => {
            const el = document.getElementById(`page-${pageNum}`);
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 50);
    };

    return (
        <div className="flex flex-col space-y-1">
            {pages.map((page) => {
                const pageNum = page.page_number;
                const density = page.match_density ?? page.density_score ?? 0;
                const color = getColor(page);
                const isActive = currentPage === pageNum;
                const barWidth = Math.max(4, Math.round(density * 100));
                const matchCount = page.match_count || 0;
                const hasMatch = matchCount > 0;

                return (
                    <button
                        key={pageNum}
                        onClick={() => handlePageClick(pageNum)}
                        title={`Page ${pageNum} — density ${Math.round(density * 100)}%${hasMatch ? ` (${matchCount} match${matchCount > 1 ? 'es' : ''})` : ''}`}
                        className={`flex items-center w-full text-left transition-all group focus:outline-none focus-visible:ring-1 focus-visible:ring-primary ${
                            isActive ? 'bg-surface-container-highest' : 'hover:bg-surface-container-high'
                        }`}
                        style={{ padding: '3px 6px', borderRadius: 0 }}
                    >
                        {/* Page number */}
                        <span
                            className="font-mono text-[9px] text-on-surface-variant shrink-0 w-6 text-right mr-2"
                            style={{ color: isActive ? color : undefined }}
                        >
                            {pageNum}
                        </span>

                        {/* Density bar */}
                        <div className="flex-1 h-4 bg-surface-container-highest relative overflow-hidden">
                            <div
                                className="absolute inset-y-0 left-0 transition-all duration-300"
                                style={{
                                    width: `${barWidth}%`,
                                    backgroundColor: color,
                                    opacity: hasMatch ? 0.85 : 0.15,
                                }}
                            />
                            {/* Breakdown sub-bars */}
                            {page.internal_density > 0 && (
                                <div
                                    className="absolute inset-y-0 left-0 opacity-40"
                                    style={{
                                        width: `${Math.round(page.internal_density * 100)}%`,
                                        backgroundColor: '#ef4444',
                                    }}
                                />
                            )}
                        </div>

                        {/* Match count pill */}
                        {hasMatch && (
                            <span
                                className="ml-2 font-mono text-[9px] font-bold px-1 rounded-sm shrink-0"
                                style={{ backgroundColor: color, color: '#fff', minWidth: '18px', textAlign: 'center' }}
                            >
                                {matchCount}
                            </span>
                        )}

                        {/* Active page indicator */}
                        {isActive && (
                            <span className="ml-1 w-1 h-1 rounded-full bg-primary shrink-0" />
                        )}
                    </button>
                );
            })}
        </div>
    );
}
