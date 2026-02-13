/**
 * Shared UI Helpers - Toast Notifications & Log Formatting
 * Genutzt von temu.js und pdf.js
 * 
 * Voraussetzung im HTML:
 * <div id="toast-container"></div>
 *
 * Usage:
 * showToast('Erfolgreich!', 'success');
 * showToast('Fehler aufgetreten', 'error');
 * const line = formatLogEntry(logObject);
 */

// ═══ Toast Notifications ═══

const TOAST_DURATION = 3000;

/**
 * Show a toast notification
 * @param {string} message - Toast message text
 * @param {string} [type='info'] - Toast type: 'info', 'success', 'error'
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) {
        console.error('Toast container (#toast-container) not found');
        return;
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, TOAST_DURATION);
}

// ═══ Log Formatting ═══

/**
 * Format a log entry for display
 * @param {Object} log - Log entry with timestamp, job_type, level, message
 * @returns {string} Formatted log line
 */
function formatLogEntry(log) {
    const time = new Date(log.timestamp).toLocaleString('de-DE');
    return `[${time}] [${log.job_type}] [${log.level}] ${log.message}`;
}
