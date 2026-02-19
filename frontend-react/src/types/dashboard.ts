/**
 * Dashboard TypeScript Interfaces
 * Type definitions for TEMU stats, jobs, and logs
 */

export interface Stats {
  orders: {
    total: number;
    imported: number;
    xml_generated: number;
    uploaded: number;
    tracked: number;
  };
  inventory: {
    total_skus: number;
    synced: number;
    pending: number;
    errors: number;
  };
  last_sync: {
    orders: string | null;
    inventory: string | null;
  };
}

export interface Job {
  job_id: string;
  job_type: string;
  enabled: boolean;
  schedule?: string;
  config?: JobConfig;
  status?: JobStatus;
  recent_logs?: JobLog[];
}

export interface JobConfig {
  job_type: string;
  schedule: {
    interval_minutes: number;
    enabled: boolean;
  };
  description?: string;
}

export interface JobStatus {
  status: 'success' | 'running' | 'error' | 'idle';
  last_run: string;
  next_run: string | null;
  last_error: string | null;
  last_duration: number;
}

export interface JobLog {
  log_id: number;
  job_id: string;
  job_type: string;
  level: LogLevel;
  message: string;
  timestamp: string;
  duration_seconds: number | null;
  status: string | null;
  error_text: string | null;
}

export type LogLevel = 'INFO' | 'WARNING' | 'ERROR';

export interface LogEntry {
  id: number;
  job_id: string;
  component: string;
  level: LogLevel;
  message: string;
  timestamp: string;
  duration_ms?: number;
  error_text?: string;
}

export interface DashboardStats {
  ordersToday: number;
  pendingOrders: number;
  inventoryItems: number;
  activeJobs: number;
}

export interface SyncResponse {
  status: string;
  workflow: string;
  params: Record<string, unknown>;
  message: string;
}

// Order types
export interface Order {
  id: number;
  bestell_id: string;
  kaufdatum: string;
  status: string;
  kunde_name: string;
  summe: number;
  lieferadresse?: {
    name: string;
    strasse: string;
    plz: string;
    ort: string;
    land: string;
  };
}

// Inventory types
export interface InventoryItem {
  id: number;
  sku: string;
  name: string;
  bestand: number;
  reserviert: number;
  verfuegbar: number;
}
