import { useState } from 'react';
import { useReportStore } from '../../stores/reportStore';
import { FileText, Globe } from 'lucide-react';
import Client from '../../api/client';
import { useParams } from 'react-router-dom';

export default function MatchCard({ match, onUpdate }) {
    const { id } = useParams();
    const { setSelectedMatch, selectedMatchId } = useReportStore();
    const [isEditingComment, setIsEditingComment] = useState(false);
    const [commentText, setCommentText] = useState(match.comment || "");

    const handleExclude = (e) => {
        e.stopPropagation();
        Client.reports.excludeMatch(id, match.id, { is_excluded: true, reason: 'faculty_review' })
            .then(() => onUpdate && onUpdate());
    };

    const handleRestore = (e) => {
        e.stopPropagation();
        Client.reports.excludeMatch(id, match.id, { is_excluded: false })
            .then(() => onUpdate && onUpdate());
    };

    const handleSaveComment = (e) => {
        e.stopPropagation();
        Client.reports.commentMatch(id, match.id, commentText).then(() => {
            setIsEditingComment(false);
            if (onUpdate) onUpdate();
        });
    };

    if (match.is_excluded) {
        return (
            <div className="p-4 bg-surface-container border border-ghost opacity-50 transition-opacity hover:opacity-100 flex justify-between items-center pr-6">
                <span className="text-on-surface-variant font-mono text-xs uppercase tracking-widest line-through">EXCLUDED ANOMALY</span>
                <button onClick={handleRestore} className="text-secondary font-bold text-xs uppercase hover:underline">RESTORE</button>
            </div>
        );
    }

    const isInternal = match.type === 'internal_exact' || match.type === 'internal_paraphrase';
    
    // Triage cards: 4px left-accent border based on severity
    let accentBorder = 'border-l-4 border-l-secondary';
    if (match.type === 'internal_exact') accentBorder = 'border-l-4 border-l-error';
    else if (match.type === 'internal_paraphrase') accentBorder = 'border-l-4 border-l-primary-fixed';

    const Icon = isInternal ? FileText : Globe;
    const isSelected = selectedMatchId === match.id;

    return (
        <div
            onClick={() => setSelectedMatch(match.id)}
            className={`p-4 bg-surface-container border border-ghost cursor-pointer transition-colors ${accentBorder} ${
                isSelected ? 'bg-surface-container-highest shadow-ambient border-outline' : 'hover:bg-surface-container-high'
            }`}
        >
            <div className="flex justify-between items-start mb-3">
                <span className="inline-flex items-center text-[10px] font-bold uppercase tracking-widest text-on-surface">
                    <Icon className="w-3 h-3 mr-2" />
                    {match.type.replace('_', ' ')}
                </span>
                <span className={`text-xs font-mono font-bold ${match.similarity >= 80 ? 'text-error' : 'text-on-surface'}`}>
                    {Math.round(match.similarity)}%
                </span>
            </div>

            <div className={`text-sm text-on-surface font-sans leading-relaxed line-clamp-3 mb-4`}>
                "{match.submitted_text}"
            </div>

            <div className="flex items-center justify-between text-xs text-on-surface-variant font-mono uppercase tracking-widest pt-2 border-t border-ghost">
                <span>PAGE {match.submitted_page}</span>
                <div className="space-x-4">
                    <button onClick={(e) => { e.stopPropagation(); setIsEditingComment(true); }} className="hover:text-primary transition-colors">COMMENT</button>
                    <button onClick={handleExclude} className="text-error hover:text-error-container transition-colors">EXCLUDE</button>
                </div>
            </div>

            {isEditingComment ? (
                <div className="mt-4 pt-3 border-t border-ghost" onClick={(e) => e.stopPropagation()}>
                    <textarea 
                        value={commentText} 
                        onChange={(e) => setCommentText(e.target.value)} 
                        className="w-full text-xs font-mono p-3 bg-surface border border-ghost text-on-surface focus:border-outline focus:outline-none transition-colors rounded-none placeholder-on-surface-variant/50 min-h-[60px]" 
                        placeholder="ENTER TRIAGE LOG..."
                    />
                    <div className="flex justify-end space-x-3 mt-2">
                        <button onClick={() => setIsEditingComment(false)} className="text-xs font-mono text-on-surface-variant hover:text-on-surface">CANCEL</button>
                        <button onClick={handleSaveComment} className="text-xs font-mono text-secondary font-bold hover:text-secondary-fixed">SAVE LOG</button>
                    </div>
                </div>
            ) : match.comment && (
                <div className="mt-4 pt-3 border-t border-ghost bg-surface-container-lowest p-3">
                    <div className="text-[10px] uppercase font-bold tracking-widest text-secondary mb-1">TRIAGE LOG</div>
                    <div className="text-xs text-on-surface">{match.comment}</div>
                </div>
            )}
        </div>
    );
}
