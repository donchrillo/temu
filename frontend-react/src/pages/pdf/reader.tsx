import { useState, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Upload, FileText } from 'lucide-react';
import { logsApi } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/shared/loading-spinner';
import { useProgress } from '@/components/shared/progress-overlay';
import axios from 'axios';

const API_BASE = '';

type TabType = 'werbung' | 'rechnungen';

export function PdfReader() {
  const [activeTab, setActiveTab] = useState<TabType>('werbung');
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Progress hook
  const progress = useProgress('Bereite Dateien vor...');

  // Logs Query - alle laden
  const { data: logsData, isLoading: logsLoading, refetch: refetchLogs } = useQuery({
    queryKey: ['pdf-logs'],
    queryFn: () => logsApi.getRecent(50),
    retry: 1,
  });

  // Drag & Drop
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      file => file.type === 'application/pdf'
    );
    setFiles(prev => [...prev, ...droppedFiles]);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      setFiles(prev => [...prev, ...selectedFiles]);
    }
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    
    const endpoint = activeTab === 'werbung' ? '/api/pdf/werbung/upload' : '/api/pdf/rechnungen/upload';
    
    progress.startProgress('Hochladen...');
    
    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });
      
      await axios.post(`${API_BASE}${endpoint}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      progress.updateProgress(100, 'Hochladen abgeschlossen!');
      
      // Logs aktualisieren
      await refetchLogs();
    } catch (error: any) {
      console.error('Upload error:', error);
      progress.updateProgress(0, 'Fehler: ' + (error.response?.data?.detail || error.message || 'Unbekannt'));
    } finally {
      setTimeout(() => progress.closeProgress(), 1500);
    }
  };

  const handleExtract = async () => {
    if (files.length === 0 || activeTab !== 'werbung') return;
    
    progress.startProgress('Extrahiere erste Seite...');
    
    try {
      await axios.post(`${API_BASE}/api/pdf/werbung/extract`);
      progress.updateProgress(100, 'Extraktion abgeschlossen!');
      
      // Logs aktualisieren
      await refetchLogs();
    } catch (error: any) {
      console.error('Extract error:', error);
      progress.updateProgress(0, 'Fehler: ' + (error.response?.data?.detail || error.message || 'Unbekannt'));
    } finally {
      setTimeout(() => progress.closeProgress(), 1500);
    }
  };

  const handleProcess = async () => {
    if (files.length === 0) return;
    
    const endpoint = activeTab === 'werbung' ? '/api/pdf/werbung/process' : '/api/pdf/rechnungen/process';
    
    progress.startProgress('Verarbeite Dateien...');
    
    try {
      await axios.post(`${API_BASE}${endpoint}`);
      progress.updateProgress(100, 'Verarbeitung abgeschlossen!');
      
      // Logs aktualisieren
      await refetchLogs();
    } catch (error: any) {
      console.error('Process error:', error);
      progress.updateProgress(0, 'Fehler: ' + (error.response?.data?.detail || error.message || 'Unbekannt'));
    } finally {
      setTimeout(() => progress.closeProgress(), 1500);
    }
  };

  const handleDownload = async () => {
    if (files.length === 0) return;
    
    const endpoint = activeTab === 'werbung' ? '/api/pdf/werbung/result' : '/api/pdf/rechnungen/result';
    
    progress.startProgress('Erstelle Excel...');
    
    try {
      const response = await axios.get(`${API_BASE}${endpoint}`, {
        responseType: 'blob',
      });
      
      // Download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${activeTab}_export.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      progress.updateProgress(100, 'Download gestartet!');
    } catch (error: any) {
      // Wenn kein Resultat verfügbar
      if (error.response?.status === 404) {
        alert('Noch keine Ergebnisse verfügbar. Bitte zuerst Dateien verarbeiten.');
      } else {
        console.error('Download error:', error);
        progress.updateProgress(0, 'Fehler: ' + (error.message || 'Unbekannt'));
      }
    } finally {
      setTimeout(() => progress.closeProgress(), 1500);
    }
  };

  const handleCleanup = async () => {
    if (!confirm('Möchten Sie wirklich alle Dateien löschen?')) return;
    
    progress.startProgress('Räume auf...');
    
    try {
      await axios.post(`${API_BASE}/api/pdf/cleanup`);
      setFiles([]);
      await refetchLogs();
      progress.updateProgress(100, 'Aufgeräumt!');
    } catch (error: any) {
      console.error('Cleanup error:', error);
      progress.updateProgress(0, 'Fehler: ' + (error.message || 'Unbekannt'));
    } finally {
      setTimeout(() => progress.closeProgress(), 1500);
    }
  };

  const formatFileSize = (bytes: number) => {
    return (bytes / 1024).toFixed(1) + ' KB';
  };

  // Format log entry - wie im alten Frontend
  const formatLogEntry = (log: any) => {
    const timestamp = log.timestamp 
      ? new Date(log.timestamp).toLocaleString('de-DE')
      : '-';
    return `[${timestamp}] [${log.level}] ${log.message}`;
  };

  const logs = logsData || [];
  
  // Filter für PDF-Logs - job_id enthält pdf
  const filteredLogs = logs.filter((l: any) => 
    (l.job_id && l.job_id.toLowerCase().includes('pdf')) ||
    (l.component && l.component.toLowerCase().includes('pdf'))
  );

  return (
    <div className="space-y-6">
      {/* Progress Overlay */}
      <progress.ProgressComponent />

      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-text">PDF Processor</h1>
        <p className="text-text-secondary">Rechnung & Werbung Verarbeitung</p>
      </div>

      {/* Status Cards */}
      <section>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary-light flex items-center justify-center">
                <FileText className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-text-secondary">Status</p>
                <p className="font-medium">{files.length} Dateien bereit</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Tabs */}
      <div className="flex gap-2">
        <button
          onClick={() => setActiveTab('werbung')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'werbung' 
              ? 'bg-primary text-white' 
              : 'bg-background text-text-secondary hover:bg-border'
          }`}
        >
          📦 Werbung
        </button>
        <button
          onClick={() => setActiveTab('rechnungen')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'rechnungen' 
              ? 'bg-primary text-white' 
              : 'bg-background text-text-secondary hover:bg-border'
          }`}
        >
          🧾 Rechnungen
        </button>
      </div>

      {/* Tab Content */}
      <Card>
        <CardHeader>
          <CardTitle>
            {activeTab === 'werbung' ? '📦 Werbung PDFs' : '🧾 Rechnungen'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-text-secondary">
            {activeTab === 'werbung' 
              ? 'Amazon Advertising Rechnungen hochladen und verarbeiten' 
              : 'Standard-Rechnungen hochladen und verarbeiten'}
          </p>

          {/* Upload Zone */}
          <div 
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
              isDragging ? 'border-primary bg-primary-light' : 'border-border hover:border-primary'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              multiple
              className="hidden"
              onChange={handleFileSelect}
            />
            
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-background flex items-center justify-center">
              <Upload className="w-8 h-8 text-text-secondary" />
            </div>
            
            <p className="text-text mb-2">
              PDFs hier ablegen oder klicken zum Auswählen
            </p>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="space-y-2">
              {files.map((file, index) => (
                <div 
                  key={index}
                  className="flex items-center gap-3 p-3 bg-background rounded-lg"
                >
                  <FileText className="w-5 h-5 text-danger" />
                  <span className="flex-1 text-sm text-text">{file.name}</span>
                  <span className="text-xs text-text-secondary">
                    {formatFileSize(file.size)}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-2">
            <Button 
              variant="primary" 
              onClick={handleUpload}
              disabled={files.length === 0}
            >
              📤 Hochladen
            </Button>
            
            {activeTab === 'werbung' && (
              <Button 
                variant="secondary" 
                onClick={handleExtract}
                disabled={files.length === 0}
              >
                ✂️ Extrahieren
              </Button>
            )}
            
            <Button 
              variant="secondary" 
              onClick={handleProcess}
              disabled={files.length === 0}
            >
              ⚙️ Verarbeiten
            </Button>
            
            <Button 
              variant="primary" 
              onClick={handleDownload}
              disabled={files.length === 0}
            >
              💾 Excel Download
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Logs Section */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>📋 Logs</CardTitle>
          <Button variant="secondary" size="sm" onClick={() => refetchLogs()}>
            🔄 Refresh
          </Button>
        </CardHeader>
        <CardContent>
          <div className="bg-background rounded-lg border border-border max-h-80 overflow-y-auto p-3 font-mono text-xs">
            {logsLoading ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner size="lg" />
              </div>
            ) : filteredLogs.length > 0 ? (
              <pre className="whitespace-pre-wrap text-text">
                {filteredLogs.map(formatLogEntry).join('\n')}
              </pre>
            ) : (
              <p className="text-text-secondary">
                Noch keine Logs vorhanden. Bitte Dateien hochladen und verarbeiten.
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Cleanup Section */}
      <div>
        <Button variant="danger" onClick={handleCleanup}>
          🗑️ Aufräumen (Alle Dateien löschen)
        </Button>
      </div>
    </div>
  );
}
