/**
 * Mock API Client for Alethian Frontend Development
 * Simulates Backend responses based on API_Spec.md
 */

// Simulated Delay to mimic network latency
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const MockClient = {
    auth: {
        login: async (username, password) => {
            await delay(1000);
            if (username === "admin@university.edu" && password === "admin") {
                return {
                    access_token: "mock_token_admin_123",
                    token_type: "bearer",
                    role: "admin",
                    user: { name: "Admin System", email: username }
                };
            }
            return {
                access_token: "mock_token_faculty_456",
                token_type: "bearer",
                role: "faculty",
                user: { name: "Prof. Xavier", email: username }
            };
        }
    },

    documents: {
        list: async () => {
            await delay(800);
            return [
                {
                    id: "1",
                    title: "Analysis of Deep Learning Architectures in Healthcare",
                    author: "J. Doe",
                    status: "complete",
                    score: 85.5,
                    uploaded_at: "2026-02-05T10:00:00Z"
                },
                {
                    id: "2",
                    title: "Quantum Computing: A Review",
                    author: "B. Wayne",
                    status: "ready", // Ready/Perfect
                    score: 0.0,
                    uploaded_at: "2026-02-04T15:30:00Z"
                },
                {
                    id: "3",
                    title: "Modern History of Artificial Intelligence",
                    author: "A. Smith",
                    status: "processing",
                    progress: 45, // Simulation for progress bar
                    uploaded_at: "2026-02-05T11:20:00Z"
                }
            ];
        },

        upload: async (file) => {
            await delay(2000);
            return {
                id: Math.random().toString(36).substr(2, 9),
                filename: file.name,
                status: "processing"
            };
        }
    },

    reports: {
        get: async (docId) => {
            await delay(1200);
            if (docId === "2") {
                return { // Clean report
                    document_id: "2",
                    total_score: 0.0,
                    citations: [],
                    segments: []
                };
            }

            // Default Dirty Report
            return {
                document_id: docId,
                total_score: 85.5,
                citations: [
                    {
                        id: 101,
                        text: "Smith, J. (2029). The End of Privacy.",
                        status: "hallucinated", // Red
                        page: 12,
                        context: "As argued by [Smith 2029], privacy is effectively dead."
                    },
                    {
                        id: 102,
                        text: "Wong, L. et al. (2023). AR Privacy Concerns.",
                        status: "verified", // Green
                        page: 3,
                        context: "Rapid advances in AR lead to privacy issues [Wong et al., 2023]."
                    }
                ],
                segments: [
                    {
                        id: 201,
                        type: "internal_similarity",
                        score: 0.92,
                        source: "Local Archive: Thesis_2021 (K. West)",
                        page: 45,
                        text_content: "...data clearly shows a linear trend in user adoption. This specific pattern was previously observed...",
                        match_content: "...data clearly shows a linear trend in user adoption. This specific pattern was previously observed..."
                    },
                    {
                        id: 202,
                        type: "web_dragnet",
                        score: 0.88,
                        source: "wikipedia.org/wiki/Deep_learning",
                        page: 2,
                        text_content: "Deep learning is part of a broader family of machine learning methods based on artificial neural networks."
                    }
                ]
            };
        }
    },

    admin: {
        getConfig: async () => {
            await delay(500);
            return {
                threshold_similarity: 0.8,
                semantic_scholar_key: "sk-********************",
                serper_key: "****************",
                api_status: {
                    semantic_scholar: "ok",
                    serper: "error_quota" // To show error state UI
                }
            };
        },
        updateConfig: async (config) => {
            await delay(1000);
            return { message: "Configuration updated successfully" };
        }
    }
};

export default MockClient;
