/* ============================================================================
   CSV Verarbeiter - Frontend JavaScript
   ============================================================================ */

const API_BASE = '/api/csv';
const POLL_INTERVAL = 1000; // 1 second
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

// State Management
const state = {
    currentFile: null,
    currentJobId: null,
    currentJobStatus: null,
    processingHistory: JSON.parse(localStorage.getItem('csvVerarbeiterHistory') || '[]'),
    pollInterval: null,
};

// DOM Elements
const elements = {
    uploadArea: document.getElementById('uploadArea'),
    fileInput: document.getElementById('fileInput'),
    selectFileBtn: document.getElementById('selectFileBtn'),
    uploadStatus: document.getElementById('uploadStatus'),
    fileNameDisplay: document.getElementById('fileNameDisplay'),
    fileSizeDisplay: document.getElementById('fileSizeDisplay'),
    clearFileBtn: document.getElementById('clearFileBtn'),
    skipCriticalAccounts: document.getElementById('skipCriticalAccounts'),
    processBtn: document.getElementById('processBtn'),
    spinner: document.getElementById('spinner'),
    processStatus: document.getElementById('processStatus'),
    statusBadge: document.getElementById('statusBadge'),
    jobIdDisplay: document.getElementById('jobIdDisplay'),
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),
    statusDetails: document.getElementById('statusDetails'),
    resultsSection: document.getElementById('resultsSection'),
    resultsSummary: document.getElementById('resultsSummary'),
    downloadCSVBtn: document.getElementById('downloadCSVBtn'),
    downloadReportBtn: document.getElementById('downloadReportBtn'),
    reportsList: document.getElementById('reportsList'),
    historyList: document.getElementById('historyList'),
    clearHistoryBtn: document.getElementById('clearHistoryBtn'),
    errorModal: document.getElementById('errorModal'),
    errorMessage: document.getElementById('errorMessage'),
    closeErrorBtn: document.getElementById('closeErrorBtn'),
    closeErrorModalBtn: document.getElementById('closeErrorModalBtn'),
    successModal: document.getElementById('successModal'),
    successMessage: document.getElementById('successMessage'),
    closeSuccessBtn: document.getElementById('closeSuccessBtn'),
    closeSuccessModalBtn: document.getElementById('closeSuccessModalBtn'),
    apiStatus: document.getElementById('apiStatus'),
    apiStatusText: document.getElementById('apiStatusText'),
};

/* ============================================================================
   Initialization
   ============================================================================ */

document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkAPIStatus();
    loadReports();
    loadHistory();
    setInterval(checkAPIStatus, 5000); // Check API status every 5 seconds
});

function setupEventListeners() {
    // Upload Area
    elements.uploadArea.addEventListener('click', () => elements.fileInput.click());
    elements.fileInput.addEventListener('change', handleFileSelect);
    elements.selectFileBtn.addEventListener('click', () => elements.fileInput.click());
    
    // Drag & Drop
    elements.uploadArea.addEventListener('dragover', handleDragOver);
    elements.uploadArea.addEventListener('dragleave', handleDragLeave);
    elements.uploadArea.addEventListener('drop', handleDrop);
    
    // Clear Button
    elements.clearFileBtn.addEventListener('click', clearSelectedFile);
    
    // Process Button
    elements.processBtn.addEventListener('click', startProcessing);
    
    // Download Buttons
    elements.downloadCSVBtn.addEventListener('click', () => downloadFile('csv'));
    elements.downloadReportBtn.addEventListener('click', () => downloadFile('report'));
    
    // History
    elements.clearHistoryBtn.addEventListener('click', clearHistory);
    
    // Modals
    elements.closeErrorBtn.addEventListener('click', closeErrorModal);
    elements.closeErrorModalBtn.addEventListener('click', closeErrorModal);
    elements.closeSuccessBtn.addEventListener('click', closeSuccessModal);
    elements.closeSuccessModalBtn.addEventListener('click', closeSuccessModal);
}

/* ============================================================================
   File Upload Handlers
   ============================================================================ */

function handleFileSelect(event) {
    const files = event.target.files;
    if (files.length > 0) {
        selectFile(files[0]);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    elements.uploadArea.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    elements.uploadArea.classList.remove('dragover');
}

function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    elements.uploadArea.classList.remove('dragover');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        selectFile(files[0]);
    }
}

function selectFile(file) {
    // Validate file type
    if (!file.name.endsWith('.csv') && !file.name.endsWith('.zip')) {
        showError('Nur CSV und ZIP Dateien sind erlaubt!');
        return;
    }
    
    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
        showError(`Datei ist zu groß! Maximum: ${MAX_FILE_SIZE / 1024 / 1024}MB`);
        return;
    }
    
    state.currentFile = file;
    updateUploadStatus();
    elements.processBtn.disabled = false;
}

function updateUploadStatus() {
    if (state.currentFile) {
        elements.fileNameDisplay.textContent = state.currentFile.name;
        elements.fileSizeDisplay.textContent = `${(state.currentFile.size / 1024).toFixed(2)} KB`;
        elements.uploadStatus.style.display = 'flex';
        elements.uploadArea.style.display = 'none';
    }
}

function clearSelectedFile() {
    state.currentFile = null;
    elements.fileInput.value = '';
    elements.uploadStatus.style.display = 'none';
    elements.uploadArea.style.display = 'block';
    elements.processBtn.disabled = true;
    elements.resultsSection.style.display = 'none';
}

/* ============================================================================
   Upload & Processing
   ============================================================================ */

async function startProcessing() {
    if (!state.currentFile) {
        showError('Bitte wählen Sie eine Datei aus!');
        return;
    }
    
    try {
        // Step 1: Upload file
        elements.processBtn.disabled = true;
        showProcessingStatus('Datei wird hochgeladen...', 'uploading');
        
        const jobId = await uploadFile(state.currentFile);
        state.currentJobId = jobId;
        elements.jobIdDisplay.textContent = `Job ID: ${jobId}`;
        
        // Step 2: Start processing
        showProcessingStatus('Processing wird gestartet...', 'processing');
        await triggerProcessing(jobId);
        
        // Step 3: Poll for status
        pollJobStatus(jobId);
        
    } catch (error) {
        showError(`Fehler: ${error.message}`);
        elements.processBtn.disabled = false;
        stopPolling();
    }
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload fehlgeschlagen');
    }
    
    const data = await response.json();
    return data.job_id;
}

async function triggerProcessing(jobId) {
    const response = await fetch(`${API_BASE}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            job_id: jobId,
            skip_critical_accounts: elements.skipCriticalAccounts.checked,
        }),
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Processing konnte nicht gestartet werden');
    }
}

function pollJobStatus(jobId) {
    stopPolling();
    
    state.pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/status/${jobId}`);
            
            if (!response.ok) {
                throw new Error('Status konnte nicht abgerufen werden');
            }
            
            const data = await response.json();
            updateJobStatus(data);
            
            if (data.status === 'completed' || data.status === 'failed') {
                stopPolling();
                elements.processBtn.disabled = false;
                
                if (data.status === 'completed') {
                    addToHistory(jobId, state.currentFile.name, data);
                    showResults(data);
                    showSuccess('Processing erfolgreich abgeschlossen!');
                } else {
                    showError(data.error || 'Processing fehlgeschlagen');
                }
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, POLL_INTERVAL);
}

function updateJobStatus(status) {
    state.currentJobStatus = status;
    
    // Update status badge
    const statusMap = {
        'uploading': { text: '📤 Uploading...', class: 'warning' },
        'processing': { text: '⏳ Processing...', class: 'primary' },
        'completed': { text: '✅ Completed', class: 'success' },
        'failed': { text: '❌ Failed', class: 'error' },
    };
    
    const statusInfo = statusMap[status.status] || { text: '❓ Unbekannt', class: 'secondary' };
    elements.statusBadge.textContent = statusInfo.text;
    elements.statusBadge.className = `status-badge ${statusInfo.class}`;
    
    // Update progress
    const progress = status.progress || 0;
    elements.progressFill.style.width = `${progress}%`;
    elements.progressText.textContent = `${progress}%`;
    
    // Update details
    updateStatusDetails(status);
}

function updateStatusDetails(status) {
    elements.statusDetails.innerHTML = '';
    
    const details = [
        { label: 'Status', value: status.status },
        { label: 'Rows', value: status.rows_processed || 0 },
        { label: 'Valid', value: status.valid_rows || 0 },
        { label: 'Errors', value: status.error_rows || 0 },
    ];
    
    details.forEach(detail => {
        const div = document.createElement('div');
        div.className = 'status-detail-item';
        div.innerHTML = `
            <div class="status-detail-label">${detail.label}</div>
            <div class="status-detail-value">${detail.value}</div>
        `;
        elements.statusDetails.appendChild(div);
    });
}

function showProcessingStatus(message, status) {
    elements.processStatus.style.display = 'block';
    updateJobStatus({ status, progress: 0 });
}

function stopPolling() {
    if (state.pollInterval) {
        clearInterval(state.pollInterval);
        state.pollInterval = null;
    }
}

/* ============================================================================
   Results
   ============================================================================ */

function showResults(jobStatus) {
    elements.resultsSection.style.display = 'block';
    
    // Create summary
    const summary = `
        <div class="summary-card success">
            <div class="summary-label">Valid Rows</div>
            <div class="summary-value">${jobStatus.valid_rows || 0}</div>
        </div>
        <div class="summary-card warning">
            <div class="summary-label">Warnings</div>
            <div class="summary-value">${jobStatus.warning_rows || 0}</div>
        </div>
        <div class="summary-card error">
            <div class="summary-label">Errors</div>
            <div class="summary-value">${jobStatus.error_rows || 0}</div>
        </div>
        <div class="summary-card">
            <div class="summary-label">Total Processed</div>
            <div class="summary-value">${jobStatus.rows_processed || 0}</div>
        </div>
    `;
    
    elements.resultsSummary.innerHTML = summary;
    
    // Scroll to results
    elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
}

async function downloadFile(type) {
    if (!state.currentJobId) {
        showError('Keine Job ID verfügbar!');
        return;
    }
    
    try {
        const response = await fetch(
            `${API_BASE}/download/${state.currentJobId}?type=${type}`
        );
        
        if (!response.ok) {
            throw new Error('Download fehlgeschlagen');
        }
        
        // Get filename from Content-Disposition header
        const contentDisposition = response.headers.get('Content-Disposition');
        const filename = contentDisposition
            ? contentDisposition.split('filename=')[1].replace(/"/g, '')
            : `export_${state.currentJobId}.${type === 'report' ? 'xlsx' : 'csv'}`;
        
        // Create blob and download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
    } catch (error) {
        showError(`Download fehlgeschlagen: ${error.message}`);
    }
}

/* ============================================================================
   Reports & History
   ============================================================================ */

async function loadReports() {
    try {
        const response = await fetch(`${API_BASE}/reports`);
        
        if (!response.ok) {
            throw new Error('Reports konnte nicht geladen werden');
        }
        
        const reports = await response.json();
        displayReports(reports.reports || []);
        
    } catch (error) {
        console.error('Error loading reports:', error);
        elements.reportsList.innerHTML = '<p class="empty-message">Fehler beim Laden der Reports</p>';
    }
}

function displayReports(reports) {
    if (reports.length === 0) {
        elements.reportsList.innerHTML = '<p class="empty-message">Keine Reports vorhanden</p>';
        return;
    }
    
    elements.reportsList.innerHTML = reports.map(report => `
        <div class="report-item">
            <div class="report-info">
                <div class="report-name">${report.filename || report}</div>
                <div class="report-date">${new Date(report.created_at || Date.now()).toLocaleString('de-DE')}</div>
            </div>
            <div class="report-actions">
                <button class="btn-primary btn-icon" title="Herunterladen" onclick="downloadReport('${report.filename || report}')">
                    📥
                </button>
            </div>
        </div>
    `).join('');
}

async function downloadReport(filename) {
    try {
        const response = await fetch(`${API_BASE}/download/${filename}`);
        
        if (!response.ok) {
            throw new Error('Download fehlgeschlagen');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
    } catch (error) {
        showError(`Report Download fehlgeschlagen: ${error.message}`);
    }
}

function addToHistory(jobId, filename, status) {
    const historyItem = {
        id: jobId,
        filename,
        timestamp: new Date().toLocaleString('de-DE'),
        status: status.status,
        rows: status.rows_processed,
        errors: status.error_rows,
    };
    
    state.processingHistory.unshift(historyItem);
    state.processingHistory = state.processingHistory.slice(0, 50); // Keep last 50
    localStorage.setItem('csvVerarbeiterHistory', JSON.stringify(state.processingHistory));
    loadHistory();
}

function loadHistory() {
    const history = state.processingHistory;
    
    if (history.length === 0) {
        elements.historyList.innerHTML = '<p class="empty-message">Keine Historie vorhanden</p>';
        return;
    }
    
    elements.historyList.innerHTML = history.map(item => `
        <div class="history-item">
            <div class="history-info">
                <div class="history-name">${item.filename}</div>
                <div class="history-date">${item.timestamp} · ${item.status}</div>
            </div>
            <div class="report-actions">
                <span class="status-badge ${item.status === 'completed' ? 'success' : 'error'} btn-icon">
                    ${item.status === 'completed' ? '✅' : '❌'}
                </span>
            </div>
        </div>
    `).join('');
}

function clearHistory() {
    if (confirm('Möchten Sie die Historie wirklich löschen?')) {
        state.processingHistory = [];
        localStorage.removeItem('csvVerarbeiterHistory');
        loadHistory();
    }
}

/* ============================================================================
   API Status
   ============================================================================ */

async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_BASE}/reports`, { method: 'GET' });
        
        if (response.ok) {
            elements.apiStatus.classList.remove('status-offline');
            elements.apiStatus.classList.add('status-online');
            elements.apiStatusText.textContent = 'Online';
        } else {
            setOffline();
        }
    } catch (error) {
        setOffline();
    }
}

function setOffline() {
    elements.apiStatus.classList.remove('status-online');
    elements.apiStatus.classList.add('status-offline');
    elements.apiStatusText.textContent = 'Offline';
}

/* ============================================================================
   Modals & Notifications
   ============================================================================ */

function showError(message) {
    elements.errorMessage.textContent = message;
    elements.errorModal.classList.add('show');
}

function closeErrorModal() {
    elements.errorModal.classList.remove('show');
}

function showSuccess(message) {
    elements.successMessage.textContent = message;
    elements.successModal.classList.add('show');
}

function closeSuccessModal() {
    elements.successModal.classList.remove('show');
}

// Close modals on outside click
document.addEventListener('click', (e) => {
    if (e.target === elements.errorModal) {
        closeErrorModal();
    }
    if (e.target === elements.successModal) {
        closeSuccessModal();
    }
});

/* ============================================================================
   Utility Functions
   ============================================================================ */

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function formatDate(date) {
    return new Date(date).toLocaleString('de-DE', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    });
}
