import { useState, useRef, useEffect } from 'react';
import { Upload, FileSpreadsheet, Download, Trash2, RefreshCw, CheckCircle, XCircle, Package } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs } from '@/components/ui/tabs';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table';
import { Dialog } from '@/components/ui/dialog';
import { ProgressOverlay, useProgress } from '@/components/shared/progress-overlay';
import { csvApi, type CsvStatus, type CsvReport } from '@/lib/api-client';

// ============ Types ============
interface MetricData {
  replacements: number;
  errors: number;
  openOrders: number;
}

interface LogEntry {
  timestamp: string;
  level: string;
  job_type: string;
  message: string;
}

// ============ Helper Functions ============
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

function formatTimestamp(value: string): string {
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

function calculateMetrics(report: CsvReport | null): MetricData {
  const metrics: MetricData = { replacements: 0, errors: 0, openOrders: 0 };
  
  if (!report?.sheets?.['Mini-Report']) return metrics;
  
  const miniReport = report.sheets['Mini-Report'];
  
  metrics.replacements = miniReport.reduce((acc, row) => {
    const val = parseInt(String(row['Ersetzungen'] || '0'), 10);
    return acc + (isNaN(val) ? 0 : val);
  }, 0);
  
  metrics.openOrders = miniReport.reduce((acc, row) => {
    const val = parseInt(String(row['Offene Order-IDs'] || '0'), 10);
    return acc + (isNaN(val) ? 0 : val);
  }, 0);
  
  metrics.errors = miniReport.filter(row => row['Verarbeitung OK'] === '❌').length;
  
  return metrics;
}

function getColumns(rows: Record<string, string>[]): string[] {
  if (!rows || rows.length === 0) return [];
  return Object.keys(rows[0]);
}

// ============ Main Component ============
export function CsvProcessor() {
  // State
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [, setJobId] = useState<string | null>(null); // Used in startProcessing
  const [status, setStatus] = useState<CsvStatus['status'] | null>(null);
  const [statusText, setStatusText] = useState<string>('');
  
  const [report, setReport] = useState<CsvReport | null>(null);
  const [metrics, setMetrics] = useState<MetricData>({ replacements: 0, errors: 0, openOrders: 0 });
  
  const [processedFiles, setProcessedFiles] = useState<string[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [zipName, setZipName] = useState('export_DE_2024');
  const [includeReport, setIncludeReport] = useState(true);
  const [includeLog, setIncludeLog] = useState(true);
  const [createdZip, setCreatedZip] = useState<{ name: string; url: string } | null>(null);
  
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [logsOpen, setLogsOpen] = useState(false);
  const [cleanupResult, setCleanupResult] = useState<string>('');
  
  const [modalOpen, setModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState<{ type: 'success' | 'error'; title: string; message: string }>({
    type: 'success',
    title: '',
    message: ''
  });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const { isOpen: progressOpen, progress, text: progressText, startProgress, updateProgress, stopProgress } = useProgress();

  // Load initial data
  useEffect(() => {
    loadProcessedFiles();
    loadLatestReport();
    loadLogs();

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  // ============ API Functions ============
  const loadProcessedFiles = async () => {
    try {
      const data = await csvApi.listProcessedFiles();
      setProcessedFiles(data.files || []);
    } catch (err) {
      console.error('Load processed files error:', err);
    }
  };

  const loadLatestReport = async () => {
    try {
      const data = await csvApi.getLatestReport();
      if (data.filename) {
        setReport(data as CsvReport);
        setMetrics(calculateMetrics(data as CsvReport));
      } else {
        setReport(null);
        setMetrics({ replacements: 0, errors: 0, openOrders: 0 });
      }
    } catch (err) {
      console.error('Load report error:', err);
    }
  };

  const loadLogs = async () => {
    try {
      const data = await csvApi.getLogs('csv', 200);
      setLogs(data.logs || []);
    } catch (err) {
      console.error('Load logs error:', err);
    }
  };

  // ============ File Handling ============
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file: File) => {
    const validExtensions = ['.csv', '.zip'];
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();

    if (!validExtensions.includes(fileExt)) {
      showModal('error', 'Ungültiger Dateityp', 'Bitte nur CSV oder ZIP Dateien hochladen.');
      return;
    }

    setCurrentFile(file);
    setStatus(null);
    setStatusText('');
    setJobId(null);
    setCreatedZip(null);
    startProcessing(file);
  };

  // ============ Processing ============
  const startProcessing = async (file: File) => {
    try {
      startProgress('Lade Datei hoch...');
      setStatus('pending');
      setStatusText('Uploading...');

      // Upload
      const uploadData = await csvApi.upload(file);
      const newJobId = uploadData.job_id;
      setJobId(newJobId);

      updateProgress(30, 'Datei hochgeladen, starte Verarbeitung...');
      setStatus('pending');
      setStatusText(`Job ID: ${newJobId}`);

      // Trigger processing
      await csvApi.process(newJobId, false);
      
      updateProgress(50, 'Verarbeite Daten...');
      setStatus('processing');
      setStatusText('Processing...');

      // Start polling
      startPolling(newJobId);
    } catch (err: any) {
      stopProgress();
      const errorMsg = err.response?.data?.detail || err.message || 'Unbekannter Fehler';
      showModal('error', 'Fehler', errorMsg);
      setStatus('failed');
      setStatusText(errorMsg);
    }
  };

  const startPolling = (jobId: string) => {
    if (pollingRef.current) clearInterval(pollingRef.current);

    let progressValue = 50;
    pollingRef.current = setInterval(async () => {
      try {
        const data = await csvApi.getStatus(jobId);

        // Simuliere Progress
        if (progressValue < 90) {
          progressValue += 5;
          updateProgress(progressValue);
        }

        if (data.status === 'completed') {
          stopPolling();
          updateProgress(100, 'Fertig!');
          setTimeout(() => stopProgress(), 800);
          setStatus('completed');
          setStatusText('Abgeschlossen');
          handleProcessingComplete();
        } else if (data.status === 'failed') {
          stopPolling();
          stopProgress();
          setStatus('failed');
          const errorMsg = data.error || 'Unbekannter Fehler';
          setStatusText(errorMsg);
          showModal('error', 'Processing fehlgeschlagen', errorMsg);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2000);
  };

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  const handleProcessingComplete = async () => {
    await Promise.all([
      loadLatestReport(),
      loadProcessedFiles(),
      loadLogs()
    ]);
  };

  // ============ Export ============
  const handleCreateZip = async () => {
    if (selectedFiles.length === 0) {
      showModal('error', 'Keine Auswahl', 'Bitte CSV-Dateien auswählen.');
      return;
    }

    if (!zipName.trim()) {
      showModal('error', 'Kein Name', 'Bitte ZIP-Dateinamen eingeben.');
      return;
    }

    try {
      startProgress('Erstelle ZIP-Datei...');
      
      const data = await csvApi.createExportZip({
        csv_files: selectedFiles,
        zip_name: zipName.trim(),
        include_report: includeReport,
        include_log: includeLog
      });

      updateProgress(100, 'ZIP erstellt!');
      setTimeout(() => stopProgress(), 500);
      
      setCreatedZip({ name: data.zip_filename, url: data.download_url });
      await loadProcessedFiles();
    } catch (err: any) {
      stopProgress();
      const errorMsg = err.response?.data?.detail || err.message || 'Unbekannter Fehler';
      showModal('error', 'Fehler', errorMsg);
    }
  };

  const handleDownloadZip = () => {
    if (createdZip?.url) {
      window.location.href = createdZip.url;
    }
  };

  // ============ Cleanup ============
  const handleCleanup = async () => {
    try {
      const data = await csvApi.cleanupAll();
      const errorCount = (data.errors || []).length;
      setCleanupResult(
        errorCount === 0
          ? `Alle Verzeichnisse geleert. Dateien gelöscht: ${data.deleted}`
          : `Gelöscht: ${data.deleted}, Fehler: ${errorCount}`
      );
      
      await Promise.all([
        loadProcessedFiles(),
        loadLatestReport(),
        loadLogs()
      ]);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Unbekannter Fehler';
      showModal('error', 'Fehler', errorMsg);
    }
  };

  // ============ Modal ============
  const showModal = (type: 'success' | 'error', title: string, message: string) => {
    setModalContent({ type, title, message });
    setModalOpen(true);
  };

  // ============ Render Helpers ============
  const renderTable = (rows: Record<string, string>[]) => {
    if (!rows || rows.length === 0) {
      return <p className="text-text-secondary py-4">Keine Daten vorhanden.</p>;
    }

    const columns = getColumns(rows);

    return (
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((col, idx) => (
                <TableHead key={idx}>{col}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row, rowIdx) => (
              <TableRow key={rowIdx}>
                {columns.map((col, colIdx) => (
                  <TableCell key={colIdx}>
                    {row[col] === null || row[col] === undefined ? '' : String(row[col])}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-text mb-2">CSV Verarbeiter</h1>
        <p className="text-text-secondary">Amazon DATEV Export Processing System</p>
      </div>

      {/* ============ Upload Card ============ */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5" />
            Datei-Upload (CSV oder ZIP)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-text-secondary mb-4">Amazon DATEV Export Dateien hochladen und verarbeiten</p>
          
          {/* Upload Zone */}
          <div 
            className="border-2 border-dashed border-border rounded-lg p-8 text-center transition-colors hover:border-primary cursor-pointer"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.zip"
              className="hidden"
              onChange={handleFileSelect}
            />
            
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-success/10 flex items-center justify-center">
              <FileSpreadsheet className="w-8 h-8 text-success" />
            </div>
            
            <h3 className="text-lg font-semibold text-text mb-2">
              Dateien hier ablegen oder klicken zum Auswählen
            </h3>
            <p className="text-text-secondary">Unterstützte Formate: .csv, .zip</p>
          </div>

          {/* Upload Status */}
          {currentFile && (
            <div className="mt-4 p-4 bg-background rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-medium text-text">{currentFile.name}</span>
                  <span className="text-text-secondary ml-2">({formatFileSize(currentFile.size)})</span>
                </div>
              </div>
            </div>
          )}

          {/* Process Status */}
          {status && (
            <div className="mt-4 p-4 bg-background rounded-lg">
              <div className="flex items-center gap-3">
                {status === 'completed' && <CheckCircle className="w-5 h-5 text-success" />}
                {status === 'failed' && <XCircle className="w-5 h-5 text-danger" />}
                {status === 'processing' && <RefreshCw className="w-5 h-5 text-primary animate-spin" />}
                {status === 'pending' && <RefreshCw className="w-5 h-5 text-primary" />}
                
                <div>
                  <span className={`font-medium ${
                    status === 'completed' ? 'text-success' : 
                    status === 'failed' ? 'text-danger' : 'text-primary'
                  }`}>
                    {status === 'completed' ? 'Abgeschlossen' : 
                     status === 'failed' ? 'Fehler' : 
                     status === 'processing' ? 'Processing...' : 'Pending'}
                  </span>
                  {statusText && (
                    <span className="text-text-secondary ml-2 text-sm">{statusText}</span>
                  )}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ============ Report Card ============ */}
      {report && (
        <Card>
          <CardHeader>
            <CardTitle>Mini-Report</CardTitle>
          </CardHeader>
          <CardContent>
            {/* Metrics */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-background rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-primary">{metrics.replacements}</div>
                <div className="text-sm text-text-secondary">Ersetzungen</div>
              </div>
              <div className="bg-background rounded-lg p-4 text-center">
                <div className={`text-2xl font-bold ${metrics.errors > 0 ? 'text-danger' : 'text-success'}`}>
                  {metrics.errors}
                </div>
                <div className="text-sm text-text-secondary">Fehler</div>
              </div>
              <div className="bg-background rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-warning">{metrics.openOrders}</div>
                <div className="text-sm text-text-secondary">Offene Order-IDs</div>
              </div>
            </div>

            {/* Tabs */}
            <Tabs 
              defaultValue="mini"
              tabs={[
                { value: 'mini', label: 'Mini-Report', content: renderTable(report.sheets['Mini-Report'] || []) },
                { value: 'aenderungen', label: 'Änderungen', content: renderTable(report.sheets['Änderungen'] || []) },
                { value: 'fehler', label: 'Fehler', content: renderTable(report.sheets['Fehler'] || []) },
                { value: 'nicht', label: 'Nicht gefunden', content: renderTable(report.sheets['Nicht gefunden'] || []) },
              ]}
            />

            <p className="text-text-secondary text-sm mt-4">
              Letzter Report: {report.filename}
            </p>
          </CardContent>
        </Card>
      )}

      {/* ============ Export Card ============ */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="w-5 h-5" />
            Nachbereitung / Export
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-text-secondary mb-4">Wähle CSV-Dateien für den Export (ZIP)</p>
          
          {/* File Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-text mb-2">CSV-Dateien auswählen:</label>
            <select 
              multiple
              className="w-full h-32 p-2 border border-border rounded-md bg-background text-text"
              value={selectedFiles}
              onChange={(e) => setSelectedFiles(Array.from(e.target.selectedOptions, option => option.value))}
            >
              {processedFiles.length === 0 ? (
                <option disabled>Keine CSV-Dateien vorhanden</option>
              ) : (
                processedFiles.map((file, idx) => (
                  <option key={idx} value={file}>{file}</option>
                ))
              )}
            </select>
          </div>

          {/* ZIP Name */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-text mb-2">ZIP-Dateiname (ohne .zip):</label>
            <Input
              value={zipName}
              onChange={(e) => setZipName(e.target.value)}
              placeholder="export_DE_2024"
            />
          </div>

          {/* Checkboxes */}
          <div className="flex gap-6 mb-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input 
                type="checkbox" 
                checked={includeReport}
                onChange={(e) => setIncludeReport(e.target.checked)}
                className="w-4 h-4"
              />
              <span className="text-text">Mini-Report beilegen</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input 
                type="checkbox" 
                checked={includeLog}
                onChange={(e) => setIncludeLog(e.target.checked)}
                className="w-4 h-4"
              />
              <span className="text-text">Letztes Logfile beilegen</span>
            </label>
          </div>

          {/* Create Button */}
          <Button 
            onClick={handleCreateZip}
            className="bg-success hover:bg-success-hover"
          >
            <Package className="w-4 h-4 mr-2" />
            ZIP-Datei erstellen
          </Button>

          {/* Download Result */}
          {createdZip && (
            <div className="mt-4 p-4 bg-success/10 border border-success rounded-lg">
              <p className="text-success mb-2">
                ZIP erfolgreich erstellt: <strong>{createdZip.name}</strong>
              </p>
              <Button 
                onClick={handleDownloadZip}
                variant="primary"
              >
                <Download className="w-4 h-4 mr-2" />
                ZIP-Datei herunterladen
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ============ Logs Card ============ */}
      <Card>
        <CardHeader>
          <CardTitle>Letztes Logfile</CardTitle>
        </CardHeader>
        <CardContent>
          <details open={logsOpen} onToggle={(e) => setLogsOpen((e.target as HTMLDetailsElement).open)}>
            <summary className="cursor-pointer text-text-secondary">
              DB Logs (prefix: csv) - {logs.length} Einträge
            </summary>
            <pre className="mt-4 p-4 bg-background rounded-lg text-xs text-text-secondary overflow-x-auto max-h-96">
              {logs.length === 0 
                ? 'Keine Logs vorhanden'
                : logs.map(entry => 
                    `[${formatTimestamp(entry.timestamp)}] [${entry.job_type}] [${entry.level}] ${entry.message}`
                  ).join('\n')
              }
            </pre>
          </details>
        </CardContent>
      </Card>

      {/* ============ Cleanup Section ============ */}
      <div className="flex items-center gap-4">
        <Button 
          variant="danger"
          onClick={handleCleanup}
        >
          <Trash2 className="w-4 h-4 mr-2" />
          Aufräumen (Alle Dateien löschen)
        </Button>
        {cleanupResult && (
          <span className="text-text-secondary">{cleanupResult}</span>
        )}
      </div>

      {/* ============ Progress Overlay ============ */}
      <ProgressOverlay 
        isOpen={progressOpen} 
        progress={progress} 
        text={progressText}
      />

      {/* ============ Modal ============ */}
      <Dialog open={modalOpen} onClose={() => setModalOpen(false)} title={modalContent.title}>
        <div className="text-center">
          <div className={`w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center ${
            modalContent.type === 'success' ? 'bg-success/10' : 'bg-danger/10'
          }`}>
            {modalContent.type === 'success' ? (
              <CheckCircle className="w-8 h-8 text-success" />
            ) : (
              <XCircle className="w-8 h-8 text-danger" />
            )}
          </div>
          <p className="text-text mb-4">{modalContent.message}</p>
          <Button onClick={() => setModalOpen(false)}>OK</Button>
        </div>
      </Dialog>
    </div>
  );
}
