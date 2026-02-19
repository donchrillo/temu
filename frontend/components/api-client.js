/**
 * API Client - Zentrale Fetch-Logik für alle Module
 * DRY-Prinzip: Einheitliche Fehlerbehandlung und Request-Handling
 */

const API_CLIENT = {
    baseUrl: '',
    
    /**
     * Basis-Request-Methode mit Fehlerbehandlung
     * @param {string} endpoint - API endpoint (ohne Basis-URL)
     * @param {Object} options - Request-Optionen
     * @returns {Promise<any>} JSON-Response
     */
    async request(endpoint, options = {}) {
        const url = this.baseUrl + endpoint;
        const config = {
            headers: { 'Content-Type': 'application/json' },
            ...options
        };
        
        try {
            const res = await fetch(url, config);
            if (!res.ok) {
                const errorText = await res.text();
                throw new Error(`HTTP ${res.status}: ${errorText || res.statusText}`);
            }
            return await res.json();
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    },
    
    /**
     * GET-Request
     * @param {string} endpoint - API endpoint
     * @returns {Promise<any>}
     */
    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },
    
    /**
     * POST-Request mit JSON-Body
     * @param {string} endpoint - API endpoint
     * @param {Object} data - Request body (wird als JSON gesendet)
     * @returns {Promise<any>}
     */
    post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    /**
     * POST-Request mit FormData (für File-Uploads)
     * @param {string} endpoint - API endpoint
     * @param {FormData} formData - FormData object
     * @returns {Promise<any>}
     */
    postFormData(endpoint, formData) {
        return this.request(endpoint, {
            method: 'POST',
            body: formData
        });
    },
    
    /**
     * POST-Request mit Query-Parametern
     * @param {string} endpoint - API endpoint
     * @param {string} queryString - URL query string (z.B. 'param1=value1&param2=value2')
     * @returns {Promise<any>}
     */
    postQuery(endpoint, queryString) {
        return this.request(endpoint + '?' + queryString, {
            method: 'POST'
        });
    }
};

// Export for global use
window.API_CLIENT = API_CLIENT;
