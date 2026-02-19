// ═══════════════════════════════════════════════════════════
// TEMU Integration - JavaScript
// ═══════════════════════════════════════════════════════════

// ═══ Constants ═══

const TEMU_CONFIG = {
    ENDPOINTS: {
        JOBS: '/api/jobs',
        LOGS: '/api/logs'
    },
    SELECTORS: {
        JOBS_CONTAINER: 'jobs-container',
        LOGS_CONTENT: 'logs-content',
        LOG_FILTER: 'log-filter'
    },
    JOB_REFRESH_INTERVAL: 5000
};

// ═══════════════════════════════════════════════════════════
// Initialization
// ═══════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    loadJobs();
    loadLogs();

    // Auto-refresh every 5 seconds
    setInterval(loadJobs, TEMU_CONFIG.JOB_REFRESH_INTERVAL);
});

// Progress Bar + Toast + formatLogEntry aus shared components:
// /components/progress-helper.js, /components/ui-helpers.js

// ═══════════════════════════════════════════════════════════
// Jobs Management
// ═══════════════════════════════════════════════════════════

async function loadJobs() {
    const container = document.getElementById(TEMU_CONFIG.SELECTORS.JOBS_CONTAINER);

    try {
        const jobs = await API_CLIENT.get(TEMU_CONFIG.ENDPOINTS.JOBS);

        if (!jobs || jobs.length === 0) {
            container.innerHTML = '<div class="loading">Keine Jobs gefunden</div>';
            return;
        }

        container.innerHTML = '';
        const fragment = document.createDocumentFragment();
        jobs.forEach(job => fragment.appendChild(renderJob(job)));
        container.appendChild(fragment);
    } catch (err) {
        console.error('Failed to load jobs:', err);
        container.innerHTML = '<div class="loading">Fehler beim Laden der Jobs</div>';
    }
}

/**
 * Create a job item DOM element (XSS-safe, no innerHTML with API data)
 */
function renderJob(job) {
    const config = job.config || {};
    const status = job.status || {};
    const jobType = config.job_type || 'unknown';
    const description = config.description || 'No description';
    const enabled = config.schedule?.enabled;
    const interval = config.schedule?.interval_minutes || 0;
    const lastRun = status.last_run ? new Date(status.last_run).toLocaleString('de-DE') : 'Nie';
    const nextRun = status.next_run ? new Date(status.next_run).toLocaleString('de-DE') : '-';
    const statusClass = status.status?.toLowerCase() || 'idle';

    const item = document.createElement('div');
    item.className = 'job-item';

    // Job info
    const info = document.createElement('div');
    info.className = 'job-info';

    const name = document.createElement('div');
    name.className = 'job-name';
    name.textContent = `${enabled ? '✅' : '⏸️'} ${jobType}`;

    const meta = document.createElement('div');
    meta.className = 'job-meta';
    meta.textContent = `${description} — Intervall: ${interval}min | Letzter Lauf: ${lastRun} | Nächster Lauf: ${nextRun}`;

    info.appendChild(name);
    info.appendChild(meta);

    // Actions
    const actions = document.createElement('div');
    actions.className = 'job-actions';

    const statusBadge = document.createElement('span');
    statusBadge.className = `job-status ${statusClass}`;
    statusBadge.textContent = status.status || 'IDLE';

    const intervalBtn = document.createElement('button');
    intervalBtn.className = 'btn btn-secondary btn-sm';
    intervalBtn.textContent = '⏱️';
    intervalBtn.title = 'Intervall ändern';
    intervalBtn.addEventListener('click', () => openIntervalDialog(job.job_id, interval));

    const toggleBtn = document.createElement('button');
    toggleBtn.className = `btn ${enabled ? 'btn-success' : 'btn-secondary'} btn-sm`;
    toggleBtn.textContent = enabled ? '✓' : '✗';
    toggleBtn.title = enabled ? 'Deaktivieren' : 'Aktivieren';
    toggleBtn.addEventListener('click', () => toggleJob(job.job_id, !enabled));

    actions.appendChild(statusBadge);
    actions.appendChild(intervalBtn);
    actions.appendChild(toggleBtn);

    item.appendChild(info);
    item.appendChild(actions);
    return item;
}

function refreshJobs() {
    loadJobs();
    showToast('Jobs aktualisiert', 'info');
}

// ═══════════════════════════════════════════════════════════
// Manual Triggers
// ═══════════════════════════════════════════════════════════

/**
 * Find a job by type and trigger it with parameters
 * @param {string} jobType - e.g. 'sync_orders', 'sync_inventory'
 * @param {string} queryString - URL query params
 * @param {string} progressText - Text for progress overlay
 * @param {string} successText - Toast text on success
 */
async function triggerJob(jobType, queryString, progressText, successText) {
    try {
        showProgress(progressText);

        const jobs = await API_CLIENT.get(TEMU_CONFIG.ENDPOINTS.JOBS);
        const job = jobs.find(j => j.config?.job_type === jobType);

        if (!job) {
            throw new Error(`${jobType} Job nicht gefunden`);
        }

        const data = await API_CLIENT.post(`${TEMU_CONFIG.ENDPOINTS.JOBS}/${job.job_id}/run-now?${queryString}`);
        updateProgress(100, 'Gestartet!');

        setTimeout(() => {
            hideProgress();
            if (data.status === 'triggered') {
                showToast(successText, 'success');
                loadJobs();
            } else {
                showToast('Fehler beim Starten', 'error');
            }
        }, 500);
    } catch (err) {
        hideProgress();
        showToast(`Fehler: ${err.message}`, 'error');
    }
}

async function triggerOrderSync() {
    const params = await showOrderSyncParameterDialog();
    if (params === null) return;

    const query = `parent_order_status=${params.status}&days_back=${params.days}&verbose=${params.verbose}`;
    await triggerJob(
        'sync_orders',
        query,
        'Starte Order Sync Workflow...',
        `Order Sync gestartet (Status: ${params.status}, Tage: ${params.days})`
    );
}

async function triggerInventorySync() {
    const params = await showInventorySyncParameterDialog();
    if (params === null) return;

    const modeText = params.mode === 'full' ? 'Vollständig (Steps 1-4)' : 'Quick Sync (Steps 3+4)';
    const query = `mode=${params.mode}&verbose=${params.verbose}`;
    await triggerJob(
        'sync_inventory',
        query,
        `Starte ${modeText}...`,
        `Inventory Sync gestartet (${modeText})`
    );
}

// ═══════════════════════════════════════════════════════════
// Logs
// ═══════════════════════════════════════════════════════════

async function loadLogs() {
    try {
        const filter = document.getElementById(TEMU_CONFIG.SELECTORS.LOG_FILTER).value || 'temu';
        const logs = await API_CLIENT.get(`${TEMU_CONFIG.ENDPOINTS.LOGS}?job_id=${filter}&limit=200`);

        const container = document.getElementById(TEMU_CONFIG.SELECTORS.LOGS_CONTENT);

        if (!logs || logs.length === 0) {
            container.textContent = 'Keine Logs verfügbar';
            return;
        }

        container.textContent = logs.map(formatLogEntry).join('\n');
    } catch (err) {
        console.error('Failed to load logs:', err);
    }
}

function filterLogs() {
    loadLogs();
}

function refreshLogs() {
    loadLogs();
    showToast('Logs aktualisiert', 'info');
}

// ═══════════════════════════════════════════════════════════
// Job Settings
// ═══════════════════════════════════════════════════════════

async function openIntervalDialog(jobId, currentInterval) {
    const newInterval = prompt(`Neues Intervall in Minuten (aktuell: ${currentInterval} Min):`, currentInterval);

    if (newInterval === null || newInterval === '') return;

    const interval = parseInt(newInterval);
    if (isNaN(interval) || interval < 1) {
        showToast('Ungültiges Intervall! Bitte eine Zahl >= 1 eingeben.', 'error');
        return;
    }

    try {
        await API_CLIENT.post(`${TEMU_CONFIG.ENDPOINTS.JOBS}/${jobId}/schedule?interval_minutes=${interval}`);
        showToast(`Intervall geändert auf ${interval} Minuten`, 'success');
        loadJobs();
    } catch (err) {
        console.error('Failed to update interval:', err);
        showToast(`Fehler: ${err.message}`, 'error');
    }
}

async function toggleJob(jobId, enabled) {
    try {
        await API_CLIENT.post(`${TEMU_CONFIG.ENDPOINTS.JOBS}/${jobId}/toggle?enabled=${enabled}`);
        showToast(`Job ${enabled ? 'aktiviert' : 'deaktiviert'}`, 'success');
        loadJobs();
    } catch (err) {
        console.error('Failed to toggle job:', err);
        showToast(`Fehler: ${err.message}`, 'error');
    }
}

// ═══════════════════════════════════════════════════════════
// Modal Dialog Helper
// ═══════════════════════════════════════════════════════════

/**
 * Create and show a modal dialog, returns a Promise that resolves when submitted or null on cancel
 * @param {Object} opts
 * @param {string} opts.title - Modal header text
 * @param {string} opts.submitBtnClass - CSS class for submit button (e.g. 'btn-primary')
 * @param {Function} opts.buildBody - Function that creates the modal body DOM content
 * @param {Function} opts.getParams - Function that reads form values and returns params object
 */
function showModal({ title, submitBtnClass = 'btn-primary', buildBody, getParams }) {
    return new Promise((resolve) => {
        const dialog = document.createElement('div');
        dialog.className = 'modal active';

        const content = document.createElement('div');
        content.className = 'modal-content';

        // Header
        const header = document.createElement('div');
        header.className = 'modal-header';
        header.textContent = title;

        // Body
        const body = document.createElement('div');
        body.className = 'modal-body';
        body.appendChild(buildBody());

        // Footer
        const footer = document.createElement('div');
        footer.className = 'modal-footer';

        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'btn btn-secondary';
        cancelBtn.textContent = 'Abbrechen';

        const submitBtn = document.createElement('button');
        submitBtn.className = `btn ${submitBtnClass}`;
        submitBtn.textContent = '▶️ Starten';

        footer.appendChild(cancelBtn);
        footer.appendChild(submitBtn);

        content.appendChild(header);
        content.appendChild(body);
        content.appendChild(footer);
        dialog.appendChild(content);
        document.body.appendChild(dialog);

        function close(result) {
            dialog.remove();
            resolve(result);
        }

        cancelBtn.addEventListener('click', () => close(null));
        submitBtn.addEventListener('click', () => close(getParams()));
        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) close(null);
        });
    });
}

// ═══════════════════════════════════════════════════════════
// Parameter Dialogs
// ═══════════════════════════════════════════════════════════

function showOrderSyncParameterDialog() {
    return showModal({
        title: '⚙️ Order Sync Parameter',
        submitBtnClass: 'btn-primary',
        buildBody() {
            const grid = document.createElement('div');
            grid.className = 'modal-form-grid';

            // Status select
            const statusField = document.createElement('div');
            const statusLabel = document.createElement('label');
            statusLabel.textContent = '📊 Status:';
            const statusSelect = document.createElement('select');
            statusSelect.id = 'param-status';
            [
                { value: '2', text: '2 - UN_SHIPPING (nicht versendet)' },
                { value: '3', text: '3 - CANCELLED (storniert)' },
                { value: '4', text: '4 - SHIPPED (versendet)' },
                { value: '5', text: '5 - RECEIPTED (Order received)' }
            ].forEach(({ value, text }) => {
                const opt = document.createElement('option');
                opt.value = value;
                opt.textContent = text;
                statusSelect.appendChild(opt);
            });
            statusField.appendChild(statusLabel);
            statusField.appendChild(statusSelect);

            // Days input
            const daysField = document.createElement('div');
            const daysLabel = document.createElement('label');
            daysLabel.textContent = '📅 Tage zurück:';
            const daysInput = document.createElement('input');
            daysInput.type = 'number';
            daysInput.id = 'param-days';
            daysInput.value = '7';
            daysInput.min = '1';
            daysInput.max = '365';
            const daysHint = document.createElement('p');
            daysHint.className = 'modal-field-hint';
            daysHint.textContent = 'Wie viele Tage in die Vergangenheit sollen Orders gesucht werden?';
            daysField.appendChild(daysLabel);
            daysField.appendChild(daysInput);
            daysField.appendChild(daysHint);

            // Verbose checkbox
            const verboseField = createVerboseCheckbox();

            grid.appendChild(statusField);
            grid.appendChild(daysField);
            grid.appendChild(verboseField);
            return grid;
        },
        getParams() {
            return {
                status: parseInt(document.getElementById('param-status').value),
                days: parseInt(document.getElementById('param-days').value),
                verbose: document.getElementById('param-verbose').checked
            };
        }
    });
}

function showInventorySyncParameterDialog() {
    return showModal({
        title: '⚙️ Inventory Sync Parameter',
        submitBtnClass: 'btn-success',
        buildBody() {
            const grid = document.createElement('div');
            grid.className = 'modal-form-grid';

            // Mode select
            const modeField = document.createElement('div');
            const modeLabel = document.createElement('label');
            modeLabel.textContent = '🔄 Sync-Modus:';
            const modeSelect = document.createElement('select');
            modeSelect.id = 'param-mode';
            [
                { value: 'quick', text: 'Quick Sync (Steps 3+4) - Nur Bestandsabgleich' },
                { value: 'full', text: 'Vollständig (Steps 1-4) - Inkl. SKU-Import' }
            ].forEach(({ value, text }) => {
                const opt = document.createElement('option');
                opt.value = value;
                opt.textContent = text;
                modeSelect.appendChild(opt);
            });

            // Help box
            const helpBox = document.createElement('div');
            helpBox.className = 'modal-help-box';

            const quickTitle = document.createElement('p');
            quickTitle.className = 'help-title recommended';
            quickTitle.textContent = 'Quick Sync (Empfohlen):';

            const quickText = document.createElement('p');
            quickText.className = 'help-text';
            quickText.textContent = 'Aktualisiert nur JTL-Bestände und sendet Updates an TEMU. Schneller und für regelmäßige Synchronisation geeignet.';

            const fullTitle = document.createElement('p');
            fullTitle.className = 'help-title alternative';
            fullTitle.textContent = 'Vollständig:';

            const fullText = document.createElement('p');
            fullText.className = 'help-text';
            fullText.textContent = 'Lädt alle SKUs von TEMU, importiert sie in die Datenbank, dann Bestandsabgleich. Langsamer, nur nötig wenn neue SKUs hinzugekommen sind.';

            helpBox.appendChild(quickTitle);
            helpBox.appendChild(quickText);
            helpBox.appendChild(fullTitle);
            helpBox.appendChild(fullText);

            modeField.appendChild(modeLabel);
            modeField.appendChild(modeSelect);
            modeField.appendChild(helpBox);

            // Verbose checkbox
            const verboseField = createVerboseCheckbox();

            grid.appendChild(modeField);
            grid.appendChild(verboseField);
            return grid;
        },
        getParams() {
            return {
                mode: document.getElementById('param-mode').value,
                verbose: document.getElementById('param-verbose').checked
            };
        }
    });
}

/**
 * Create a standard verbose mode checkbox field
 */
function createVerboseCheckbox() {
    const field = document.createElement('div');
    const label = document.createElement('label');
    label.className = 'checkbox-label';

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = 'param-verbose';

    const text = document.createElement('span');
    text.textContent = '🔍 Verbose Mode';

    label.appendChild(checkbox);
    label.appendChild(text);
    field.appendChild(label);
    return field;
}
