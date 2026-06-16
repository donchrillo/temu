import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ShoppingCart, Package, Clock, Play } from 'lucide-react';
import { jobsApi, logsApi } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/shared/loading-spinner';
import { Dialog } from '@/components/ui/dialog';

// Status-Optionen für Order Sync
const ORDER_STATUS_OPTIONS = [
  { value: 2, label: '2 - UN_SHIPPING (nicht versendet)' },
  { value: 3, label: '3 - CANCELLED (storniert)' },
  { value: 4, label: '4 - SHIPPED (versendet)' },
  { value: 5, label: '5 - RECEIPTED (Order received)' },
];

export function TemuOrders() {
  const queryClient = useQueryClient();
  const [logFilter, setLogFilter] = useState('temu');
  
  // Dialog states
  const [showOrderDialog, setShowOrderDialog] = useState(false);
  const [showInventoryDialog, setShowInventoryDialog] = useState(false);
  
  // Order sync params
  const [orderStatus, setOrderStatus] = useState(2);
  const [orderDays, setOrderDays] = useState(7);
  const [orderVerbose, setOrderVerbose] = useState(false);
  
  // Inventory sync params
  const [inventoryMode, setInventoryMode] = useState('quick');
  const [inventoryVerbose, setInventoryVerbose] = useState(false);

  // ============ Jobs Query ============
  const { data: jobsData, isLoading: jobsLoading } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => jobsApi.getAll(),
    retry: 1,
    refetchInterval: (q) => {
      const jobs: any[] = q.state.data || [];
      return jobs.some((j: any) => j.status?.status === 'running') ? 2000 : false;
    },
  });

  // ============ Logs Query ============
  const { data: logsData, isLoading: logsLoading, refetch: refetchLogs } = useQuery({
    queryKey: ['logs', logFilter],
    queryFn: () => logsApi.getRecent(50),
    retry: 1,
    refetchInterval: () => {
      const jobs: any[] = jobsData || [];
      return jobs.some((j: any) => j.status?.status === 'running') ? 2000 : false;
    },
  });

  // ============ Mutations ============
  const triggerJobMutation = useMutation({
    mutationFn: async ({ jobType, params }: { jobType: string; params?: Record<string, any> }) => {
      const jobs = jobsData || [];
      const job = jobs.find((j: any) => j.config?.job_type === jobType);
      if (!job) throw new Error(`Job ${jobType} nicht gefunden`);
      return jobsApi.trigger(job.job_id, params);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['logs'] });
    },
  });

  const toggleJobMutation = useMutation({
    mutationFn: async ({ jobId, enabled }: { jobId: string; enabled: boolean }) => {
      return jobsApi.toggle(jobId, enabled);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });

  const updateScheduleMutation = useMutation({
    mutationFn: async ({ jobId, interval }: { jobId: string; interval: number }) => {
      return jobsApi.updateSchedule(jobId, interval);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });

  const isTriggering = triggerJobMutation.isPending;

  const jobs = jobsData || [];
  const logs = logsData || [];

  const temuJobs = jobs.filter((j: any) => 
    j.config?.job_type === 'sync_orders' || 
    j.config?.job_type === 'sync_inventory'
  );

  // ============ Handler Functions ============
  const handleRunNow = (jobType: string) => {
    if (jobType === 'sync_orders') {
      setShowOrderDialog(true);
    } else {
      setShowInventoryDialog(true);
    }
  };

  const handleConfirmOrderSync = () => {
    triggerJobMutation.mutate({ 
      jobType: 'sync_orders',
      params: { 
        parent_order_status: orderStatus, 
        days_back: orderDays,
        verbose: orderVerbose 
      }
    });
    setShowOrderDialog(false);
  };

  const handleConfirmInventorySync = () => {
    triggerJobMutation.mutate({ 
      jobType: 'sync_inventory',
      params: { 
        mode: inventoryMode,
        verbose: inventoryVerbose 
      }
    });
    setShowInventoryDialog(false);
  };

  const handleToggleJob = (job: any) => {
    const enabled = !job.config?.schedule?.enabled;
    toggleJobMutation.mutate({ jobId: job.job_id, enabled });
  };

  const handleUpdateInterval = (job: any) => {
    const currentInterval = job.config?.schedule?.interval_minutes || 15;
    const newInterval = prompt(`Neues Intervall in Minuten (aktuell: ${currentInterval} Min):`, String(currentInterval));
    if (!newInterval || newInterval === '') return;
    const interval = parseInt(newInterval);
    if (isNaN(interval) || interval < 1) {
      alert('Ungültiges Intervall! Bitte eine Zahl >= 1 eingeben.');
      return;
    }
    updateScheduleMutation.mutate({ jobId: job.job_id, interval });
  };

  // Format log entry like old frontend
  const formatLogEntry = (log: any) => {
    const timestamp = log.timestamp 
      ? new Date(log.timestamp).toLocaleString('de-DE')
      : '-';
    return `[${timestamp}] [${log.level}] ${log.message}`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-text">TEMU Integration</h1>
        <p className="text-text-secondary">Marktplatz-Anbindung</p>
      </div>

      {/* === SCHEDULED JOBS === */}
      <section>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>⚙️ Scheduled Jobs</CardTitle>
            <Button 
              variant="secondary" 
              size="sm"
              onClick={() => queryClient.invalidateQueries({ queryKey: ['jobs'] })}
            >
              🔄 Refresh
            </Button>
          </CardHeader>
          <CardContent>
            {jobsLoading ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner size="lg" />
              </div>
            ) : temuJobs.length > 0 ? (
              <div className="space-y-2">
                {temuJobs.map((job: any) => {
                  const isEnabled = job.config?.schedule?.enabled;
                  const interval = job.config?.schedule?.interval_minutes;
                  const status = job.status?.status;
                  const lastRun = job.status?.last_run 
                    ? new Date(job.status.last_run).toLocaleString('de-DE')
                    : 'Nie';
                  const nextRun = job.status?.next_run 
                    ? new Date(job.status.next_run).toLocaleString('de-DE')
                    : '-';
                  const isOrders = job.config?.job_type === 'sync_orders';

                  return (
                    <div key={job.job_id} className="flex items-center justify-between p-3 bg-background rounded-lg border border-border">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-white ${
                          isOrders ? 'bg-primary' : 'bg-success'
                        }`}>
                          {isOrders ? <ShoppingCart className="w-5 h-5" /> : <Package className="w-5 h-5" />}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-sm">
                              {isEnabled ? '✅' : '⏸️'} {job.config?.job_type}
                            </span>
                          </div>
                          <p className="text-xs text-text-secondary">
                            Intervall: {interval}min | Letzter: {lastRun} | Nächster: {nextRun}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          status === 'success' ? 'bg-green-100 text-green-700' :
                          status === 'running' ? 'bg-blue-100 text-blue-700' :
                          status === 'error' || status === 'failed' ? 'bg-red-100 text-red-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {status || 'idle'}
                        </span>
                        <Button 
                          variant="primary"
                          size="sm"
                          onClick={() => handleRunNow(job.config?.job_type)}
                          title="Jetzt ausführen"
                          disabled={isTriggering}
                        >
                          <Play className="w-3 h-3" />
                        </Button>
                        <Button 
                          variant="secondary" 
                          size="sm"
                          onClick={() => handleUpdateInterval(job)}
                          title="Intervall ändern"
                        >
                          <Clock className="w-3 h-3" />
                        </Button>
                        <Button 
                          variant={isEnabled ? 'primary' : 'secondary'}
                          size="sm"
                          onClick={() => handleToggleJob(job)}
                          title={isEnabled ? 'Deaktivieren' : 'Aktivieren'}
                        >
                          {isEnabled ? '✓' : '✗'}
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-center py-8 text-text-secondary">Keine TEMU Jobs konfiguriert</p>
            )}
          </CardContent>
        </Card>
      </section>

      {/* === RECENT LOGS === */}
      <section>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>📋 Recent Logs</CardTitle>
            <Button 
              variant="secondary" 
              size="sm"
              onClick={() => refetchLogs()}
            >
              🔄 Refresh
            </Button>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2 mb-4">
              <select 
                value={logFilter}
                onChange={(e) => setLogFilter(e.target.value)}
                className="px-3 py-2 bg-background border border-border rounded-md text-sm"
              >
                <option value="temu">Alle TEMU Jobs</option>
                <option value="sync_orders">Order Sync</option>
                <option value="sync_inventory">Inventory Sync</option>
              </select>
            </div>

            <div className="bg-background rounded-lg border border-border max-h-80 overflow-y-auto p-3 font-mono text-xs">
              {logsLoading ? (
                <div className="flex justify-center py-8">
                  <LoadingSpinner size="lg" />
                </div>
              ) : logs.length > 0 ? (
                <pre className="whitespace-pre-wrap text-text">{logs.map(formatLogEntry).join('\n')}</pre>
              ) : (
                <p className="text-text-secondary">Keine Logs verfügbar</p>
              )}
            </div>
          </CardContent>
        </Card>
      </section>

      {/* === ORDER SYNC DIALOG === */}
      <Dialog 
        open={showOrderDialog} 
        onClose={() => setShowOrderDialog(false)}
        title="⚙️ Order Sync Parameter"
      >
        <div className="space-y-4">
          {/* Status Select */}
          <div>
            <label className="block text-sm font-medium text-text mb-1">
              📊 Status:
            </label>
            <select
              value={orderStatus}
              onChange={(e) => setOrderStatus(Number(e.target.value))}
              className="w-full px-3 py-2 bg-background border border-border rounded-md text-sm"
            >
              {ORDER_STATUS_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          {/* Days Input */}
          <div>
            <label className="block text-sm font-medium text-text mb-1">
              📅 Tage zurück:
            </label>
            <input
              type="number"
              min={1}
              max={365}
              value={orderDays}
              onChange={(e) => setOrderDays(Number(e.target.value))}
              className="w-full px-3 py-2 bg-background border border-border rounded-md text-sm"
            />
            <p className="text-xs text-text-secondary mt-1">
              Wie viele Tage in die Vergangenheit sollen Orders gesucht werden?
            </p>
          </div>

          {/* Verbose Checkbox */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="order-verbose"
              checked={orderVerbose}
              onChange={(e) => setOrderVerbose(e.target.checked)}
              className="w-4 h-4"
            />
            <label htmlFor="order-verbose" className="text-sm text-text">
              📝 Detailliertes Logging (Verbose Mode)
            </label>
          </div>

          {/* Buttons */}
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="secondary" onClick={() => setShowOrderDialog(false)}>
              Abbrechen
            </Button>
            <Button variant="primary" onClick={handleConfirmOrderSync}>
              Starten
            </Button>
          </div>
        </div>
      </Dialog>

      {/* === INVENTORY SYNC DIALOG === */}
      <Dialog 
        open={showInventoryDialog} 
        onClose={() => setShowInventoryDialog(false)}
        title="⚙️ Inventory Sync Parameter"
      >
        <div className="space-y-4">
          {/* Mode Select */}
          <div>
            <label className="block text-sm font-medium text-text mb-1">
              🔄 Sync-Modus:
            </label>
            <select
              value={inventoryMode}
              onChange={(e) => setInventoryMode(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-md text-sm"
            >
              <option value="quick">Quick (Nur Bestand aktualisieren)</option>
              <option value="full">Full (Alle SKUs neu laden)</option>
            </select>
          </div>

          {/* Verbose Checkbox */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="inventory-verbose"
              checked={inventoryVerbose}
              onChange={(e) => setInventoryVerbose(e.target.checked)}
              className="w-4 h-4"
            />
            <label htmlFor="inventory-verbose" className="text-sm text-text">
              📝 Detailliertes Logging (Verbose Mode)
            </label>
          </div>

          {/* Buttons */}
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="secondary" onClick={() => setShowInventoryDialog(false)}>
              Abbrechen
            </Button>
            <Button variant="primary" onClick={handleConfirmInventorySync}>
              Starten
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
