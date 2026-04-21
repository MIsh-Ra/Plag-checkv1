import { useEffect, useRef, useCallback } from 'react';
import { useReportStore } from '../../stores/reportStore';

/**
 * Applies highlight spans to a plain text string given an array of char-range matches.
 * Returns an array of React elements (text nodes + highlighted spans).
 */
function buildHighlightedSegments(text, matches, charOffset) {
    if (!matches || matches.length === 0) {
        return [<span key="all">{text}</span>];
    }

    // Translate global char coords to local (page-relative) coords
    const localMatches = matches
        .filter(m => {
            const s = (m.submitted_start_char || 0) - charOffset;
            const e = (m.submitted_end_char || 0) - charOffset;
            return e > 0 && s < text.length;
        })
        .map(m => ({
            start: Math.max(0, (m.submitted_start_char || 0) - charOffset),
            end: Math.min(text.length, (m.submitted_end_char || 0) - charOffset),
            type: m.type,
            id: m.id,
            sim: m.similarity || m.similarity_score || 0,
        }))
        .sort((a, b) => a.start - b.start);

    if (localMatches.length === 0) {
        return [<span key="all">{text}</span>];
    }

    // Spec colours: Red=exact, Orange=paraphrase, Blue=web (Report_Design_v2 §3.1)
    const getHighlightStyle = (type) => {
        switch (type) {
            case 'internal_exact':
                return { background: 'rgba(239,68,68,0.25)', borderBottom: '2px solid #ef4444' };
            case 'internal_paraphrase':
                return { background: 'rgba(249,115,22,0.20)', borderBottom: '2px solid #f97316' };
            case 'web':
                return { background: 'rgba(59,130,246,0.18)', borderBottom: '2px solid #3b82f6' };
            default:
                return { background: 'rgba(100,100,100,0.15)' };
        }
    };

    const segments = [];
    let cursor = 0;

    for (const match of localMatches) {
        if (cursor < match.start) {
            segments.push(
                <span key={`txt-${cursor}`}>{text.slice(cursor, match.start)}</span>
            );
        }
        segments.push(
            <mark
                key={`hl-${match.id}-${match.start}`}
                style={getHighlightStyle(match.type)}
                title={`${match.type.replace(/_/g, ' ')} — ${Math.round(match.sim)}% similarity`}
                className="cursor-pointer rounded-[2px] px-[1px] transition-opacity hover:opacity-80"
            >
                {text.slice(match.start, match.end)}
            </mark>
        );
        cursor = match.end;
    }

    if (cursor < text.length) {
        segments.push(<span key={`txt-end-${cursor}`}>{text.slice(cursor)}</span>);
    }

    return segments;
}

export default function TextOverlay({ pageTexts, documentText, matches }) {
    const { currentPage, setCurrentPage } = useReportStore();
    const pageRefs = useRef({});
    const containerRef = useRef(null);

    // Scroll to currentPage whenever heatmap click changes it
    useEffect(() => {
        if (!currentPage) return;
        const el = pageRefs.current[currentPage];
        if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, [currentPage]);

    // Observe which page is visible for scroll-sync back to heatmap
    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                // Find the topmost visible page
                let topEntry = null;
                for (const entry of entries) {
                    if (entry.isIntersecting) {
                        if (!topEntry || entry.boundingClientRect.top < topEntry.boundingClientRect.top) {
                            topEntry = entry;
                        }
                    }
                }
                if (topEntry) {
                    const pageNum = parseInt(topEntry.target.dataset.page, 10);
                    if (pageNum && pageNum !== currentPage) {
                        setCurrentPage(pageNum);
                    }
                }
            },
            {
                root: containerRef.current,
                threshold: 0.3,
                rootMargin: '0px 0px -40% 0px',
            }
        );

        Object.values(pageRefs.current).forEach(el => {
            if (el) observer.observe(el);
        });

        return () => observer.disconnect();
    }, [pageTexts, documentText, setCurrentPage]);

    // Build pages array: prefer page_texts from backend; fall back to
    // splitting the monolithic document_text by estimated page size.
    let pages = [];
    if (pageTexts && pageTexts.length > 0) {
        pages = pageTexts;
    } else if (documentText) {
        // Fallback: roughly split at ~4000 chars per page
        const CHARS_PER_PAGE = 4000;
        let offset = 0;
        let pg = 1;
        while (offset < documentText.length) {
            const chunk = documentText.slice(offset, offset + CHARS_PER_PAGE);
            pages.push({ page: pg, text: chunk, char_start: offset, char_end: offset + chunk.length });
            offset += CHARS_PER_PAGE;
            pg++;
        }
        if (pages.length === 0 && documentText) {
            pages = [{ page: 1, text: documentText, char_start: 0, char_end: documentText.length }];
        }
    }

    if (pages.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-on-surface-variant text-xs font-mono uppercase tracking-widest">
                No document text available.
            </div>
        );
    }

    const activeMatches = (matches || []).filter(m => !m.is_excluded);

    return (
        <div ref={containerRef} className="h-full overflow-y-auto">
            {pages.map((pg) => {
                const pageNum = pg.page;
                const isActive = pageNum === currentPage;

                return (
                    <div
                        key={pageNum}
                        ref={el => { pageRefs.current[pageNum] = el; }}
                        id={`page-${pageNum}`}
                        data-page={pageNum}
                        className="relative mx-auto my-6 bg-white shadow-md"
                        style={{
                            // A4-proportioned page look: 794px wide, letter-style margins
                            width: '720px',
                            minHeight: '988px',
                            padding: '72px 80px',
                            fontFamily: '"Times New Roman", Times, serif',
                            fontSize: '12px',
                            lineHeight: '1.75',
                            color: '#111',
                            boxSizing: 'border-box',
                            borderTop: isActive ? '3px solid #6366f1' : '3px solid transparent',
                            transition: 'border-color 0.3s',
                        }}
                    >
                        {/* Page header */}
                        <div
                            style={{
                                position: 'absolute',
                                top: '24px',
                                left: '80px',
                                right: '80px',
                                display: 'flex',
                                justifyContent: 'space-between',
                                fontSize: '9px',
                                color: '#9ca3af',
                                fontFamily: 'monospace',
                                letterSpacing: '0.08em',
                                textTransform: 'uppercase',
                                borderBottom: '1px solid #e5e7eb',
                                paddingBottom: '4px',
                            }}
                        >
                            <span>Alethian — Document View</span>
                            <span>Page {pageNum} of {pages.length}</span>
                        </div>

                        {/* Page body text with highlighted match ranges */}
                        <p style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                            {buildHighlightedSegments(pg.text, activeMatches, pg.char_start)}
                        </p>

                        {/* Page footer */}
                        <div
                            style={{
                                position: 'absolute',
                                bottom: '20px',
                                left: '80px',
                                right: '80px',
                                textAlign: 'center',
                                fontSize: '9px',
                                color: '#d1d5db',
                                fontFamily: 'monospace',
                                borderTop: '1px solid #e5e7eb',
                                paddingTop: '4px',
                            }}
                        >
                            {pageNum}
                        </div>
                    </div>
                );
            })}
            {/* Bottom padding so last page can scroll past header */}
            <div style={{ height: '100px' }} />
        </div>
    );
}
