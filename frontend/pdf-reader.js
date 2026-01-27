// Basic helpers
const API_BASE = `${window.location.origin}/api/pdf`;

function logTo(el, message) {
  const box = document.getElementById(el);
  if (!box) return;
  const ts = new Date().toLocaleTimeString('de-DE');
  box.textContent = `[${ts}] ${message}\n` + box.textContent;
}

async function upload(endpoint, inputId, logId) {
  const input = document.getElementById(inputId);
  if (!input || !input.files.length) {
    logTo(logId, 'Bitte mindestens eine PDF auswählen.');
    return false;
  }

  const fd = new FormData();
  for (const file of input.files) {
    fd.append('files', file);
  }

  const url = `${API_BASE}/${endpoint}/upload`;
  logTo(logId, `Sende ${input.files.length} Dateien…`);

  try {
    const res = await fetch(url, { method: 'POST', body: fd });
    const data = await res.json();
    if (!res.ok || data.status === 'error') throw new Error(data.message || res.status);
    logTo(logId, `✓ Upload ok (${data.saved?.length || 0} Dateien)`);
    return true;
  } catch (e) {
    logTo(logId, `✗ Fehler: ${e.message}`);
    return false;
  }
}

async function extract(logId) {
  logTo(logId, 'Extrahiere erste Seiten…');
  try {
    const res = await fetch(`${API_BASE}/werbung/extract`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok || data.status === 'error') throw new Error(data.message || res.status);
    logTo(logId, `✓ Extrahiert: ${data.extracted?.length || 0} Dateien`);
    return true;
  } catch (e) {
    logTo(logId, `✗ Fehler: ${e.message}`);
    return false;
  }
}

async function process(endpoint, logId) {
  logTo(logId, 'Verarbeite…');
  try {
    const res = await fetch(`${API_BASE}/${endpoint}/process`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok || data.status === 'error') throw new Error(data.message || res.status);
    logTo(logId, `✓ Verarbeitet: ${data.count || 0} Einträge`);
    return true;
  } catch (e) {
    logTo(logId, `✗ Fehler: ${e.message}`);
    return false;
  }
}

async function downloadResult(endpoint, filename, logId) {
  try {
    const res = await fetch(`${API_BASE}/${endpoint}/result`);
    if (!res.ok) throw new Error(res.statusText);
    const blob = await res.blob();
    if (blob.type.includes('json')) {
      const text = await blob.text();
      logTo(logId, `✗ Nicht gefunden oder Fehler: ${text}`);
      return;
    }
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    logTo(logId, '✓ Datei heruntergeladen');
  } catch (e) {
    logTo(logId, `✗ Download-Fehler: ${e.message}`);
  }
}

function bindUi() {
  // Werbung: Auto-Upload bei Dateiauswahl
  document.getElementById('ads-input')?.addEventListener('change', async (e) => {
    if (e.target.files.length > 0) {
      const success = await upload('werbung', 'ads-input', 'ads-log');
      document.getElementById('ads-extract').disabled = !success;
      document.getElementById('ads-process').disabled = true;
    }
  });

  document.getElementById('ads-extract')?.addEventListener('click', async () => {
    const success = await extract('ads-log');
    document.getElementById('ads-process').disabled = !success;
  });

  document.getElementById('ads-process')?.addEventListener('click', () => process('werbung', 'ads-log'));
  document.getElementById('ads-download')?.addEventListener('click', () => downloadResult('werbung', 'werbung.xlsx', 'ads-log'));

  document.getElementById('ads-read-log')?.addEventListener('click', () => viewLog('werbung_read.log', 'ads-log'));
  document.getElementById('ads-extract-log')?.addEventListener('click', () => viewLog('werbung_extraction.log', 'ads-log'));

  // Rechnungen: Auto-Upload bei Dateiauswahl
  document.getElementById('inv-input')?.addEventListener('change', async (e) => {
    if (e.target.files.length > 0) {
      const success = await upload('rechnungen', 'inv-input', 'inv-log');
      document.getElementById('inv-process').disabled = !success;
    }
  });

  document.getElementById('inv-process')?.addEventListener('click', () => process('rechnungen', 'inv-log'));
  document.getElementById('inv-download')?.addEventListener('click', () => downloadResult('rechnungen', 'rechnungen.xlsx', 'inv-log'));

  document.getElementById('inv-read-log')?.addEventListener('click', () => viewLog('rechnung_read.log', 'inv-log'));

  document.getElementById('clear-dirs')?.addEventListener('click', async () => {
    try {
      const res = await fetch(`${API_BASE}/cleanup`, { method: 'POST' });
      const data = await res.json();
      if (!res.ok || data.status !== 'ok') throw new Error(data.message || res.statusText);
      logTo('ads-log', '✓ Verzeichnisse geleert');
      logTo('inv-log', '✓ Verzeichnisse geleert');
      await refreshStatus();
    } catch (e) {
      logTo('ads-log', `✗ Cleanup-Fehler: ${e.message}`);
      logTo('inv-log', `✗ Cleanup-Fehler: ${e.message}`);
    }
  });

  refreshStatus();
}

document.addEventListener('DOMContentLoaded', bindUi);

async function refreshStatus() {
  const panel = document.getElementById('status-warnings');
  if (!panel) return;
  try {
    const res = await fetch(`${API_BASE}/status`);
    const data = await res.json();
    const warnings = [];
    const addWarning = (label, info) => {
      if ((info.count || 0) > 0) {
        warnings.push(`⚠️ ${label}: ${info.count} Dateien`);
      }
    };
    addWarning('Rechnungen', data.rechnungen || {});
    addWarning('Werbung', data.werbung || {});
    addWarning('Temporäre Werbung', data.tmp || {});

    if (warnings.length === 0) {
      panel.style.display = 'none';
      panel.textContent = '';
    } else {
      panel.style.display = 'block';
      panel.innerHTML = warnings.map(w => `<div>${w}</div>`).join('');
    }
  } catch (e) {
    panel.style.display = 'block';
    panel.textContent = `✗ Status konnte nicht geladen werden: ${e.message}`;
  }
}

async function viewLog(logfile, boxId) {
  try {
    const res = await fetch(`${API_BASE}/logs/${logfile}`);
    const data = await res.json();
    if (!res.ok || data.status === 'error') throw new Error(data.message || res.status);
    const box = document.getElementById(boxId);
    if (box) {
      box.textContent = data.content || '(Logfile leer)';
      box.scrollTop = 0;
    }
  } catch (e) {
    logTo(boxId, `✗ Log-Fehler: ${e.message}`);
  }
}
