/**
 * CSV Verarbeiter Frontend - Streamlit UI Nachbau
 */

const API_BASE = '/api/csv';

const state = {
    currentFile: null,
    currentJobId: null,
    pollingInterval: null,
    downloadZipUrl: null
};

const elements = {
    uploadArea: document.getElementById('uploadArea'),
    fileInput: document.getElementById('fileInput'),
    uploadStatus: document.getElementById('uploadStatus'),
    fileNameDisplay: document.getElementById('fileNameDisplay'),
    fileSizeDisplay: document.getElementById('fileSizeDisplay'),
    processStatus: document.getElementById('processStatus'),
    statusBadge: document.getElementById('statusBadge'),
    statusDetails: document.getElementById('statusDetails'),

    reportSection: document.getElementById('reportSection'),
    metricReplacements: document.getElementById('metricReplacements'),
    metricErrors: document.getElementById('metricErrors'),
    metricOpen: document.getElementById('metricOpen'),
    latestReportInfo: document.getElementById('latestReportInfo'),
    tabButtons: document.querySelectorAll('.tab-button'),
    tabMini: document.getElementById('tab-mini'),
    tabAenderungen: document.getElementById('tab-aenderungen'),
    tabFehler: document.getElementById('tab-fehler'),
    tabNicht: document.getElementById('tab-nicht-gefunden'),

    exportSelect: document.getElementById('exportSelect'),
    zipNameInput: document.getElementById('zipNameInput'),
    includeReportCheckbox: document.getElementById('includeReportCheckbox'),
    includeLogCheckbox: document.getElementById('includeLogCheckbox'),
    createZipBtn: document.getElementById('createZipBtn'),
    exportResult: document.getElementById('exportResult'),
    createdZipName: document.getElementById('createdZipName'),
    downloadZipBtn: document.getElementById('downloadZipBtn'),

    logDetails: document.getElementById('logDetails'),
    latestLogName: document.getElementById('latestLogName'),
    latestLogContent: document.getElementById('latestLogContent'),

    cleanupBtn: document.getElementById('cleanupBtn'),
    cleanupResult: document.getElementById('cleanupResult'),

    messageModal: document.getElementById('messageModal'),
    modalIcon: document.getElementById('modalIcon'),
    modalTitle: document.getElementById('modalTitle'),
    modalMessage: document.getElementById('modalMessage'),
    modalCloseBtn: document.getElementById('modalCloseBtn')
};

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

function showModal(type, title, message) {
    elements.modalIcon.textContent = type === 'success' ? 'OK' : 'X';
    elements.modalTitle.textContent = title;
    elements.modalMessage.textContent = message;
    elements.messageModal.style.display = 'flex';
}

function hideModal() {
    elements.messageModal.style.display = 'none';
}

function setupEventListeners() {
    elements.fileInput.addEventListener('change', handleFileSelect);
    
    // Click to select files
    elements.uploadArea.addEventListener('click', () => {
        elements.fileInput.click();
    });

    // Drag & Drop
    elements.uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.uploadArea.classList.add('drag-over');
    });

    elements.uploadArea.addEventListener('dragleave', () => {
        elements.uploadArea.classList.remove('drag-over');
    });

    elements.uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.uploadArea.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    elements.tabButtons.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    elements.createZipBtn.addEventListener('click', createExportZip);
    elements.downloadZipBtn.addEventListener('click', downloadZip);
    elements.cleanupBtn.addEventListener('click', cleanupAll);
    elements.modalCloseBtn.addEventListener('click', hideModal);
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFile(file) {
    const validExtensions = ['.csv', '.zip'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();

    if (!validExtensions.includes(fileExt)) {
        showModal('error', 'Ungueltiger Dateityp', 'Bitte nur CSV oder ZIP Dateien hochladen.');
        return;
    }

    state.currentFile = file;
    elements.fileNameDisplay.textContent = file.name;
    elements.fileSizeDisplay.textContent = formatFileSize(file.size);
    elements.uploadStatus.style.display = 'flex';

    startProcessing();
}

async function startProcessing() {
    if (!state.currentFile) return;

    try {
        elements.processStatus.style.display = 'block';
        elements.statusBadge.textContent = 'Uploading...';
        elements.statusDetails.textContent = '';

        // Zeige Progress
        showProgress('Lade Datei hoch...', 0);

        const jobId = await uploadFile(state.currentFile);
        state.currentJobId = jobId;

        updateProgress(30);
        updateProgressText('Datei hochgeladen, starte Verarbeitung...');

        elements.statusBadge.textContent = 'Processing...';
        elements.statusDetails.textContent = `Job ID: ${jobId}`;

        await triggerProcessing(jobId);
        
        updateProgress(50);
        updateProgressText('Verarbeite Daten...');
        
        startPolling(jobId);
    } catch (error) {
        hideProgress();
        const errorMsg = error.message || JSON.stringify(error) || 'Unbekannter Fehler';
        showModal('error', 'Fehler', errorMsg);
    }
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('files', file);

    const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload fehlgeschlagen');
    }

    const data = await response.json();
    return data.job_id;
}

async function triggerProcessing(jobId) {
    const response = await fetch(`${API_BASE}/process?job_id=${jobId}&skip_critical=false`, {
        method: 'POST'
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Processing konnte nicht gestartet werden');
    }
}

function startPolling(jobId) {
    if (state.pollingInterval) clearInterval(state.pollingInterval);

    let progressValue = 50;
    state.pollingInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/status/${jobId}`);
            const data = await response.json();

            // Simuliere Progress
            if (progressValue < 90) {
                progressValue += 5;
                updateProgress(progressValue);
            }

            if (data.status === 'completed') {
                stopPolling();
                updateProgress(100);
                updateProgressText('Fertig!');
                setTimeout(() => hideProgress(), 800);
                handleProcessingComplete(data);
            } else if (data.status === 'failed') {
                stopPolling();
                hideProgress();
                handleProcessingFailed(data);
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 2000);
}

function stopPolling() {
    if (state.pollingInterval) {
        clearInterval(state.pollingInterval);
        state.pollingInterval = null;
    }
}

function handleProcessingComplete(data) {
    elements.statusBadge.textContent = 'Abgeschlossen';
    elements.statusDetails.textContent = 'Verarbeitung abgeschlossen';

    loadLatestReport();
    loadProcessedFiles();
    loadLatestLog();
}

function handleProcessingFailed(data) {
    elements.statusBadge.textContent = 'Fehler';
    const errorMsg = data.error || 'Unbekannter Fehler';
    elements.statusDetails.textContent = errorMsg;
    showModal('error', 'Processing fehlgeschlagen', errorMsg);
}

function switchTab(tabName) {
    elements.tabButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    elements.tabMini.style.display = tabName === 'mini' ? 'block' : 'none';
    elements.tabAenderungen.style.display = tabName === 'aenderungen' ? 'block' : 'none';
    elements.tabFehler.style.display = tabName === 'fehler' ? 'block' : 'none';
    elements.tabNicht.style.display = tabName === 'nicht-gefunden' ? 'block' : 'none';
}

function renderTable(container, rows) {
    if (!rows || rows.length === 0) {
        container.innerHTML = '<p class="empty-message">Keine Daten vorhanden.</p>';
        return;
    }

    const columns = Object.keys(rows[0]);
    const table = document.createElement('table');
    table.className = 'report-table';

    const thead = document.createElement('thead');
    const headRow = document.createElement('tr');
    columns.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col;
        headRow.appendChild(th);
    });
    thead.appendChild(headRow);

    const tbody = document.createElement('tbody');
    rows.forEach(row => {
        const tr = document.createElement('tr');
        columns.forEach(col => {
            const td = document.createElement('td');
            const val = row[col] === null || row[col] === undefined ? '' : String(row[col]);
            td.textContent = val;
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });

    table.appendChild(thead);
    table.appendChild(tbody);

    container.innerHTML = '';
    container.appendChild(table);
}

function updateMetrics(miniReport) {
    if (!miniReport || miniReport.length === 0) {
        elements.metricReplacements.textContent = '0';
        elements.metricErrors.textContent = '0';
        elements.metricOpen.textContent = '0';
        return;
    }

    const replacements = miniReport.reduce((acc, row) => acc + (parseInt(row['Ersetzungen'], 10) || 0), 0);
    const openIds = miniReport.reduce((acc, row) => acc + (parseInt(row['Offene Order-IDs'], 10) || 0), 0);
    const errors = miniReport.filter(row => row['Verarbeitung OK'] === '❌').length;

    elements.metricReplacements.textContent = String(replacements);
    elements.metricErrors.textContent = String(errors);
    elements.metricOpen.textContent = String(openIds);
}

async function loadLatestReport() {
    try {
        const response = await fetch(`${API_BASE}/report/latest`);
        if (!response.ok) {
            throw new Error('Report konnte nicht geladen werden');
        }

        const data = await response.json();
        if (!data.filename) {
            elements.reportSection.style.display = 'none';
            return;
        }

        const sheets = data.sheets || {};
        const mini = sheets['Mini-Report'] || [];

        updateMetrics(mini);
        renderTable(elements.tabMini, mini);
        renderTable(elements.tabAenderungen, sheets['Änderungen'] || []);
        renderTable(elements.tabFehler, sheets['Fehler'] || []);
        renderTable(elements.tabNicht, sheets['Nicht gefunden'] || []);

        elements.reportSection.style.display = 'block';
        elements.latestReportInfo.style.display = 'block';
        elements.latestReportInfo.textContent = `Letzter Report: ${data.filename}`;
    } catch (error) {
        console.error('Load report error:', error);
    }
}

async function loadProcessedFiles() {
    try {
        const response = await fetch(`${API_BASE}/list-processed-files`);
        if (!response.ok) {
            throw new Error('Dateiliste konnte nicht geladen werden');
        }

        const data = await response.json();
        const files = data.files || [];

        elements.exportSelect.innerHTML = '';
        if (files.length === 0) {
            const opt = document.createElement('option');
            opt.textContent = 'Keine CSV-Dateien vorhanden';
            opt.disabled = true;
            elements.exportSelect.appendChild(opt);
            return;
        }

        files.forEach(file => {
            const opt = document.createElement('option');
            opt.value = file;
            opt.textContent = file;
            elements.exportSelect.appendChild(opt);
        });
    } catch (error) {
        console.error('Load processed files error:', error);
    }
}

function getSelectedExportFiles() {
    return Array.from(elements.exportSelect.selectedOptions).map(opt => opt.value);
}

async function createExportZip() {
    const selected = getSelectedExportFiles();
    if (selected.length === 0) {
        showModal('error', 'Keine Auswahl', 'Bitte CSV-Dateien auswaehlen.');
        return;
    }

    const zipName = elements.zipNameInput.value.trim();
    if (!zipName) {
        showModal('error', 'Kein Name', 'Bitte ZIP-Dateinamen eingeben.');
        return;
    }

    try {
        elements.createZipBtn.disabled = true;
        
        // Zeige Progress
        showProgress('Erstelle ZIP-Datei...', 0);
        
        const response = await fetch(`${API_BASE}/create-export-zip`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                csv_files: selected,
                zip_name: zipName,
                include_report: elements.includeReportCheckbox.checked,
                include_log: elements.includeLogCheckbox.checked
            })
        });

        updateProgress(50);

        if (!response.ok) {
            hideProgress();
            const error = await response.json();
            throw new Error(error.detail || 'ZIP-Erstellung fehlgeschlagen');
        }

        const data = await response.json();
        
        updateProgress(100);
        updateProgressText('ZIP erstellt!');
        
        setTimeout(() => {
            hideProgress();
            elements.exportResult.style.display = 'block';
            elements.createdZipName.textContent = data.zip_filename;
            state.downloadZipUrl = data.download_url;
            loadProcessedFiles();
        }, 500);

    } catch (error) {
        hideProgress();
        showModal('error', 'Fehler', error.message);
    } finally {
        elements.createZipBtn.disabled = false;
    }
}

function downloadZip() {
    if (state.downloadZipUrl) {
        window.location.href = state.downloadZipUrl;
    }
}

async function loadLatestLog() {
    try {
        const response = await fetch(`${API_BASE}/logs/db?prefix=csv&limit=200`);
        if (!response.ok) {
            throw new Error('Logfile konnte nicht geladen werden');
        }

        const data = await response.json();
        const logs = data.logs || [];
        if (logs.length === 0) {
            elements.latestLogName.textContent = 'Keine DB-Logs gefunden';
            elements.latestLogContent.textContent = '';
            return;
        }

        elements.latestLogName.textContent = `DB Logs (prefix: ${data.prefix})`;
        const lines = logs.map(entry => {
            const rawTs = entry.timestamp || '';
            const ts = formatTimestamp(rawTs);
            const level = entry.level || '';
            const jobType = entry.job_type || '';
            const msg = entry.message || '';
            return `[${ts}] [${jobType}] [${level}] ${msg}`;
        });
        elements.latestLogContent.textContent = lines.join('\n');
    } catch (error) {
        console.error('Load log error:', error);
    }
}

function formatTimestamp(value) {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);

    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');

    return `${day}.${month}.${year}, ${hours}:${minutes}:${seconds}`;
}

async function cleanupAll() {
    try {
        const response = await fetch(`${API_BASE}/cleanup-all`, { method: 'POST' });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Cleanup fehlgeschlagen');
        }

        const data = await response.json();
        const errorCount = (data.errors || []).length;
        elements.cleanupResult.textContent = errorCount === 0
            ? `Alle Verzeichnisse geleert. Dateien geloescht: ${data.deleted}`
            : `Geloescht: ${data.deleted}, Fehler: ${errorCount}`;

        loadProcessedFiles();
        loadLatestReport();
        loadLatestLog();
    } catch (error) {
        showModal('error', 'Fehler', error.message);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadProcessedFiles();
    loadLatestReport();
    loadLatestLog();
});