// API Wrapper for CreditLens AI
const API = {
    BASE_URL: '/api/v1',

    async get(endpoint) {
        try {
            const response = await fetch(`${this.BASE_URL}${endpoint}`);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP Error ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`GET request failed: ${endpoint}`, error);
            throw error;
        }
    },

    async post(endpoint, data) {
        try {
            const response = await fetch(`${this.BASE_URL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP Error ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`POST request failed: ${endpoint}`, error);
            throw error;
        }
    }
};
