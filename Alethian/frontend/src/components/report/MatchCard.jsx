import { useReportStore } from '../../stores/reportStore';
import { FileText, Globe } from 'lucide-react';
import Client from '../../api/client';
import { useParams } from 'react-router-dom';

export default function MatchCard({ match }) {
    const { id } = useParams();
    const { setSelectedMatch, selectedMatchId } = useReportStore();

if (match.is_excluded) {
    return (
        <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg opacity-60">
            <div className="flex justify-between items-center text-xs">
                <span className="text-gray-500 line-through">Excluded Match</span>
                <button onClick={() => Client.reports.excludeMatch(id, match.id, { is_excluded: false }).then(() => window.location.reload())} className="text-blue-500 font-medium hover:underline">Restore</button>
            </div>
        </div>
    );
}

const isInternal = match.type === 'internal_exact' || match.type === 'internal_paraphrase';
const badgeColor = match.type === 'internal_exact' ? 'bg-red-100 text-red-800' :
    match.type === 'internal_paraphrase' ? 'bg-orange-100 text-orange-800' :
        'bg-blue-100 text-blue-800';

const Icon = isInternal ? FileText : Globe;

return (
    <div
        onClick={() => setSelectedMatch(match.id)}
        className={`p-3 bg-white border rounded-lg cursor-pointer transition-all ${selectedMatchId === match.id
                ? 'border-blue-500 shadow-md ring-1 ring-blue-500'
                : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
            }`}
    >
        <div className="flex justify-between items-start mb-2">
            <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider ${badgeColor}`}>
                <Icon className="w-3 h-3 mr-1" />
                {match.type.replace('_', ' ')}
            </span>
            <span className="text-xs font-bold text-gray-700">{Math.round(match.similarity)}%</span>
        </div>

        <div className="text-sm text-gray-800 line-clamp-3 mb-2 font-serif leading-relaxed">
            "{match.submitted_text}"
        </div>

        <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
            <span>Page {match.submitted_page}</span>
            <div className="space-x-3">
                <button onClick={(e) => {
                    e.stopPropagation();
                    const comment = prompt("Enter instructor comment:");
                    if (comment) {
                        Client.reports.commentMatch(id, match.id, comment).then(() => alert("Comment saved"));
                    }
                }} className="text-blue-600 hover:text-blue-800 font-medium">Comment</button>
                <button onClick={(e) => {
                    e.stopPropagation();
                    Client.reports.excludeMatch(id, match.id, { is_excluded: true, reason: 'faculty_review' })
                        .then(() => window.location.reload());
                }} className="text-gray-500 hover:text-red-600 font-medium">Exclude</button>
            </div>
        </div>
    </div>
    );
}
