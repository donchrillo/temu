// ═══════════════════════════════════════════════════════════
// PDF Processor - JavaScript
// ═══════════════════════════════════════════════════════════

// ═══ Constants ═══

const PDF_CONFIG = {
    ENDPOINTS: {
        STATUS: '/api/pdf/status',
        WERBUNG: '/api/pdf/werbung',
        RECHNUNGEN: '/api/pdf/rechnungen',
        CLEANUP: '/api/pdf/cleanup',
        LOGS: '/api/logs'
    },
    SELECTORS: {
        STATUS_INFO: 'status-info',
        LOG_CONTENT: 'log-content',
        LOG_FILTER: 'log-filter'
    }
};

// ═══ File State (Map statt separate Arrays) ═══

const fileState = {
    werbung: [],
    rechnungen: []
};

// ═══════════════════════════════════════════════════════════
// Initialization
// ═══════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initUploadZones();
    loadStatus();
    showLog(); // Initial logs
});

// ═══════════════════════════════════════════════════════════
// Tabs
// ═══════════════════════════════════════════════════════════

function initTabs() {
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            switchTab(tab);
        });
    });
}

function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `tab-${tabName}`);
    });
}

// ═══════════════════════════════════════════════════════════
// Upload Zones (Drag & Drop)
// ═══════════════════════════════════════════════════════════

function initUploadZones() {
    setupUploadZone('werbung');
    setupUploadZone('rechnungen');
}

function setupUploadZone(type) {
    const dropzone = document.getElementById(`${type}-dropzone`);
    const input = document.getElementById(`${type}-input`);

    // Click to select files
    dropzone.addEventListener('click', () => input.click());

    // File selection
    input.addEventListener('change', (e) => {
        handleFiles(type, Array.from(e.target.files));
    });

    // Drag & Drop
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        const files = Array.from(e.dataTransfer.files).filter(f => f.type === 'application/pdf');
        handleFiles(type, files);
    });
}

function handleFiles(type, files) {
    fileState[type] = fileState[type].concat(files);
    renderFileList(type);
}

/**
 * Render file list with DOM creation (XSS-safe, no innerHTML with user data)
 */
function renderFileList(type) {
    const container = document.getElementById(`${type}-files`);
    container.innerHTML = '';

    const fragment = document.createDocumentFragment();
    fileState[type].forEach((file, index) => {
        fragment.appendChild(createFileItem(file, type, index));
    });
    container.appendChild(fragment);
}

function createFileItem(file, type, index) {
    const div = document.createElement('div');
    div.className = 'file-item';

    const span = document.createElement('span');
    span.textContent = `📄 ${file.name} (${formatFileSize(file.size)})`; // XSS-safe

    const btn = document.createElement('button');
    btn.className = 'file-remove';
    btn.textContent = '✕';
    btn.addEventListener('click', () => removeFile(type, index));

    div.appendChild(span);
    div.appendChild(btn);
    return div;
}

function removeFile(type, index) {
    fileState[type].splice(index, 1);
    renderFileList(type);
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ═══════════════════════════════════════════════════════════
// Status
// ═══════════════════════════════════════════════════════════

async function loadStatus() {
    try {
        const res = await fetch(PDF_CONFIG.ENDPOINTS.STATUS);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        const statusEl = document.getElementById(PDF_CONFIG.SELECTORS.STATUS_INFO);
        statusEl.innerHTML = '';

        const grid = document.createElement('div');
        grid.className = 'status-info-grid';

        const items = [
            { label: 'Werbung', value: `${data.werbung.count} Dateien` },
            { label: 'Rechnungen', value: `${data.rechnungen.count} Dateien` },
            { label: 'TMP', value: `${data.tmp.count} Dateien` }
        ];

        items.forEach(({ label, value }) => {
            const div = document.createElement('div');
            const strong = document.createElement('strong');
            strong.textContent = `${label}: `;
            div.appendChild(strong);
            div.appendChild(document.createTextNode(value));
            grid.appendChild(div);
        });

        statusEl.appendChild(grid);
    } catch (err) {
        console.error('Status laden fehlgeschlagen:', err);
    }
}

// ═══════════════════════════════════════════════════════════
// Generic Action Helper (DRY für alle API-Aufrufe)
// ═══════════════════════════════════════════════════════════

/**
 * Führt eine API-Aktion mit Progress-Overlay und Toast-Feedback aus
 * @param {Object} opts
 * @param {string} opts.progressText - Text im Progress-Overlay
 * @param {string} opts.url - API endpoint
 * @param {string} [opts.method='POST'] - HTTP method
 * @param {FormData|null} [opts.body=null] - Request body
 * @param {Function} opts.onSuccess - Callback bei data.status === 'ok'
 * @param {string} opts.failureText - Toast-Text bei Fehler
 */
async function performAction({ progressText, url, method = 'POST', body = null, onSuccess, failureText }) {
    try {
        showProgress(progressText);

        const options = { method };
        if (body) options.body = body;

        const res = await fetch(url, options);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        updateProgress(100, 'Fertig!');

        setTimeout(() => {
            hideProgress();
            if (data.status === 'ok') {
                onSuccess(data);
                showLog();
            } else {
                showToast(failureText, 'error');
            }
        }, 500);
    } catch (err) {
        hideProgress();
        showToast(`Fehler: ${err.message}`, 'error');
    }
}

// ═══════════════════════════════════════════════════════════
// Werbung Actions
// ═══════════════════════════════════════════════════════════

async function uploadWerbung() {
    if (fileState.werbung.length === 0) {
        showToast('Bitte wähle Dateien aus', 'error');
        return;
    }

    const formData = new FormData();
    fileState.werbung.forEach(file => formData.append('files', file));

    await performAction({
        progressText: `Lade ${fileState.werbung.length} Dateien hoch...`,
        url: `${PDF_CONFIG.ENDPOINTS.WERBUNG}/upload`,
        body: formData,
        failureText: 'Upload fehlgeschlagen',
        onSuccess: (data) => {
            showToast(`${data.saved.length} Dateien hochgeladen`, 'success');
            fileState.werbung = [];
            renderFileList('werbung');
            loadStatus();
        }
    });
}

async function extractWerbung() {
    await performAction({
        progressText: 'Extrahiere erste Seiten...',
        url: `${PDF_CONFIG.ENDPOINTS.WERBUNG}/extract`,
        failureText: 'Extraktion fehlgeschlagen',
        onSuccess: (data) => {
            showToast(`${data.extracted.length} Seiten extrahiert`, 'success');
            loadStatus();
        }
    });
}

async function processWerbung() {
    await performAction({
        progressText: 'Verarbeite PDFs...',
        url: `${PDF_CONFIG.ENDPOINTS.WERBUNG}/process`,
        failureText: 'Verarbeitung fehlgeschlagen',
        onSuccess: (data) => {
            showToast(`${data.count} Einträge verarbeitet`, 'success');
        }
    });
}

function downloadWerbung() {
    window.location.href = `${PDF_CONFIG.ENDPOINTS.WERBUNG}/result`;
}

// ═══════════════════════════════════════════════════════════
// Rechnungen Actions
// ═══════════════════════════════════════════════════════════

async function uploadRechnungen() {
    if (fileState.rechnungen.length === 0) {
        showToast('Bitte wähle Dateien aus', 'error');
        return;
    }

    const formData = new FormData();
    fileState.rechnungen.forEach(file => formData.append('files', file));

    await performAction({
        progressText: `Lade ${fileState.rechnungen.length} Dateien hoch...`,
        url: `${PDF_CONFIG.ENDPOINTS.RECHNUNGEN}/upload`,
        body: formData,
        failureText: 'Upload fehlgeschlagen',
        onSuccess: (data) => {
            showToast(`${data.saved.length} Dateien hochgeladen`, 'success');
            fileState.rechnungen = [];
            renderFileList('rechnungen');
            loadStatus();
        }
    });
}

async function processRechnungen() {
    await performAction({
        progressText: 'Verarbeite Rechnungen...',
        url: `${PDF_CONFIG.ENDPOINTS.RECHNUNGEN}/process`,
        failureText: 'Verarbeitung fehlgeschlagen',
        onSuccess: (data) => {
            showToast(`${data.count} Einträge verarbeitet`, 'success');
        }
    });
}

function downloadRechnungen() {
    window.location.href = `${PDF_CONFIG.ENDPOINTS.RECHNUNGEN}/result`;
}

// ═══════════════════════════════════════════════════════════
// Logs
// ═══════════════════════════════════════════════════════════

async function showLog() {
    const logContent = document.getElementById(PDF_CONFIG.SELECTORS.LOG_CONTENT);
    
    try {
        const filter = document.getElementById(PDF_CONFIG.SELECTORS.LOG_FILTER).value || 'pdf';
        const res = await fetch(`${PDF_CONFIG.ENDPOINTS.LOGS}?job_id=${filter}&limit=100`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const logs = await res.json();

        if (logs && logs.length > 0) {
            logContent.textContent = logs.map(formatLogEntry).join('\n');
        } else {
            logContent.textContent = 'Keine Logs gefunden.';
        }
    } catch (err) {
        logContent.textContent = `Fehler beim Laden der Logs: ${err.message}`;
    }
}

// ═══════════════════════════════════════════════════════════
// Cleanup
// ═══════════════════════════════════════════════════════════

async function cleanup() {
    if (!confirm('Wirklich ALLE Dateien löschen? Diese Aktion kann nicht rückgängig gemacht werden!')) {
        return;
    }

    await performAction({
        progressText: 'Räume auf...',
        url: PDF_CONFIG.ENDPOINTS.CLEANUP,
        failureText: 'Cleanup fehlgeschlagen',
        onSuccess: (data) => {
            const total = Object.values(data.cleared).reduce((sum, val) => sum + val, 0);
            showToast(`${total} Dateien gelöscht`, 'success');
            loadStatus();
        }
    });
}

// Progress Bar + Toast + formatLogEntry aus shared components:
// /components/progress-helper.js, /components/ui-helpers.js
