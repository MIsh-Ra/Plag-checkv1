import { useState, useEffect, useCallback } from 'react';
import Client from '../api/client';

export function useReport(id) {
    const [report, setReport] = useState(null);
    const [documentData, setDocumentData] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchData = useCallback(async (abortSignal) => {
        if (!id) return;
        setLoading(true);
        try {
            const doc = await Client.documents.get(id);
            if (abortSignal?.aborted) return;
            setDocumentData(doc);

            if (doc.status === 'complete' || doc.status === 'ready') {
                const data = await Client.reports.get(id);
                if (abortSignal?.aborted) return;
                setReport(data);
            }
        } catch (err) {
            console.error("Error fetching report or document:", err);
        } finally {
            if (!abortSignal?.aborted) setLoading(false);
        }
    }, [id]);

    useEffect(() => {
        const controller = new AbortController();
        fetchData(controller.signal);
        return () => controller.abort();
    }, [fetchData]);

    const refetch = () => fetchData();

    return { report, documentData, loading, refetch };
}
