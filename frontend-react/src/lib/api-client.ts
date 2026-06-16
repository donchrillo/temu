import axios from 'axios';
import type { Stats, Job, LogEntry, SyncResponse, Order, InventoryItem } from '@/types/dashboard';

// Use Vite proxy - requests to /api will be forwarded to backend
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
  timeout: 30000,
});

// ============ TEMU STATS API ============
export const statsApi = {
  get: (): Promise<Stats> => 
    apiClient.get('/api/temu/stats').then(res => res.data),
};

// ============ TEMU ORDERS API ============
export const ordersApi = {
  getAll: (): Promise<Order[]> => 
    apiClient.get('/api/temu/orders').then(res => res.data),
  
  // Trigger via jobs endpoint
  sync: (verbose: boolean = false, daysBack: number = 7): Promise<SyncResponse> => 
    apiClient.post(`/api/jobs/sync_orders/run-now?verbose=${verbose}&days_back=${daysBack}`).then(res => res.data),
};

// ============ TEMU INVENTORY API ============
export const inventoryApi = {
  getAll: (): Promise<InventoryItem[]> => 
    apiClient.get('/api/temu/inventory').then(res => res.data),
  
  // Trigger via jobs endpoint
  sync: (verbose: boolean = false, mode: 'quick' | 'full' = 'quick'): Promise<SyncResponse> => 
    apiClient.post(`/api/jobs/sync_inventory/run-now?verbose=${verbose}&mode=${mode}`).then(res => res.data),
};

// ============ JOBS API ============
export const jobsApi = {
  getAll: (): Promise<Job[]> => 
    apiClient.get('/api/jobs').then(res => res.data),
  
  getById: (jobId: string): Promise<Job> => 
    apiClient.get(`/api/jobs/${jobId}`).then(res => res.data),
  
  trigger: (jobId: string, params?: Record<string, any>): Promise<any> => {
    const qs = params
      ? '?' + new URLSearchParams(Object.fromEntries(Object.entries(params).map(([k, v]) => [k, String(v)]))).toString()
      : '';
    return apiClient.post(`/api/jobs/${jobId}/run-now${qs}`).then(res => res.data);
  },
  
  toggle: (jobId: string, enabled: boolean): Promise<Job> => 
    apiClient.post(`/api/jobs/${jobId}/toggle?enabled=${enabled}`).then(res => res.data),
  
  updateSchedule: (jobId: string, intervalMinutes: number): Promise<any> => 
    apiClient.post(`/api/jobs/${jobId}/schedule?interval_minutes=${intervalMinutes}`).then(res => res.data),
};

// ============ LOGS API ============
export const logsApi = {
  getRecent: (limit: number = 20): Promise<LogEntry[]> => 
    apiClient.get(`/api/logs?limit=${limit}`).then(res => res.data),
  
  getByJobId: (jobId: string, limit: number = 20): Promise<LogEntry[]> => 
    apiClient.get(`/api/logs?job_id=${jobId}&limit=${limit}`).then(res => res.data),
};

// ============ CSV API ============
export interface CsvReport {
  filename: string;
  sheets: Record<string, Record<string, string>[]>;
}

export interface CsvStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  job_id: string;
  error?: string;
  progress?: number;
}

export interface CsvExportParams {
  csv_files: string[];
  zip_name: string;
  include_report: boolean;
  include_log: boolean;
}

export interface CsvExportResponse {
  zip_filename: string;
  download_url: string;
}

export interface CsvCleanupResponse {
  deleted: number;
  errors: string[];
}

export interface CsvLogEntry {
  timestamp: string;
  level: string;
  job_type: string;
  message: string;
}

export const csvApi = {
  upload: async (file: File): Promise<{ job_id: string }> => {
    const formData = new FormData();
    formData.append('files', file);
    return apiClient.post('/api/csv/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(res => res.data);
  },

  process: (jobId: string, skipCritical: boolean = false): Promise<any> => {
    return apiClient.post(`/api/csv/process?job_id=${jobId}&skip_critical=${skipCritical}`);
  },

  getStatus: (jobId: string): Promise<CsvStatus> => {
    return apiClient.get(`/api/csv/status/${jobId}`).then(res => res.data);
  },

  getLatestReport: (): Promise<CsvReport | { filename?: never }> => {
    return apiClient.get('/api/csv/report/latest').then(res => res.data);
  },

  listProcessedFiles: (): Promise<{ files: string[] }> => {
    return apiClient.get('/api/csv/list-processed-files').then(res => res.data);
  },

  createExportZip: (params: CsvExportParams): Promise<CsvExportResponse> => {
    return apiClient.post('/api/csv/create-export-zip', params).then(res => res.data);
  },

  getLogs: (prefix: string = 'csv', limit: number = 200): Promise<{ logs: CsvLogEntry[]; prefix: string }> => {
    return apiClient.get(`/api/csv/logs/db?prefix=${prefix}&limit=${limit}`).then(res => res.data);
  },

  cleanupAll: (): Promise<CsvCleanupResponse> => {
    return apiClient.post('/api/csv/cleanup-all').then(res => res.data);
  },
};

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error(`[API] Error ${error.response.status}:`, error.response.data);
    } else if (error.request) {
      console.error('[API] No response received:', error.message);
    } else {
      console.error('[API] Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
