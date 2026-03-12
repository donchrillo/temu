export interface FileInfo {
  name: string;
  size: number;
  modified: string;
}

export interface FileListResponse {
  files: FileInfo[];
}

export interface ConvertTotals {
  orders?: number;
  bookings?: number;
  skipped?: number;
  ignored?: number;
  transactions?: number;
}

export interface ConvertFileDetail {
  filename: string;
  records: number;
  bookings: number;
  skipped: number;
  ignored: number;
}

export interface ConvertIgnoredRow {
  filename: string;
  bestellnummer: string;
  rechnungsnummer: string;
  verkaufsart: string;
  grund: string;
}

export interface ConvertDetails {
  mode: 'orders' | 'payments';
  files: ConvertFileDetail[];
  notes: string[];
  ignored_rows: ConvertIgnoredRow[];
}

export interface ConvertResponse {
  status: string;
  message: string;
  processed_files: string[];
  totals: ConvertTotals;
  output_files: string[];
  details?: ConvertDetails;
}

export interface OffenerPosten {
  belegfeld1: string;
  saldo: number;
}

export interface OpSummary {
  ausgeglichen_count: number;
  bestellungen_ohne_zahlung: number;
  zahlungen_ohne_bestellung: number;
  gesamt_offen_eur: number;
  ohne_op_count: number;
  top_offen: OffenerPosten[];
}

export interface OpAnalysisResponse {
  status: string;
  message: string;
  output_files: string[];
  summary?: OpSummary;
}
