import axios from 'axios';

// Base URL configuration - In production this would come from env vars
const API_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
    baseURL: API_URL,
});

const Client = {
    // Auth - Placeholder / Mock for now as Backend Auth isn't ready
    auth: {
        login: async (username, password) => {
            // Simulate success for development continuity
            return {
                access_token: "dev_token",
                token_type: "bearer",
                role: "faculty",
                user: { name: "Dev User", email: username }
            };
        }
    },

    documents: {
        list: async () => {
            const response = await api.get('/documents');
            // Transform backend response to match frontend expectations if needed
            return response.data;
        },

        upload: async (file) => {
            const formData = new FormData();
            formData.append('file', file);

            const response = await api.post('/documents/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });
            return response.data;
        }
    },

    // Reports - Placeholder
    reports: {
        get: async (docId) => {
            return {
                document_id: docId,
                total_score: 0,
                citations: [],
                segments: []
            };
        }
    },

    // Admin - Placeholder
    admin: {
        getConfig: async () => ({}),
        updateConfig: async () => ({})
    }
};

export default Client;
