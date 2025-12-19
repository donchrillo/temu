// ===== KONFIGURATION =====
const HOST = window.location.hostname === 'localhost' 
    ? 'localhost' 
    : window.location.hostname;
const PORT = window.location.port || '8000';

const API_URL = `http://${HOST}:${PORT}/api`;
const WS_URL = `ws://${HOST}:${PORT}/ws/logs`;

console.log("🔗 API URL:", API_URL);
console.log("🔗 WS URL:", WS_URL);

let ws = null;
let jobs = [];
let allLogs = [];
let selectedJobId = null;
let wsReconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

// ===== TAB MANAGEMENT =====
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(el => {
        el.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    event.target.classList.add('active');
    
    // Load data für Tab
    if (tabName === 'logs') {
        loadAllLogs();
    } else if (tabName === 'stats') {
        loadStatistics();
    }
}

// ===== DEBUG INFO =====
function showDebugInfo(message) {
    const debugEl = document.getElementById("debug-info");
    if (debugEl) {
        debugEl.textContent = message;
    }
    console.log(message);
}

// ===== API HEALTH CHECK =====
async function testApiHealth() {
    try {
        showDebugInfo("🔍 Teste API-Verbindung...");
        const response = await fetch(`${API_URL}/health`);
        if (response.ok) {
            showDebugInfo("✓ API erreichbar!");
            return true;
        } else {
            showDebugInfo(`✗ API Status ${response.status}`);
            return false;
        }
    } catch (e) {
        showDebugInfo(`✗ API nicht erreichbar: ${e.message}`);
        return false;
    }
}

// ===== WEBSOCKET =====
function connectWebSocket() {
    console.log("📡 Verbinde WebSocket...");
    ws = new WebSocket(WS_URL);
    
    ws.onopen = () => {
        console.log("✓ WebSocket verbunden");
        showDebugInfo("✓ WebSocket verbunden!");
        document.getElementById("status").textContent = "Online";
        wsReconnectAttempts = 0;
    };
    
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === "jobs_update") {
                jobs = data.data;
                console.log(`📋 ${jobs.length} Jobs geladen`);
                renderJobs();
                updateJobFilter();
            }
        } catch (e) {
            console.error("❌ JSON Parse Error:", e);
        }
    };
    
    ws.onerror = () => {
        console.error("❌ WebSocket Fehler");
        document.getElementById("status").textContent = "Fehler";
    };
    
    ws.onclose = () => {
        console.warn("⚠ WebSocket geschlossen");
        document.getElementById("status").textContent = "Offline";
        
        wsReconnectAttempts++;
        if (wsReconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            const delay = Math.min(3000 * wsReconnectAttempts, 10000);
            setTimeout(connectWebSocket, delay);
        }
    };
}

// ===== LOGS LADEN =====
async function loadAllLogs() {
    try {
        const jobId = document.getElementById('filter-job').value || '';
        const level = document.getElementById('filter-level').value || '';
        const limit = document.getElementById('filter-limit').value || 100;
        
        let url = `${API_URL}/logs?limit=${limit}`;
        if (jobId) url += `&job_id=${jobId}`;
        if (level) url += `&level=${level}`;
        
        console.log("📥 Lade Logs mit URL:", url);
        
        const response = await fetch(url);
        if (response.ok) {
            allLogs = await response.json();
            console.log(`📋 ${allLogs.length} Logs geladen`);
            renderLogs(allLogs);
        } else {
            console.error("❌ API Error:", response.status);
        }
    } catch (e) {
        console.error("❌ Logs laden fehlgeschlagen:", e);
    }
}

// ===== ERROR LOGS LADEN =====
async function loadErrorLogs() {
    try {
        const level = document.getElementById('filter-error-level').value || '';
        const days = document.getElementById('filter-error-days').value || '7';
        const limit = document.getElementById('filter-error-limit').value || 100;
        
        let url = `${API_URL}/logs/errors?limit=${limit}&days=${days}`;
        if (level) url += `&level=${level}`;
        
        console.log("📥 Lade Error-Logs mit URL:", url);
        
        const response = await fetch(url);
        if (response.ok) {
            const data = await response.json();
            console.log(`📋 ${data.data.length} Error-Logs geladen`);
            renderErrorLogs(data.data);
        } else {
            console.error("❌ API Error:", response.status);
        }
    } catch (e) {
        console.error("❌ Error-Logs laden fehlgeschlagen:", e);
    }
}

// ===== LOG FILTER & SUCHE =====
function updateJobFilter() {
    const select = document.getElementById('filter-job');
    const currentValue = select.value;
    
    // Sammle alle Job-IDs
    const jobIds = [...new Set(jobs.map(j => j.job_id))];
    
    // Behalte "Alle Jobs" Option
    select.innerHTML = '<option value="">— Alle Jobs —</option>';
    jobIds.forEach(id => {
        const opt = document.createElement('option');
        opt.value = id;
        opt.textContent = jobs.find(j => j.job_id === id)?.config.description || id;
        select.appendChild(opt);
    });
    
    select.value = currentValue;
}

function applyLogFilters() {
    loadAllLogs();
}

function clearLogFilter() {
    document.getElementById('filter-job').value = '';
    document.getElementById('filter-level').value = '';
    document.getElementById('filter-search').value = '';
    loadAllLogs();
}

// ===== ERROR LOG FILTER & SUCHE =====
function clearErrorFilter() {
    document.getElementById('filter-error-level').value = '';
    document.getElementById('filter-error-days').value = '7';
    document.getElementById('filter-error-limit').value = '100';
    loadErrorLogs();
}

// ===== LOG RENDERING =====
function renderLogs(logs) {
    const container = document.getElementById('logs-container');
    
    const searchText = document.getElementById('filter-search').value.toLowerCase();
    
    let filteredLogs = logs;
    if (searchText) {
        filteredLogs = logs.filter(log => 
            (log.message || '').toLowerCase().includes(searchText) ||
            (log.job_id && log.job_id.toLowerCase().includes(searchText))
        );
    }

    // Sicherstellen: neueste zuerst (stabile Sortierung mit Tie-Breaker)
    filteredLogs = [...filteredLogs].sort((a, b) => {
        const ta = a.timestamp ? new Date(a.timestamp).getTime() : 0;
        const tb = b.timestamp ? new Date(b.timestamp).getTime() : 0;
        if (tb !== ta) return tb - ta;
        const ida = typeof a.log_id === 'number' ? a.log_id : (parseInt(a.id || 0, 10) || 0);
        const idb = typeof b.log_id === 'number' ? b.log_id : (parseInt(b.id || 0, 10) || 0);
        return idb - ida;
    });
    
    if (!filteredLogs || filteredLogs.length === 0) {
        container.innerHTML = '<div class="log-line">Keine Logs vorhanden</div>';
        return;
    }
    
    container.innerHTML = filteredLogs
        .map(log => {
            let className = 'log-line';
            if (log.level === 'ERROR') {
                className = 'log-line log-error';
            } else if (log.level === 'WARNING') {
                className = 'log-line log-warning';
            } else if (log.level === 'DEBUG') {
                className = 'log-line';
            } else {
                className = 'log-line log-info';
            }
            
            const timestamp = log.timestamp ? new Date(log.timestamp).toLocaleTimeString('de-DE') : '';
            
            return `
                <div class="${className}">
                    <strong>[${timestamp}]</strong> 
                    <span style="color: #94a3b8;">[${log.level}]</span>
                    ${escapeHtml(log.message || '')}
                </div>
            `;
        })
        .join('');
    
    container.scrollTop = 0;
}


// ===== STATISTIKEN =====
async function loadStatistics() {
    try {
        const jobId = document.getElementById('filter-job').value || '';
        let url = `${API_URL}/logs/stats`;
        if (jobId) url += `?job_id=${jobId}`;
        
        const response = await fetch(url);
        if (response.ok) {
            const stats = await response.json();
            renderStatistics(stats);
        }
    } catch (e) {
        console.error("❌ Stats laden fehlgeschlagen:", e);
    }
}

function renderStatistics(stats) {
    document.getElementById('stat-total').textContent = stats.total_runs || 0;
    document.getElementById('stat-success').textContent = stats.successful_runs || 0;
    document.getElementById('stat-failed').textContent = stats.failed_runs || 0;
    document.getElementById('stat-success-rate').textContent = (stats.success_rate || 0).toFixed(1) + '%';
    document.getElementById('stat-avg-duration').textContent = (stats.avg_duration || 0).toFixed(2) + 's';
    document.getElementById('stat-max-duration').textContent = (stats.max_duration || 0).toFixed(2) + 's';
    
    // Update Erfolgsrate im Header
    document.getElementById('success-rate').textContent = (stats.success_rate || 0).toFixed(0) + '%';
}

// ===== EXPORT =====
async function exportLogs(format) {
    try {
        const jobId = document.getElementById('filter-job').value || '';
        let url = `${API_URL}/logs/export?format=${format}`;
        if (jobId) url += `&job_id=${jobId}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        const filename = `temu_logs_${new Date().toISOString().split('T')[0]}.${format}`;
        const blob = new Blob([data.data], { type: 'text/plain' });
        const url_link = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url_link;
        a.download = filename;
        a.click();
        
        alert(`✓ Logs exportiert: ${filename}`);
    } catch (e) {
        console.error("❌ Export fehlgeschlagen:", e);
        alert("✗ Fehler beim Export");
    }
}

// ===== JOB RENDERING =====
function renderJobs() {
    const grid = document.getElementById('jobs-grid');
    grid.innerHTML = "";
    
    jobs.forEach(job => {
        const card = document.createElement("div");
        card.className = "job-card";
        
        const lastRun = job.status.last_run 
            ? new Date(job.status.last_run).toLocaleString("de-DE")
            : "Noch nie";
        
        const nextRun = job.status.next_run 
            ? new Date(job.status.next_run).toLocaleString("de-DE")
            : "—";
        
        const statusClass = `status-${job.status.status.toLowerCase()}`;
        
        const lastDuration = job.status.last_duration 
            ? `<div class="info-row">
                <span class="info-label">Dauer:</span>
                <span class="info-value">${job.status.last_duration.toFixed(2)}s</span>
            </div>`
            : "";
        
        const lastError = job.status.last_error 
            ? `<div class="info-row" style="background: #7f1d1d;">
                <span class="info-label">Fehler:</span>
                <span class="info-value">${escapeHtml(job.status.last_error.substring(0, 50))}</span>
            </div>`
            : "";
        
        card.innerHTML = `
            <div class="job-header">
                <div>
                    <div class="job-title">${job.config.description}</div>
                    <div style="font-size: 12px; color: #94a3b8; margin-top: 5px;">${job.config.job_type}</div>
                </div>
                <div class="job-status ${statusClass}">${job.status.status}</div>
            </div>
            
            <div class="job-info">
                <div class="info-row">
                    <span class="info-label">Intervall:</span>
                    <span class="info-value">${job.config.schedule.interval_minutes} Min</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Letzte Ausführung:</span>
                    <span class="info-value">${lastRun}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Nächste Ausführung:</span>
                    <span class="info-value">${nextRun}</span>
                </div>
                ${lastDuration}
                ${lastError}
            </div>
            
            <div class="job-controls">
                <button class="btn-primary" onclick="triggerJob('${job.job_id}')">Ausführen</button>
                <button class="btn-secondary" onclick="switchToJobLogs('${job.job_id}')">📋 Logs</button>
                <button class="btn-secondary" onclick="openIntervalDialog('${job.job_id}', ${job.config.schedule.interval_minutes})">⏱️</button>
                <button class="btn-${job.config.schedule.enabled ? 'success' : 'danger'}" onclick="toggleJob('${job.job_id}', ${!job.config.schedule.enabled})">${job.config.schedule.enabled ? '✓' : '✗'}</button>
            </div>
        `;
        
        grid.appendChild(card);
    });
    
    document.getElementById("active-jobs").textContent = jobs.length;
}

// ===== JOB CONTROL FUNKTIONEN =====
async function triggerJob(jobId) {
    // Prüfe Job-Typ
    const job = jobs.find(j => j.job_id === jobId);
    if (!job) return;
    
    let params;
    if (job.config.job_type === 'sync_inventory') {
        params = await showInventoryParameterDialog();
    } else {
        params = await showJobParameterDialog();
    }
    
    if (params === null) return;
    
    try {
        const url = `${API_URL}/jobs/${jobId}/run-now?` +
            `parent_order_status=${params.status || 2}&` +
            `days_back=${params.days || 7}&` +
            `verbose=${params.verbose || false}&` +
            `log_to_db=${params.log_to_db !== false}&` +
            `mode=${params.mode || 'quick'}`;
        
        const response = await fetch(url, { method: "POST" });
        const data = await response.json();
        
        if (job.config.job_type === 'sync_inventory') {
            alert(`✓ Inventur Job gestartet\nModus: ${params.mode === 'full' ? 'Vollständig (4 Steps)' : 'Quick Sync (Steps 3+4)'}`);
        } else {
            alert(`✓ Job gestartet mit Parametern:\n` +
                  `Status: ${params.status}\n` +
                  `Tage: ${params.days}\n` +
                  `Verbose: ${params.verbose ? 'Ja' : 'Nein'}\n` +
                  `Log-to-DB: ${params.log_to_db ? 'Ja' : 'Nein'}`);
        }
    } catch (e) {
        console.error("✗ Fehler:", e);
        alert("✗ Fehler beim Starten");
    }
}

async function showInventoryParameterDialog() {
    return new Promise((resolve) => {
        const html = `
            <div style="display: grid; gap: 15px;">
                <div>
                    <label style="display: block; margin-bottom: 5px;">🔄 Sync-Modus:</label>
                    <select id="dialog-inventory-mode" style="width: 100%; padding: 8px; background: #1e293b; border: 1px solid #334155; color: #e2e8f0; border-radius: 4px;">
                        <option value="quick">Quick Sync (Steps 3+4) - Nur Bestandsabgleich</option>
                        <option value="full">Vollständig (Steps 1-4) - Inkl. SKU-Import</option>
                    </select>
                    <p style="font-size: 12px; color: #94a3b8; margin-top: 8px;">
                        <strong>Quick Sync:</strong> Aktualisiert nur JTL-Bestände und sendet an TEMU (schnell)<br>
                        <strong>Vollständig:</strong> Lädt SKUs von TEMU, importiert in DB, dann Bestandsabgleich (langsam)
                    </p>
                </div>
            </div>
        `;
        
        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">⚙️ Inventur Sync Parameter</div>
                <div class="modal-body">${html}</div>
                <div class="modal-footer">
                    <button class="btn-secondary" onclick="this.closest('.modal').remove(); 
                        window.__inventoryParamResolve(null)">Abbrechen</button>
                    <button class="btn-primary" onclick="
                        const params = {
                            mode: document.getElementById('dialog-inventory-mode').value,
                            status: 2,
                            days: 7,
                            verbose: false,
                            log_to_db: true
                        };
                        this.closest('.modal').remove();
                        window.__inventoryParamResolve(params);
                    ">Starten</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        window.__inventoryParamResolve = resolve;
    });
}

async function showJobParameterDialog() {
    return new Promise((resolve) => {
        const html = `
            <div style="display: grid; gap: 15px;">
                <div>
                    <label style="display: block; margin-bottom: 5px;">📊 Status:</label>
                    <select id="dialog-status" style="width: 100%; padding: 8px;">
                        <option value="2">2 - UN_SHIPPING (nicht versendet)</option>
                        <option value="3">3 - CANCELLED (storniert)</option>
                        <option value="4">4 - SHIPPED (versendet)</option>
                        <option value="5">5 - RECEIPTED (Order received)</option>
                    </select>
                </div>
                
                <div>
                    <label style="display: block; margin-bottom: 5px;">📅 Tage zurück:</label>
                    <input type="number" id="dialog-days" value="7" min="1" max="365" 
                           style="width: 100%; padding: 8px;">
                </div>
                
                <div style="display: flex; gap: 10px;">
                    <label style="display: flex; align-items: center; gap: 8px;">
                        <input type="checkbox" id="dialog-verbose">
                        🔍 Verbose Mode
                    </label>
                </div>
                
                <div style="display: flex; gap: 10px;">
                    <label style="display: flex; align-items: center; gap: 8px;">
                        <input type="checkbox" id="dialog-log-to-db" checked>
                        💾 Log to Database
                    </label>
                </div>
            </div>
        `;
        
        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">⚙️ Job Parameter</div>
                <div class="modal-body">${html}</div>
                <div class="modal-footer">
                    <button class="btn-secondary" onclick="this.closest('.modal').remove(); 
                        window.__jobParamResolve(null)">Abbrechen</button>
                    <button class="btn-primary" onclick="
                        const params = {
                            status: parseInt(document.getElementById('dialog-status').value),
                            days: parseInt(document.getElementById('dialog-days').value),
                            verbose: document.getElementById('dialog-verbose').checked,
                            log_to_db: document.getElementById('dialog-log-to-db').checked
                        };
                        this.closest('.modal').remove();
                        window.__jobParamResolve(params);
                    ">Starten</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        window.__jobParamResolve = resolve;
    });
}

function switchToJobLogs(jobId) {
    document.getElementById('filter-job').value = jobId;
    switchTab('logs');
    loadAllLogs();
}

async function openIntervalDialog(jobId, currentInterval) {
    const newInterval = prompt(`Neues Intervall in Minuten (aktuell: ${currentInterval} Min):`, currentInterval);
    if (newInterval && !isNaN(newInterval)) {
        try {
            await fetch(`${API_URL}/jobs/${jobId}/schedule?interval_minutes=${newInterval}`, { method: "POST" });
            alert(`✓ Intervall geändert auf ${newInterval} Minuten`);
        } catch (e) {
            alert("✗ Fehler beim Ändern");
        }
    }
}

async function toggleJob(jobId, enabled) {
    try {
        await fetch(`${API_URL}/jobs/${jobId}/toggle?enabled=${enabled}`, { method: "POST" });
        console.log(`✓ Job ${enabled ? 'aktiviert' : 'deaktiviert'}`);
    } catch (e) {
        alert("✗ Fehler beim Toggle");
    }
}

// ===== UTILITY FUNKTIONEN =====
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function closeModal() {
    document.getElementById('log-modal').classList.remove('active');
}

// ===== APP INIT =====
async function init() {
    const apiOk = await testApiHealth();
    if (apiOk) {
        connectWebSocket();
    } else {
        showDebugInfo("⚠ API nicht verfügbar, versuche trotzdem WebSocket...");
        connectWebSocket();
    }
}

// Start
init();
