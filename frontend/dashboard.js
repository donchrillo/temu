/**
 * Dashboard - System Status & Service Worker Registration
 * Loaded by index-new.html
 */

const DASHBOARD_CONFIG = {
    ENDPOINTS: {
        HEALTH: '/api/health'
    },
    SELECTORS: {
        GATEWAY_STATUS: 'gateway-status',
        MODULES_COUNT: 'modules-count',
        VERSION: 'version'
    }
};

/**
 * Load and display system health status
 */
async function loadStatus() {
    try {
        const response = await fetch(DASHBOARD_CONFIG.ENDPOINTS.HEALTH);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        document.getElementById(DASHBOARD_CONFIG.SELECTORS.MODULES_COUNT).textContent =
            data.modules?.length || 0;
        document.getElementById(DASHBOARD_CONFIG.SELECTORS.VERSION).textContent =
            data.version || 'N/A';
    } catch (error) {
        console.error('Failed to load status:', error);
        renderOfflineStatus();
    }
}

/**
 * Show offline indicator when health check fails
 */
function renderOfflineStatus() {
    const statusEl = document.getElementById(DASHBOARD_CONFIG.SELECTORS.GATEWAY_STATUS);
    if (!statusEl) return;

    statusEl.textContent = '';

    const indicator = document.createElement('span');
    indicator.className = 'status-indicator offline';
    statusEl.appendChild(indicator);
    statusEl.appendChild(document.createTextNode(' Offline'));
}

/**
 * Register service worker for PWA support
 */
function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/service-worker.js').catch(console.error);
        });
    }
}

// Initialize
registerServiceWorker();
loadStatus();
