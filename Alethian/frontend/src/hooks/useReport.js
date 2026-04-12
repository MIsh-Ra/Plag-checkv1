import { useState, useEffect } from 'react';
import Client from '../api/client';

export function useReport(id) {
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!id) return;

        const fetchReport = async () => {
            try {
                const data = await Client.reports.get(id);
                setReport(data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchReport();
    }, [id]);

    return { report, loading, setReport };
}
