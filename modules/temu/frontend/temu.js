// ═══════════════════════════════════════════════════════════
// TEMU Integration - JavaScript
// ═══════════════════════════════════════════════════════════

const API_BASE = '/api';
const TEMU_API = '/api/temu';

// Progress Bar State
let progressInterval = null;
let currentProgress = 0;

// ═══════════════════════════════════════════════════════════
// Initialization
// ═══════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadJobs();
    loadLogs();

    // Auto-refresh every 5 seconds
    setInterval(loadJobs, 5000);
});

// ═══════════════════════════════════════════════════════════
// Progress Bar (same as PDF module)
// ═══════════════════════════════════════════════════════════

function showProgress(text = 'Verarbeite...') {
    const overlay = document.getElementById('progress-overlay');
    const textEl = document.getElementById('progress-text');
    const fillEl = document.getElementById('progress-fill');
    const percentEl = document.getElementById('progress-percent');

    currentProgress = 0;
    textEl.textContent = text;
    fillEl.style.width = '0%';
    percentEl.textContent = '0%';
    overlay.classList.add('active');

    if (progressInterval) clearInterval(progressInterval);
    progressInterval = setInterval(() => {
        if (currentProgress < 90) {
            currentProgress += Math.random() * 10;
            if (currentProgress > 90) currentProgress = 90;
            fillEl.style.width = currentProgress + '%';
            percentEl.textContent = Math.round(currentProgress) + '%';
        }
    }, 200);
}

function updateProgress(percent, text = null) {
    const fillEl = document.getElementById('progress-fill');
    const percentEl = document.getElementById('progress-percent');
    const textEl = document.getElementById('progress-text');

    currentProgress = percent;
    fillEl.style.width = percent + '%';
    percentEl.textContent = Math.round(percent) + '%';
    if (text) {
        textEl.textContent = text;
    }
}

function hideProgress() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    const overlay = document.getElementById('progress-overlay');
    overlay.classList.remove('active');
    currentProgress = 0;
}

// ═══════════════════════════════════════════════════════════
// Statistics
// ═══════════════════════════════════════════════════════════

async function loadStats() {
    try {
        const [statsRes, jobsRes] = await Promise.all([
            fetch(`${TEMU_API}/stats`),
            fetch(`${API_BASE}/jobs`)
        ]);

        const stats = await statsRes.json();
        const jobs = await jobsRes.json();

        document.getElementById('stat-orders').textContent = stats.orders?.total || 0;
        document.getElementById('stat-inventory').textContent = stats.inventory?.total_skus || 0;
        document.getElementById('stat-jobs').textContent = jobs?.length || 0;
    } catch (err) {
        console.error('Failed to load stats:', err);
    }
}

// ═══════════════════════════════════════════════════════════
// Jobs Management
// ═══════════════════════════════════════════════════════════

async function loadJobs() {
    try {
        const res = await fetch(`${API_BASE}/jobs`);
        const jobs = await res.json();

        const container = document.getElementById('jobs-container');

        if (!jobs || jobs.length === 0) {
            container.innerHTML = '<div class="loading">Keine Jobs gefunden</div>';
            return;
        }

        container.innerHTML = jobs.map(job => renderJob(job)).join('');
    } catch (err) {
        console.error('Failed to load jobs:', err);
        document.getElementById('jobs-container').innerHTML =
            '<div class="loading">Fehler beim Laden der Jobs</div>';
    }
}

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
    const enabledIcon = enabled ? '✅' : '⏸️';
    const toggleClass = enabled ? 'btn-success' : 'btn-secondary';
    const toggleText = enabled ? '✓' : '✗';

    return `
        <div class="job-item">
            <div class="job-info">
                <div class="job-name">${enabledIcon} ${jobType}</div>
                <div class="job-meta">
                    ${description}<br>
                    Intervall: ${interval}min | Letzter Lauf: ${lastRun} | Nächster Lauf: ${nextRun}
                </div>
            </div>
            <div style="display: flex; gap: 8px; align-items: center;">
                <span class="job-status ${statusClass}">${status.status || 'IDLE'}</span>
                <button class="btn btn-secondary btn-sm" onclick="openIntervalDialog('${job.job_id}', ${interval})" title="Intervall ändern">
                    ⏱️
                </button>
                <button class="btn ${toggleClass} btn-sm" onclick="toggleJob('${job.job_id}', ${!enabled})" title="${enabled ? 'Deaktivieren' : 'Aktivieren'}">
                    ${toggleText}
                </button>
            </div>
        </div>
    `;
}

function refreshJobs() {
    loadJobs();
    showToast('Jobs aktualisiert', 'info');
}

// ═══════════════════════════════════════════════════════════
// Manual Triggers
// ═══════════════════════════════════════════════════════════

async function triggerOrderSync() {
    try {
        // Show parameter dialog first
        const params = await showOrderSyncParameterDialog();

        if (params === null) {
            return; // User cancelled
        }

        showProgress('Starte Order Sync Workflow...');

        // Find sync_orders job
        const jobsRes = await fetch(`${API_BASE}/jobs`);
        const jobs = await jobsRes.json();
        const orderJob = jobs.find(j => j.config?.job_type === 'sync_orders');

        if (!orderJob) {
            throw new Error('Order Sync Job nicht gefunden');
        }

        // Build URL with parameters
        const url = `${API_BASE}/jobs/${orderJob.job_id}/run-now?` +
            `parent_order_status=${params.status}&` +
            `days_back=${params.days}&` +
            `verbose=${params.verbose}&` +
            `log_to_db=${params.log_to_db}`;

        const res = await fetch(url, {
            method: 'POST'
        });

        const data = await res.json();
        updateProgress(100, 'Gestartet!');

        setTimeout(() => {
            hideProgress();
            if (data.status === 'triggered') {
                showToast(`Order Sync gestartet (Status: ${params.status}, Tage: ${params.days})`, 'success');
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

async function triggerInventorySync() {
    try {
        // Show parameter dialog first
        const params = await showInventorySyncParameterDialog();

        if (params === null) {
            return; // User cancelled
        }

        const modeText = params.mode === 'full' ? 'Vollständiger Sync' : 'Quick Sync';
        showProgress(`Starte ${modeText}...`);

        // Find sync_inventory job
        const jobsRes = await fetch(`${API_BASE}/jobs`);
        const jobs = await jobsRes.json();
        const invJob = jobs.find(j => j.config?.job_type === 'sync_inventory');

        if (!invJob) {
            throw new Error('Inventory Sync Job nicht gefunden');
        }

        const res = await fetch(`${API_BASE}/jobs/${invJob.job_id}/run-now?mode=${params.mode}`, {
            method: 'POST'
        });

        const data = await res.json();
        updateProgress(100, 'Gestartet!');

        setTimeout(() => {
            hideProgress();
            if (data.status === 'triggered') {
                const modeText = params.mode === 'full' ? 'Vollständig (Steps 1-4)' : 'Quick Sync (Steps 3+4)';
                showToast(`Inventory Sync gestartet (${modeText})`, 'success');
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

// ═══════════════════════════════════════════════════════════
// Logs
// ═══════════════════════════════════════════════════════════

async function loadLogs() {
    try {
        const filter = document.getElementById('log-filter').value || 'temu';
        const url = `${API_BASE}/logs?job_id=${filter}&limit=200`;

        const res = await fetch(url);
        const logs = await res.json();

        const container = document.getElementById('logs-content');

        if (!logs || logs.length === 0) {
            container.textContent = 'Keine Logs verfügbar';
            return;
        }

        container.textContent = logs.map(log => {
            const time = new Date(log.timestamp).toLocaleString('de-DE');
            return `[${time}] [${log.job_type}] [${log.level}] ${log.message}`;
        }).join('\n');
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
// Toast Notifications
// ═══════════════════════════════════════════════════════════

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ═══════════════════════════════════════════════════════════
// Job Settings
// ═══════════════════════════════════════════════════════════

async function openIntervalDialog(jobId, currentInterval) {
    const newInterval = prompt(`Neues Intervall in Minuten (aktuell: ${currentInterval} Min):`, currentInterval);

    if (newInterval === null || newInterval === '') {
        return; // User cancelled
    }

    const interval = parseInt(newInterval);
    if (isNaN(interval) || interval < 1) {
        showToast('Ungültiges Intervall! Bitte eine Zahl >= 1 eingeben.', 'error');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/jobs/${jobId}/schedule?interval_minutes=${interval}`, {
            method: 'POST'
        });

        if (res.ok) {
            showToast(`Intervall geändert auf ${interval} Minuten`, 'success');
            loadJobs(); // Refresh job list
        } else {
            showToast('Fehler beim Ändern des Intervalls', 'error');
        }
    } catch (err) {
        console.error('Failed to update interval:', err);
        showToast(`Fehler: ${err.message}`, 'error');
    }
}

async function toggleJob(jobId, enabled) {
    try {
        const res = await fetch(`${API_BASE}/jobs/${jobId}/toggle?enabled=${enabled}`, {
            method: 'POST'
        });

        if (res.ok) {
            const action = enabled ? 'aktiviert' : 'deaktiviert';
            showToast(`Job ${action}`, 'success');
            loadJobs(); // Refresh job list
        } else {
            showToast('Fehler beim Ändern des Job-Status', 'error');
        }
    } catch (err) {
        console.error('Failed to toggle job:', err);
        showToast(`Fehler: ${err.message}`, 'error');
    }
}

// ═══════════════════════════════════════════════════════════
// Parameter Dialogs
// ═══════════════════════════════════════════════════════════

function showOrderSyncParameterDialog() {
    return new Promise((resolve) => {
        const dialog = document.createElement('div');
        dialog.className = 'modal active';
        dialog.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">⚙️ Order Sync Parameter</div>
                <div class="modal-body">
                    <div style="display: grid; gap: 15px;">
                        <div>
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">📊 Status:</label>
                            <select id="param-status" style="width: 100%; padding: 10px; background: var(--bg); border: 1px solid var(--border); color: var(--text); border-radius: 6px; font-size: 14px;">
                                <option value="2">2 - UN_SHIPPING (nicht versendet)</option>
                                <option value="3">3 - CANCELLED (storniert)</option>
                                <option value="4">4 - SHIPPED (versendet)</option>
                                <option value="5">5 - RECEIPTED (Order received)</option>
                            </select>
                        </div>

                        <div>
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">📅 Tage zurück:</label>
                            <input type="number" id="param-days" value="7" min="1" max="365"
                                   style="width: 100%; padding: 10px; background: var(--bg); border: 1px solid var(--border); color: var(--text); border-radius: 6px; font-size: 14px;">
                            <p style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">
                                Wie viele Tage in die Vergangenheit sollen Orders gesucht werden?
                            </p>
                        </div>

                        <div style="display: flex; gap: 15px;">
                            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                <input type="checkbox" id="param-verbose" style="width: 18px; height: 18px; cursor: pointer;">
                                <span>🔍 Verbose Mode</span>
                            </label>

                            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                <input type="checkbox" id="param-log-to-db" checked style="width: 18px; height: 18px; cursor: pointer;">
                                <span>💾 Log to Database</span>
                            </label>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" id="cancel-btn">Abbrechen</button>
                    <button class="btn btn-primary" id="submit-btn">▶️ Starten</button>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        document.getElementById('cancel-btn').onclick = () => {
            dialog.remove();
            resolve(null);
        };

        document.getElementById('submit-btn').onclick = () => {
            const params = {
                status: parseInt(document.getElementById('param-status').value),
                days: parseInt(document.getElementById('param-days').value),
                verbose: document.getElementById('param-verbose').checked,
                log_to_db: document.getElementById('param-log-to-db').checked
            };
            dialog.remove();
            resolve(params);
        };

        // Close on outside click
        dialog.onclick = (e) => {
            if (e.target === dialog) {
                dialog.remove();
                resolve(null);
            }
        };
    });
}

function showInventorySyncParameterDialog() {
    return new Promise((resolve) => {
        const dialog = document.createElement('div');
        dialog.className = 'modal active';
        dialog.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">⚙️ Inventory Sync Parameter</div>
                <div class="modal-body">
                    <div style="display: grid; gap: 15px;">
                        <div>
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">🔄 Sync-Modus:</label>
                            <select id="param-mode" style="width: 100%; padding: 10px; background: var(--bg); border: 1px solid var(--border); color: var(--text); border-radius: 6px; font-size: 14px;">
                                <option value="quick">Quick Sync (Steps 3+4) - Nur Bestandsabgleich</option>
                                <option value="full">Vollständig (Steps 1-4) - Inkl. SKU-Import</option>
                            </select>
                            <div style="margin-top: 12px; padding: 12px; background: var(--bg-secondary); border-radius: 6px; font-size: 13px; line-height: 1.6;">
                                <p style="margin: 0 0 8px 0; font-weight: 600; color: var(--primary);">Quick Sync (Empfohlen):</p>
                                <p style="margin: 0 0 12px 0; color: var(--text-secondary);">
                                    Aktualisiert nur JTL-Bestände und sendet Updates an TEMU. Schneller und für regelmäßige Synchronisation geeignet.
                                </p>
                                <p style="margin: 0 0 8px 0; font-weight: 600; color: var(--warning);">Vollständig:</p>
                                <p style="margin: 0; color: var(--text-secondary);">
                                    Lädt alle SKUs von TEMU, importiert sie in die Datenbank, dann Bestandsabgleich. Langsamer, nur nötig wenn neue SKUs hinzugekommen sind.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" id="cancel-btn">Abbrechen</button>
                    <button class="btn btn-success" id="submit-btn">▶️ Starten</button>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        document.getElementById('cancel-btn').onclick = () => {
            dialog.remove();
            resolve(null);
        };

        document.getElementById('submit-btn').onclick = () => {
            const params = {
                mode: document.getElementById('param-mode').value
            };
            dialog.remove();
            resolve(params);
        };

        // Close on outside click
        dialog.onclick = (e) => {
            if (e.target === dialog) {
                dialog.remove();
                resolve(null);
            }
        };
    });
}
