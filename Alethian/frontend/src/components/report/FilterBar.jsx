import { useReportStore } from '../../stores/reportStore';

export default function FilterBar() {
    const { filterTypes, toggleFilterType } = useReportStore();

    return (
        <div className="mt-4">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Filter Matches</h3>
            <div className="space-y-2 text-sm">
                <label className="flex items-center cursor-pointer group">
                    <input type="checkbox" checked={filterTypes.internal_exact} onChange={() => toggleFilterType('internal_exact')} className="rounded border-gray-300 text-red-600 focus:ring-red-500 mr-3" />
                    <span className="w-3 h-3 rounded-full bg-red-500 mr-2"></span>
                    <span className="text-gray-700 group-hover:text-gray-900">Exact Archival Matches</span>
                </label>
                <label className="flex items-center cursor-pointer group">
                    <input type="checkbox" checked={filterTypes.internal_paraphrase} onChange={() => toggleFilterType('internal_paraphrase')} className="rounded border-gray-300 text-orange-500 focus:ring-orange-500 mr-3" />
                    <span className="w-3 h-3 rounded-full bg-orange-500 mr-2"></span>
                    <span className="text-gray-700 group-hover:text-gray-900">Archival Paraphrased</span>
                </label>
                <label className="flex items-center cursor-pointer group">
                    <input type="checkbox" checked={filterTypes.web} onChange={() => toggleFilterType('web')} className="rounded border-gray-300 text-blue-500 focus:ring-blue-500 mr-3" />
                    <span className="w-3 h-3 rounded-full bg-blue-500 mr-2"></span>
                    <span className="text-gray-700 group-hover:text-gray-900">Web Matches</span>
                </label>
                <div className="border-t border-gray-100 my-2 pt-2">
                    <label className="flex items-center cursor-pointer group">
                        <input type="checkbox" checked={filterTypes.excluded} onChange={() => toggleFilterType('excluded')} className="rounded border-gray-300 text-gray-500 focus:ring-gray-500 mr-3" />
                        <span className="w-3 h-3 rounded-full bg-gray-400 mr-2"></span>
                        <span className="text-gray-500 group-hover:text-gray-700 italic">Show Excluded</span>
                    </label>
                </div>
            </div>
        </div>
    );
}
