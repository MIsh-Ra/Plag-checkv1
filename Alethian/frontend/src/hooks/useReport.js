import { useState, useEffect } from 'react';
import Client from '../api/client';

export function useReport(id) {
    const [report, setReport] = useState(null);
    const [documentData, setDocumentData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!id) return;

        const fetchData = async () => {
            try {
                // Fetch document status first
                const doc = await Client.documents.get(id);
                setDocumentData(doc);

                // If document is complete or ready, try to fetch the report
                if (doc.status === 'complete' || doc.status === 'ready') {
                    const data = await Client.reports.get(id);
                    setReport(data);
                }
            } catch (err) {
                console.error("Error fetching report or document:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [id]);

    return { report, documentData, loading, setReport };
}
