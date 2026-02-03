// ═══════════════════════════════════════════════════════════
// PDF Processor - JavaScript
// ═══════════════════════════════════════════════════════════

// API Base URL
const API_BASE = '/api/pdf';

// State
let werbungFiles = [];
let rechnungenFiles = [];

// ═══════════════════════════════════════════════════════════
// Initialization
// ═══════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initUploadZones();
    loadStatus();
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
    if (type === 'werbung') {
        werbungFiles = werbungFiles.concat(files);
        renderFileList('werbung', werbungFiles);
    } else {
        rechnungenFiles = rechnungenFiles.concat(files);
        renderFileList('rechnungen', rechnungenFiles);
    }
}

function renderFileList(type, files) {
    const container = document.getElementById(`${type}-files`);
    container.innerHTML = files.map((file, index) => `
        <div class="file-item">
            <span>📄 ${file.name} (${formatFileSize(file.size)})</span>
            <button class="file-remove" onclick="removeFile('${type}', ${index})">✕</button>
        </div>
    `).join('');
}

function removeFile(type, index) {
    if (type === 'werbung') {
        werbungFiles.splice(index, 1);
        renderFileList('werbung', werbungFiles);
    } else {
        rechnungenFiles.splice(index, 1);
        renderFileList('rechnungen', rechnungenFiles);
    }
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
        const res = await fetch(`${API_BASE}/status`);
        const data = await res.json();

        const html = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-top: 12px;">
                <div>
                    <strong>Werbung:</strong> ${data.werbung.count} Dateien
                </div>
                <div>
                    <strong>Rechnungen:</strong> ${data.rechnungen.count} Dateien
                </div>
                <div>
                    <strong>TMP:</strong> ${data.tmp.count} Dateien
                </div>
            </div>
        `;
        document.getElementById('status-info').innerHTML = html;
    } catch (err) {
        console.error('Status laden fehlgeschlagen:', err);
    }
}

// ═══════════════════════════════════════════════════════════
// Werbung Actions
// ═══════════════════════════════════════════════════════════

async function uploadWerbung() {
    if (werbungFiles.length === 0) {
        showToast('Bitte wähle Dateien aus', 'error');
        return;
    }

    const formData = new FormData();
    werbungFiles.forEach(file => formData.append('files', file));

    try {
        showProgress(`Lade ${werbungFiles.length} Dateien hoch...`);

        const res = await fetch(`${API_BASE}/werbung/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await res.json();
        updateProgress(100, 'Fertig!');

        setTimeout(() => {
            hideProgress();
            if (data.status === 'ok') {
                showToast(`${data.saved.length} Dateien hochgeladen`, 'success');
                werbungFiles = [];
                renderFileList('werbung', []);
                loadStatus();
            } else {
                showToast('Upload fehlgeschlagen', 'error');
            }
        }, 500);
    } catch (err) {
        hideProgress();
        showToast(`Fehler: ${err.message}`, 'error');
    }
}

async function extractWerbung() {
    try {
        showProgress('Extrahiere erste Seiten...');

        const res = await fetch(`${API_BASE}/werbung/extract`, { method: 'POST' });
        const data = await res.json();
        updateProgress(100, 'Fertig!');

        setTimeout(() => {
            hideProgress();
            if (data.status === 'ok') {
                showToast(`${data.extracted.length} Seiten extrahiert`, 'success');
                loadStatus();
            } else {
                showToast('Extraktion fehlgeschlagen', 'error');
            }
        }, 500);
    } catch (err) {
        hideProgress();
        showToast(`Fehler: ${err.message}`, 'error');
    }
}

async function processWerbung() {
    try {
        showProgress('Verarbeite PDFs...');

        const res = await fetch(`${API_BASE}/werbung/process`, { method: 'POST' });
        const data = await res.json();
        updateProgress(100, 'Fertig!');

        setTimeout(() => {
            hideProgress();
            if (data.status === 'ok') {
                showToast(`${data.count} Einträge verarbeitet`, 'success');
            } else {
                showToast('Verarbeitung fehlgeschlagen', 'error');
            }
        }, 500);
    } catch (err) {
        hideProgress();
        showToast(`Fehler: ${err.message}`, 'error');
    }
}

function downloadWerbung() {
    window.location.href = `${API_BASE}/werbung/result`;
}

// ═══════════════════════════════════════════════════════════
// Rechnungen Actions
// ═══════════════════════════════════════════════════════════

async function uploadRechnungen() {
    if (rechnungenFiles.length === 0) {
        showToast('Bitte wähle Dateien aus', 'error');
        return;
    }

    const formData = new FormData();
    rechnungenFiles.forEach(file => formData.append('files', file));

    try {
        showProgress(`Lade ${rechnungenFiles.length} Dateien hoch...`);

        const res = await fetch(`${API_BASE}/rechnungen/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await res.json();
        updateProgress(100, 'Fertig!');

        setTimeout(() => {
            hideProgress();
            if (data.status === 'ok') {
                showToast(`${data.saved.length} Dateien hochgeladen`, 'success');
                rechnungenFiles = [];
                renderFileList('rechnungen', []);
                loadStatus();
            } else {
                showToast('Upload fehlgeschlagen', 'error');
            }
        }, 500);
    } catch (err) {
        hideProgress();
        showToast(`Fehler: ${err.message}`, 'error');
    }
}

async function processRechnungen() {
    try {
        showProgress('Verarbeite Rechnungen...');

        const res = await fetch(`${API_BASE}/rechnungen/process`, { method: 'POST' });
        const data = await res.json();
        updateProgress(100, 'Fertig!');

        setTimeout(() => {
            hideProgress();
            if (data.status === 'ok') {
                showToast(`${data.count} Einträge verarbeitet`, 'success');
            } else {
                showToast('Verarbeitung fehlgeschlagen', 'error');
            }
        }, 500);
    } catch (err) {
        hideProgress();
        showToast(`Fehler: ${err.message}`, 'error');
    }
}

function downloadRechnungen() {
    window.location.href = `${API_BASE}/rechnungen/result`;
}

// ═══════════════════════════════════════════════════════════
// Logs
// ═══════════════════════════════════════════════════════════

async function showLog(type) {
    const logfile = `${type}.log`;
    try {
        const res = await fetch(`${API_BASE}/logs/${logfile}`);
        const data = await res.json();

        document.getElementById('log-content').textContent =
            data.status === 'ok' ? data.content : 'Keine Logs verfügbar';

        // Update active tab
        document.querySelectorAll('.log-tab').forEach(tab => {
            tab.classList.toggle('active', tab.textContent.includes(type.replace('_', ' ')));
        });
    } catch (err) {
        document.getElementById('log-content').textContent = `Fehler: ${err.message}`;
    }
}

// Load initial log
setTimeout(() => showLog('werbung_read'), 1000);

// ═══════════════════════════════════════════════════════════
// Cleanup
// ═══════════════════════════════════════════════════════════

async function cleanup() {
    if (!confirm('Wirklich ALLE Dateien löschen? Diese Aktion kann nicht rückgängig gemacht werden!')) {
        return;
    }

    try {
        showProgress('Räume auf...');

        const res = await fetch(`${API_BASE}/cleanup`, { method: 'POST' });
        const data = await res.json();
        updateProgress(100, 'Fertig!');

        setTimeout(() => {
            hideProgress();
            if (data.status === 'ok') {
                const total = Object.values(data.cleared).reduce((sum, val) => sum + val, 0);
                showToast(`${total} Dateien gelöscht, ${data.logs_removed} Logs gelöscht`, 'success');
                loadStatus();
                showLog('werbung_read');
            } else {
                showToast('Cleanup fehlgeschlagen', 'error');
            }
        }, 500);
    } catch (err) {
        hideProgress();
        showToast(`Fehler: ${err.message}`, 'error');
    }
}

// ═══════════════════════════════════════════════════════════
// Progress Bar (mit simuliertem Fortschritt)
// ═══════════════════════════════════════════════════════════

let progressInterval = null;
let currentProgress = 0;

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

    // Simuliere Fortschritt bis 90%
    if (progressInterval) clearInterval(progressInterval);
    progressInterval = setInterval(() => {
        if (currentProgress < 90) {
            currentProgress += Math.random() * 10; // Zufällige Schritte
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
