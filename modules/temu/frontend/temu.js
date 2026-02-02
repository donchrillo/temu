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
    const enabled = config.schedule?.enabled ? '✅' : '⏸️';
    const interval = config.schedule?.interval_minutes || 0;
    const lastRun = status.last_run ? new Date(status.last_run).toLocaleString('de-DE') : 'Nie';
    const nextRun = status.next_run ? new Date(status.next_run).toLocaleString('de-DE') : '-';
    const statusClass = status.status?.toLowerCase() || 'idle';

    return `
        <div class="job-item">
            <div class="job-info">
                <div class="job-name">${enabled} ${jobType}</div>
                <div class="job-meta">
                    ${description}<br>
                    Intervall: ${interval}min | Letzter Lauf: ${lastRun} | Nächster Lauf: ${nextRun}
                </div>
            </div>
            <div>
                <span class="job-status ${statusClass}">${status.status || 'IDLE'}</span>
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
        showProgress('Starte Order Sync Workflow...');

        // Find sync_orders job
        const jobsRes = await fetch(`${API_BASE}/jobs`);
        const jobs = await jobsRes.json();
        const orderJob = jobs.find(j => j.config?.job_type === 'sync_orders');

        if (!orderJob) {
            throw new Error('Order Sync Job nicht gefunden');
        }

        const res = await fetch(`${API_BASE}/jobs/${orderJob.job_id}/run-now`, {
            method: 'POST'
        });

        const data = await res.json();
        updateProgress(100, 'Gestartet!');

        setTimeout(() => {
            hideProgress();
            if (data.status === 'triggered') {
                showToast('Order Sync Workflow gestartet', 'success');
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
        showProgress('Starte Inventory Sync Workflow...');

        // Find sync_inventory job
        const jobsRes = await fetch(`${API_BASE}/jobs`);
        const jobs = await jobsRes.json();
        const invJob = jobs.find(j => j.config?.job_type === 'sync_inventory');

        if (!invJob) {
            throw new Error('Inventory Sync Job nicht gefunden');
        }

        const res = await fetch(`${API_BASE}/jobs/${invJob.job_id}/run-now?mode=quick`, {
            method: 'POST'
        });

        const data = await res.json();
        updateProgress(100, 'Gestartet!');

        setTimeout(() => {
            hideProgress();
            if (data.status === 'triggered') {
                showToast('Inventory Sync Workflow gestartet', 'success');
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
        const filter = document.getElementById('log-filter').value;
        const url = filter
            ? `${API_BASE}/logs?job_id=${filter}&limit=50`
            : `${API_BASE}/logs?limit=50`;

        const res = await fetch(url);
        const logs = await res.json();

        const container = document.getElementById('logs-content');

        if (!logs || logs.length === 0) {
            container.textContent = 'Keine Logs verfügbar';
            return;
        }

        container.textContent = logs.map(log => {
            const time = new Date(log.timestamp).toLocaleString('de-DE');
            return `[${time}] [${log.level}] ${log.message}`;
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
