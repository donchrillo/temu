import { useState, useRef } from 'react';
import { Upload, Table, Download, RefreshCw } from 'lucide-react';

export function CsvProcessor() {
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
      file => file.name.endsWith('.csv') || file.name.endsWith('.xlsx')
    );
    setFiles(prev => [...prev, ...droppedFiles]);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      setFiles(prev => [...prev, ...selectedFiles]);
    }
  };

  const processFiles = () => {
    // TODO: Implement file processing
    console.log('Processing files:', files);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-text mb-2">CSV Verarbeiter</h1>
        <p className="text-text-secondary">Amazon DATEV Export & JTL Mapping</p>
      </div>

      {/* Upload Zone */}
      <div 
        className={`bg-card border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging ? 'border-primary bg-primary-light' : 'border-border'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx"
          multiple
          className="hidden"
          onChange={handleFileSelect}
        />
        
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-success/10 flex items-center justify-center">
          <Upload className="w-8 h-8 text-success" />
        </div>
        
        <h3 className="text-lg font-semibold text-text mb-2">
          CSV-/Excel-Dateien hier ablegen
        </h3>
        <p className="text-text-secondary mb-4">
          Unterstützte Formate: .csv, .xlsx
        </p>
        
        <button 
          onClick={() => fileInputRef.current?.click()}
          className="py-2 px-4 bg-success text-white rounded-md hover:bg-success-hover transition-colors"
        >
          Dateien auswählen
        </button>
      </div>

      {/* Selected Files */}
      {files.length > 0 && (
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-text">
              Ausgewählte Dateien ({files.length})
            </h2>
            <button 
              onClick={processFiles}
              className="py-2 px-4 bg-success text-white rounded-md hover:bg-success-hover transition-colors flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Verarbeiten
            </button>
          </div>

          <div className="space-y-2">
            {files.map((file, index) => (
              <div 
                key={index}
                className="flex items-center gap-3 p-3 bg-background rounded-lg"
              >
                <Table className="w-5 h-5 text-success" />
                <span className="flex-1 text-sm text-text">{file.name}</span>
                <span className="text-xs text-text-secondary">
                  {(file.size / 1024).toFixed(1)} KB
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Processing Options */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-lg font-semibold text-text mb-4">Verarbeitungsoptionen</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <label className="flex items-center gap-3 p-3 bg-background rounded-lg cursor-pointer hover:bg-border/50">
            <input type="checkbox" defaultChecked className="w-4 h-4" />
            <div>
              <div className="font-medium text-text">OrderID Mapping</div>
              <div className="text-xs text-text-secondary">Bestellnummern zuordnen</div>
            </div>
          </label>
          
          <label className="flex items-center gap-3 p-3 bg-background rounded-lg cursor-pointer hover:bg-border/50">
            <input type="checkbox" defaultChecked className="w-4 h-4" />
            <div>
              <div className="font-medium text-text">DATEV Export</div>
              <div className="text-xs text-text-secondary">Für Buchhaltung</div>
            </div>
          </label>
          
          <label className="flex items-center gap-3 p-3 bg-background rounded-lg cursor-pointer hover:bg-border/50">
            <input type="checkbox" defaultChecked className="w-4 h-4" />
            <div>
              <div className="font-medium text-text">Excel Reports</div>
              <div className="text-xs text-text-secondary">Zusammenfassung</div>
            </div>
          </label>
        </div>
      </div>

      {/* Recent Exports */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-text">Letzte Exporte</h2>
        </div>
        <div className="text-center py-8 text-text-secondary">
          <Download className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p>Keine Exporte vorhanden</p>
        </div>
      </div>
    </div>
  );
}