import { FileText, Globe } from 'lucide-react';
import { useReportStore } from '../../stores/reportStore';

/**
 * Compute word-level diff between two texts using LCS approach (M-06).
 * Returns an array of { word, type } where type is 'same', 'added', or 'removed'.
 */
function computeWordDiff(textA, textB) {
    if (!textA || !textB) return { leftTokens: [], rightTokens: [] };

    const wordsA = textA.split(/\s+/).filter(Boolean);
    const wordsB = textB.split(/\s+/).filter(Boolean);
    const m = wordsA.length;
    const n = wordsB.length;

    // Build LCS table
    const dp = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));
    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (wordsA[i - 1].toLowerCase() === wordsB[j - 1].toLowerCase()) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }

    // Backtrack to find diff
    const leftTokens = [];
    const rightTokens = [];
    let i = m, j = n;

    const leftResult = [];
    const rightResult = [];

    while (i > 0 && j > 0) {
        if (wordsA[i - 1].toLowerCase() === wordsB[j - 1].toLowerCase()) {
            leftResult.unshift({ word: wordsA[i - 1], type: 'same' });
            rightResult.unshift({ word: wordsB[j - 1], type: 'same' });
            i--; j--;
        } else if (dp[i - 1][j] >= dp[i][j - 1]) {
            leftResult.unshift({ word: wordsA[i - 1], type: 'removed' });
            i--;
        } else {
            rightResult.unshift({ word: wordsB[j - 1], type: 'added' });
            j--;
        }
    }
    while (i > 0) {
        leftResult.unshift({ word: wordsA[i - 1], type: 'removed' });
        i--;
    }
    while (j > 0) {
        rightResult.unshift({ word: wordsB[j - 1], type: 'added' });
        j--;
    }

    return { leftTokens: leftResult, rightTokens: rightResult };
}

function DiffTokens({ tokens, addedClass, removedClass }) {
    return (
        <span>
            {tokens.map((token, idx) => {
                if (token.type === 'same') {
                    return <span key={idx}>{token.word} </span>;
                } else if (token.type === 'removed') {
                    return <del key={idx} className={removedClass}>{token.word} </del>;
                } else {
                    return <ins key={idx} className={addedClass}>{token.word} </ins>;
                }
            })}
        </span>
    );
}

export default function DiffViewer({ match }) {
    const { selectedMatchId } = useReportStore();
    
    // If we use selectedMatchId it would be passed via context, but we can accept `match` property directly here
    // for fallback since we initially fed `matches[0]` in ReportView.
    if (!match) return <div className="text-gray-400 text-sm italic">Select a match to view details.</div>;

    const isInternal = match.type === 'internal_exact' || match.type === 'internal_paraphrase';
    const { leftTokens, rightTokens } = computeWordDiff(match.submitted_text, match.source_text);

    return (
        <div className="grid grid-cols-2 gap-4">
            <div className="border border-gray-200 rounded-lg overflow-hidden bg-white shadow-sm flex flex-col">
                <div className="bg-gray-50 px-4 py-2 border-b border-gray-200 font-semibold text-sm text-gray-700">
                    <span className="text-blue-600 font-bold uppercase text-[10px] tracking-wider block mb-1">Submitted</span>
                    Page {match.submitted_page}
                </div>
                <div className="p-4 flex-1 overflow-y-auto font-serif text-gray-800 text-sm leading-relaxed bg-red-50">
                    <DiffTokens
                        tokens={leftTokens}
                        addedClass="bg-green-200 no-underline rounded px-0.5"
                        removedClass="bg-red-200 rounded px-0.5"
                    />
                </div>
            </div>

            <div className="border border-gray-200 rounded-lg overflow-hidden bg-white shadow-sm flex flex-col">
                <div className="bg-gray-50 px-4 py-2 border-b border-gray-200 font-semibold text-sm text-gray-700">
                    <span className="text-orange-600 font-bold uppercase text-[10px] tracking-wider mb-1 flex items-center">
                        {isInternal ? <FileText className="w-3 h-3 mr-1" /> : <Globe className="w-3 h-3 mr-1" />}
                        {isInternal ? `Archive: ${match.source?.title || 'Unknown Source'}` : `Web: ${match.source?.domain || 'Unknown Domain'}`}
                    </span>
                    Similarity: {Math.round(match.similarity)}%
                </div>
                <div className="p-4 flex-1 overflow-y-auto font-serif text-gray-800 text-sm leading-relaxed bg-orange-50">
                    <DiffTokens
                        tokens={rightTokens}
                        addedClass="bg-green-200 no-underline rounded px-0.5"
                        removedClass="bg-red-200 rounded px-0.5"
                    />
                </div>
            </div>
        </div>
    );
}
