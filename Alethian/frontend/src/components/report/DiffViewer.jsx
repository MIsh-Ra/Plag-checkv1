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
                    return <del key={idx} className={`${removedClass} border-b border-error/50`}>{token.word} </del>;
                } else {
                    return <ins key={idx} className={`${addedClass} border-b border-primary/50`}>{token.word} </ins>;
                }
            })}
        </span>
    );
}

export default function DiffViewer({ match }) {
    if (!match) return <div className="text-on-surface-variant text-xs font-mono uppercase tracking-widest p-10 text-center">SELECT AN ANOMALY TO INITIATE CROSS-EXAMINATION.</div>;

    const isInternal = match.type === 'internal_exact' || match.type === 'internal_paraphrase';
    const { leftTokens, rightTokens } = computeWordDiff(match.submitted_text, match.source_text);

    return (
        <div className="grid grid-cols-2 gap-px bg-ghost h-full">
            <div className="bg-surface-container-low flex flex-col min-h-0">
                <div className="bg-surface-container-high px-4 py-3 border-b border-ghost flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface flex items-center">
                        <span className="w-1.5 h-1.5 bg-primary mr-2"></span> SUBMITTED EVIDENCE
                    </span>
                    <span className="text-[10px] font-mono text-on-surface-variant uppercase">PAGE {match.submitted_page}</span>
                </div>
                <div className="p-6 flex-1 overflow-y-auto font-document text-sm leading-relaxed text-on-surface">
                    <DiffTokens
                        tokens={leftTokens}
                        addedClass="bg-primary/5 text-on-surface no-underline"
                        removedClass="bg-error/10 text-error no-underline"
                    />
                </div>
            </div>

            <div className="bg-surface-container-low flex flex-col min-h-0 border-l border-ghost">
                <div className="bg-surface-container-high px-4 py-3 border-b border-ghost flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface flex items-center">
                        {isInternal ? <FileText className="w-3 h-3 mr-2 text-on-surface-variant" /> : <Globe className="w-3 h-3 mr-2 text-on-surface-variant" />}
                        {isInternal ? `ARCHIVE: ${match.source?.title || 'INTERNAL_REPO'}` : `WEB_DRAGNET: ${match.source?.domain || 'OPEN_INT'}`}
                    </span>
                    <span className="text-[10px] font-mono font-bold text-on-surface bg-surface-container-highest px-2 py-0.5 border border-ghost">
                        {Math.round(match.similarity_score ?? match.similarity ?? 0)}% MATCH
                    </span>
                </div>
                <div className="p-6 flex-1 overflow-y-auto font-document text-sm leading-relaxed text-on-surface">
                    <DiffTokens
                        tokens={rightTokens}
                        addedClass="bg-primary/5 text-on-surface no-underline"
                        removedClass="bg-error/10 text-error no-underline"
                    />
                </div>
            </div>
        </div>
    );
}
