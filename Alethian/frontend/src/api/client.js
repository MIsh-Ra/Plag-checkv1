import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';

const api = axios.create({ baseURL: API_URL });

// Attach JWT token to every request
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('alethian_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

const Client = {
    auth: {
        login: async (username, password) => {
            const response = await api.post('/auth/login', { username, password });
            return response.data;
        }
    },

    documents: {
        list: async (params = {}) => {
            const response = await api.get('/documents', { params });
            return response.data;
        },
        get: async (id) => {
            const response = await api.get(`/documents/${id}`);
            return response.data;
        },
        upload: async (file, courseId = null) => {
            const formData = new FormData();
            formData.append('file', file);
            if (courseId) formData.append('course_id', courseId);
            const response = await api.post('/documents/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            return response.data;
        }
    },

    reports: {
        get: async (documentId) => {
            const response = await api.get(`/reports/${documentId}`);
            return response.data;
        },
        getHeatmap: async (documentId) => {
            const response = await api.get(`/reports/${documentId}/heatmap`);
            return response.data;
        },
        excludeMatch: async (documentId, matchId, data) => {
            const response = await api.patch(`/reports/${documentId}/matches/${matchId}`, data);
            return response.data;
        },
        commentMatch: async (documentId, matchId, comment) => {
            const response = await api.post(`/reports/${documentId}/matches/${matchId}/comment`, { comment });
            return response.data;
        },
        review: async (documentId, data) => {
            const response = await api.post(`/reports/${documentId}/review`, data);
            return response.data;
        },
        exportPdf: async (documentId) => {
            const response = await api.get(`/reports/${documentId}/export/pdf`, { responseType: 'blob' });
            // Trigger browser download
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const a = document.createElement('a');
            a.href = url;
            a.download = `report_${documentId}.pdf`;
            a.click();
            window.URL.revokeObjectURL(url);
        },
        exportJson: async (documentId) => {
            const response = await api.get(`/reports/${documentId}/export/json`);
            return response.data;
        }
    },

    admin: {
        getConfig: async () => {
            const response = await api.get('/admin/config');
            return response.data;
        },
        updateConfig: async (data) => {
            const response = await api.patch('/admin/config', data);
            return response.data;
        }
    }
};

export default Client;
