import { useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ordersApi, inventoryApi, jobsApi, logsApi } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/shared/loading-spinner';
import { EmptyState } from '@/components/shared/empty-state';
import { StatsCard } from '@/components/shared/stats-card';
import {
  ShoppingCart,
  ClipboardList,
  Package,
  Activity,
  RefreshCw,
  AlertCircle,
  Info,
} from 'lucide-react';

export default function Dashboard() {
  const queryClient = useQueryClient();

  // ============ Queries ============
  const { data: ordersData, isLoading: ordersLoading } = useQuery({
    queryKey: ['orders'],
    queryFn: ordersApi.getAll,
    retry: 1,
  });

  const { data: inventoryData, isLoading: inventoryLoading } = useQuery({
    queryKey: ['inventory'],
    queryFn: inventoryApi.getAll,
    retry: 1,
  });

  const { data: jobsData, isLoading: jobsLoading } = useQuery({
    queryKey: ['jobs'],
    queryFn: jobsApi.getAll,
    retry: 1,
  });

  const { data: logsData, isLoading: logsLoading } = useQuery({
    queryKey: ['logs'],
    queryFn: () => logsApi.getRecent(10),
    retry: 1,
  });

  // ============ Mutations ============
  const syncOrdersMutation = useMutation({
    mutationFn: (verbose: boolean) => ordersApi.sync(verbose),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });

  const syncInventoryMutation = useMutation({
    mutationFn: (verbose: boolean) => inventoryApi.sync(verbose),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    },
  });

  // ============ Stats berechnen ============
  const stats = useMemo(() => {
    const orders = ordersData || [];
    const inventory = inventoryData || [];
    const jobs = jobsData || [];

    // Heutige Bestellungen
    const today = new Date().toISOString().split('T')[0];
    const ordersToday = orders.filter(
      (o: any) => o.kaufdatum && o.kaufdatum.startsWith(today)
    ).length;

    // Offene Bestellungen
    const pendingOrders = orders.filter((o: any) => o.status === 'pending').length;

    // Inventar
    const inventoryItems = inventory.length;

    // Aktive Jobs
    const activeJobs = jobs.filter((j: any) => j.enabled).length;

    return {
      ordersToday,
      pendingOrders,
      inventoryItems,
      activeJobs,
    };
  }, [ordersData, inventoryData, jobsData]);

  // ============ Handler ============
  const handleSyncOrders = () => {
    syncOrdersMutation.mutate(false);
  };

  const handleSyncInventory = () => {
    syncInventoryMutation.mutate(false);
  };

  const isSyncingOrders = syncOrdersMutation.isPending;
  const isSyncingInventory = syncInventoryMutation.isPending;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text">Dashboard</h1>
        <p className="text-text-secondary">Übersicht über Ihr TEMU ERP System</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Bestellungen heute"
          value={stats.ordersToday}
          icon={<ShoppingCart className="w-6 h-6" />}
          iconBgColor="bg-blue-100 text-blue-600"
          isLoading={ordersLoading}
        />
        <StatsCard
          title="Offene Bestellungen"
          value={stats.pendingOrders}
          icon={<ClipboardList className="w-6 h-6" />}
          iconBgColor="bg-orange-100 text-orange-600"
          isLoading={ordersLoading}
        />
        <StatsCard
          title="Inventar-Positionen"
          value={stats.inventoryItems}
          icon={<Package className="w-6 h-6" />}
          iconBgColor="bg-green-100 text-green-600"
          isLoading={inventoryLoading}
        />
        <StatsCard
          title="Aktive Jobs"
          value={stats.activeJobs}
          icon={<Activity className="w-6 h-6" />}
          iconBgColor="bg-purple-100 text-purple-600"
          isLoading={jobsLoading}
        />
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Schnellaktionen</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button
            variant="primary"
            onClick={handleSyncOrders}
            loading={isSyncingOrders}
            disabled={isSyncingOrders}
          >
            <RefreshCw className={`w-4 h-4 ${isSyncingOrders ? 'animate-spin' : ''}`} />
            Bestellungen synchronisieren
          </Button>
          <Button
            variant="secondary"
            onClick={handleSyncInventory}
            loading={isSyncingInventory}
            disabled={isSyncingInventory}
          >
            <RefreshCw className={`w-4 h-4 ${isSyncingInventory ? 'animate-spin' : ''}`} />
            Inventar synchronisieren
          </Button>
        </CardContent>
      </Card>

      {/* Letzte Aktivitäten / Logs */}
      <Card>
        <CardHeader>
          <CardTitle>Letzte Aktivitäten</CardTitle>
        </CardHeader>
        <CardContent>
          {logsLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner size="lg" />
            </div>
          ) : logsData && logsData.length > 0 ? (
            <div className="space-y-3">
              {logsData.slice(0, 8).map((log: any) => (
                <LogEntryRow key={log.id} log={log} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon="stats"
              title="Keine Aktivitäten"
              description="Es wurden noch keine Logs aufgezeichnet."
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ============ Log Entry Row Component ============
interface LogEntryRowProps {
  log: {
    id: number;
    job_id: string;
    component: string;
    level: 'INFO' | 'WARNING' | 'ERROR';
    message: string;
    timestamp: string;
  };
}

function LogEntryRow({ log }: LogEntryRowProps) {
  const levelConfig = {
    INFO: { icon: Info, color: 'text-blue-500', bg: 'bg-blue-50' },
    WARNING: { icon: AlertCircle, color: 'text-orange-500', bg: 'bg-orange-50' },
    ERROR: { icon: AlertCircle, color: 'text-red-500', bg: 'bg-red-50' },
  };

  const config = levelConfig[log.level];
  const Icon = config.icon;

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return timestamp;
    }
  };

  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg ${config.bg}`}>
      <Icon className={`w-4 h-4 mt-0.5 ${config.color}`} />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-text">{log.message}</p>
        <div className="flex items-center gap-2 mt-1 text-xs text-text-secondary">
          <span className="font-medium">{log.component}</span>
          <span>•</span>
          <span>{log.job_id}</span>
          <span>•</span>
          <span>{formatTimestamp(log.timestamp)}</span>
        </div>
      </div>
    </div>
  );
}
