import { useState } from 'react';
import { Play, RefreshCw, Package } from 'lucide-react';

export function TemuInventory() {
  const [isLoading, setIsLoading] = useState(false);

  const handleInventorySync = async () => {
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => setIsLoading(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-text mb-2">TEMU Inventar</h1>
        <p className="text-text-secondary">Inventory Sync & Bestandsverwaltung</p>
      </div>

      {/* Manual Triggers */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-lg font-semibold text-text mb-2">Manual Triggers</h2>
        <p className="text-sm text-text-secondary mb-6">Start Workflows manuell</p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Inventory Sync Card */}
          <div className="bg-background rounded-lg p-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-success flex items-center justify-center text-white">
                <Package className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-text">Inventory Sync</h3>
                <p className="text-xs text-text-secondary">4-Step Workflow</p>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-2 mb-4">
              <span className="px-2 py-1 bg-card text-xs rounded">1️⃣ Download</span>
              <span className="px-2 py-1 bg-card text-xs rounded">2️⃣ Fetch</span>
              <span className="px-2 py-1 bg-card text-xs rounded">3️⃣ Compare</span>
              <span className="px-2 py-1 bg-card text-xs rounded">4️⃣ Push</span>
            </div>

            <button 
              onClick={handleInventorySync}
              disabled={isLoading}
              className="w-full py-2 px-4 bg-success text-white rounded-md hover:bg-success-hover transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isLoading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              <span>Start Inventory Sync</span>
            </button>
          </div>

          {/* Quick Stats */}
          <div className="bg-background rounded-lg p-4">
            <h3 className="font-semibold text-text mb-3">Aktuelle Statistiken</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-text-secondary">Artikel gesamt</span>
                <span className="font-semibold">0</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-text-secondary">Niedriger Bestand</span>
                <span className="font-semibold text-warning">0</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-text-secondary">Letzte Sync</span>
                <span className="font-semibold">-</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Inventory Table Placeholder */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-text">Inventar Übersicht</h2>
          <button className="py-1 px-3 bg-secondary text-white text-sm rounded-md hover:bg-secondary-hover transition-colors flex items-center gap-2">
            <RefreshCw className="w-3 h-3" />
            Refresh
          </button>
        </div>
        <div className="text-center py-8 text-text-secondary">
          <Package className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p>Keine Inventardaten vorhanden</p>
        </div>
      </div>
    </div>
  );
}