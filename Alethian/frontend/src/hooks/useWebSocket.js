import { useState, useEffect } from 'react';

export function useWebSocket(documentId) {
    const [status, setStatus] = useState({ stage: 'connecting', progress: 0, message: 'Connecting to WebSocket...' });

    useEffect(() => {
        if (!documentId) return;
        
        let ws = null;
        let reconnectTimeout = null;

        const connect = () => {
            ws = new WebSocket(`ws://localhost:8000/api/v1/documents/${documentId}/status`);
            
            ws.onopen = () => {
                setStatus({ stage: 'connected', progress: 0, message: 'Connected to status stream' });
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    setStatus(data);
                } catch (e) {
                    console.error("Failed to parse websocket message", e);
                }
            };

            ws.onclose = () => {
                setStatus({ stage: 'disconnected', progress: 0, message: 'Disconnected. Reconnecting...' });
                reconnectTimeout = setTimeout(connect, 3000);
            };

            ws.onerror = (error) => {
                console.error("WebSocket error", error);
                ws.close();
            };
        };

        connect();

        return () => {
            if (reconnectTimeout) clearTimeout(reconnectTimeout);
            if (ws) ws.close();
        };
    }, [documentId]);

    return status;
}
