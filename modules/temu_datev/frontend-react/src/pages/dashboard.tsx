import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  filesApi,
  convertApi,
  opApi,
  exportsApi,
  apiClient,
} from '@/lib/api-client';
import type { ConvertResponse, FileInfo, OpAnalysisResponse } from '@/types/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog } from '@/components/ui/dialog';
import { LoadingSpinner } from '@/components/shared/loading-spinner';
import { EmptyState } from '@/components/shared/empty-state';
import { StatsCard } from '@/components/shared/stats-card';
import {
  UploadCloud,
  FileText,
  Banknote,
  Download,
  FolderOpen,
  ClipboardList,
  BarChart3,
  RefreshCw,
  CircleCheck,
  AlertTriangle,
} from 'lucide-react';

interface ActionState {
  title: string;
  message: string;
  variant: 'success' | 'warning' | 'error';
}

type EditableFileType = 'orders' | 'payments';

export default function Dashboard() {
  const queryClient = useQueryClient();
  const [selectedOrders, setSelectedOrders] = useState<string[]>([]);
  const [selectedPayments, setSelectedPayments] = useState<string[]>([]);
  const [lastAction, setLastAction] = useState<ActionState | null>(null);
  const [opResult, setOpResult] = useState<OpAnalysisResponse | null>(null);
  const [convertResult, setConvertResult] = useState<ConvertResponse | null>(null);
  const [opDialogOpen, setOpDialogOpen] = useState(false);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editorType, setEditorType] = useState<EditableFileType>('orders');
  const [editorFilename, setEditorFilename] = useState('');
  const [editorContent, setEditorContent] = useState('');
  const [editorLoading, setEditorLoading] = useState(false);
  const [editorSaving, setEditorSaving] = useState(false);
  const [exportPreviewOpen, setExportPreviewOpen] = useState(false);
  const [exportPreviewFilename, setExportPreviewFilename] = useState('');
  const [exportPreviewContent, setExportPreviewContent] = useState('');
  const [exportPreviewLoading, setExportPreviewLoading] = useState(false);

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.get('/api/health').then((res) => res.data),
    retry: 1,
  });

  const { data: ordersData, isLoading: ordersLoading } = useQuery({
    queryKey: ['order-files'],
    queryFn: filesApi.listOrders,
    retry: 1,
  });

  const { data: paymentsData, isLoading: paymentsLoading } = useQuery({
    queryKey: ['payment-files'],
    queryFn: filesApi.listPayments,
    retry: 1,
  });

  const { data: exportsData, isLoading: exportsLoading } = useQuery({
    queryKey: ['exports'],
    queryFn: exportsApi.list,
    retry: 1,
  });

  const uploadOrderMutation = useMutation({
    mutationFn: filesApi.uploadOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['order-files'] });
    },
  });

  const uploadPaymentMutation = useMutation({
    mutationFn: filesApi.uploadPayment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payment-files'] });
    },
  });

  const convertOrdersMutation = useMutation({
    mutationFn: () => convertApi.orders(selectedOrders),
    onSuccess: (data) => {
      setConvertResult(data);
      setLastAction({
        title: 'Bestellberichte konvertiert',
        message: `${data.totals.orders ?? 0} Bestellungen, ${data.totals.bookings ?? 0} Buchungen, ${data.totals.skipped ?? 0} uebersprungen, ${data.totals.ignored ?? 0} ignoriert`,
        variant: 'success',
      });
      setSelectedOrders([]);
      queryClient.invalidateQueries({ queryKey: ['exports'] });
    },
    onError: () => {
      setLastAction({
        title: 'Bestellberichte fehlgeschlagen',
        message: 'Bitte prüfe die ausgewählten Dateien.',
        variant: 'error',
      });
    },
  });

  const convertPaymentsMutation = useMutation({
    mutationFn: () => convertApi.payments(selectedPayments),
    onSuccess: (data) => {
      setConvertResult(data);
      setLastAction({
        title: 'Zahlungsberichte konvertiert',
        message: `${data.totals.transactions ?? 0} Transaktionen, ${data.totals.bookings ?? 0} Buchungen`,
        variant: 'success',
      });
      setSelectedPayments([]);
      queryClient.invalidateQueries({ queryKey: ['exports'] });
    },
    onError: () => {
      setLastAction({
        title: 'Zahlungsberichte fehlgeschlagen',
        message: 'Bitte prüfe die ausgewählten Dateien.',
        variant: 'error',
      });
    },
  });

  const opMutation = useMutation({
    mutationFn: opApi.analyze,
    onSuccess: (data) => {
      setOpResult(data);
      setOpDialogOpen(true);
      const offen = data.summary?.bestellungen_ohne_zahlung ?? 0;
      const saldo = data.summary?.gesamt_offen_eur ?? 0;
      setLastAction({
        title: 'OP-Analyse erstellt',
        message: offen > 0
          ? `${offen} offene Bestellungen · ${formatEur(saldo)}`
          : 'Alle Bestellungen ausgeglichen!',
        variant: offen > 0 ? 'warning' : 'success',
      });
      queryClient.invalidateQueries({ queryKey: ['exports'] });
    },
    onError: () => {
      setLastAction({
        title: 'OP-Analyse fehlgeschlagen',
        message: 'Bitte sicherstellen, dass Bestellungen und Zahlungen exportiert sind.',
        variant: 'warning',
      });
    },
  });

  const stats = useMemo(() => {
    return {
      ordersFiles: ordersData?.files.length ?? 0,
      paymentsFiles: paymentsData?.files.length ?? 0,
      exports: exportsData?.files.length ?? 0,
      selected: selectedOrders.length + selectedPayments.length,
    };
  }, [ordersData, paymentsData, exportsData, selectedOrders, selectedPayments]);

  const handleUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
    uploadFn: (file: File) => Promise<unknown>
  ) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    await uploadFn(file);
    event.target.value = '';
  };

  const openFileEditor = async (type: EditableFileType, filename: string) => {
    setEditorType(type);
    setEditorFilename(filename);
    setEditorOpen(true);
    setEditorLoading(true);
    try {
      const response = type === 'orders'
        ? await filesApi.getOrderContent(filename)
        : await filesApi.getPaymentContent(filename);
      setEditorContent(response.content);
    } catch {
      setEditorContent('');
      setLastAction({
        title: 'Datei konnte nicht geöffnet werden',
        message: `Fehler beim Laden von ${filename}`,
        variant: 'error',
      });
    } finally {
      setEditorLoading(false);
    }
  };

  const saveFileEditor = async () => {
    if (!editorFilename) {
      return;
    }
    setEditorSaving(true);
    try {
      if (editorType === 'orders') {
        await filesApi.saveOrderContent(editorFilename, editorContent);
        queryClient.invalidateQueries({ queryKey: ['order-files'] });
      } else {
        await filesApi.savePaymentContent(editorFilename, editorContent);
        queryClient.invalidateQueries({ queryKey: ['payment-files'] });
      }
      setLastAction({
        title: 'Datei gespeichert',
        message: `${editorFilename} wurde gespeichert.`,
        variant: 'success',
      });
      setEditorOpen(false);
    } catch {
      setLastAction({
        title: 'Speichern fehlgeschlagen',
        message: `Datei ${editorFilename} konnte nicht gespeichert werden.`,
        variant: 'error',
      });
    } finally {
      setEditorSaving(false);
    }
  };

  const openExportPreview = async (filename: string) => {
    setExportPreviewFilename(filename);
    setExportPreviewOpen(true);
    setExportPreviewLoading(true);
    try {
      const response = await exportsApi.getContent(filename);
      setExportPreviewContent(response.content);
    } catch {
      setExportPreviewContent('');
      setLastAction({
        title: 'Export konnte nicht geöffnet werden',
        message: `Fehler beim Laden von ${filename}`,
        variant: 'error',
      });
    } finally {
      setExportPreviewLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#F7F8FB] via-[#F2F2F7] to-[#ECEFF5] text-text">
      <div className="max-w-6xl mx-auto px-4 md:px-6 py-8 space-y-8">
        <header className="space-y-2">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-semibold">TEMU → DATEV Dashboard</h1>
              <p className="text-text-secondary">
                Konvertiere Bestell- und Zahlungsberichte in DATEV-Exporte.
              </p>
            </div>
            <div className="flex items-center gap-2 text-sm text-text-secondary">
              <span className="h-2 w-2 rounded-full bg-success" />
              <span>Backend: {health?.status ?? 'unbekannt'}</span>
            </div>
          </div>
        </header>

        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsCard
            title="Bestellberichte"
            value={stats.ordersFiles}
            icon={<FileText className="w-6 h-6" />}
            iconBgColor="bg-blue-100 text-blue-600"
            isLoading={ordersLoading}
          />
          <StatsCard
            title="Zahlungsberichte"
            value={stats.paymentsFiles}
            icon={<Banknote className="w-6 h-6" />}
            iconBgColor="bg-emerald-100 text-emerald-600"
            isLoading={paymentsLoading}
          />
          <StatsCard
            title="Ausgewählt"
            value={stats.selected}
            icon={<ClipboardList className="w-6 h-6" />}
            iconBgColor="bg-purple-100 text-purple-600"
          />
          <StatsCard
            title="Exporte"
            value={stats.exports}
            icon={<BarChart3 className="w-6 h-6" />}
            iconBgColor="bg-orange-100 text-orange-600"
            isLoading={exportsLoading}
          />
        </section>

        {lastAction && (
          <Card className="border border-border">
            <CardContent className="flex items-start gap-3 p-4">
              {lastAction.variant === 'success' && (
                <CircleCheck className="w-5 h-5 text-success" />
              )}
              {lastAction.variant === 'warning' && (
                <AlertTriangle className="w-5 h-5 text-warning" />
              )}
              {lastAction.variant === 'error' && (
                <AlertTriangle className="w-5 h-5 text-danger" />
              )}
              <div>
                <p className="font-medium text-text">{lastAction.title}</p>
                <p className="text-sm text-text-secondary">{lastAction.message}</p>
              </div>
            </CardContent>
          </Card>
        )}

        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <FileSection
            title="Bestellberichte"
            description="CSV-Dateien mit Bestellungen auswählen oder hochladen."
            files={ordersData?.files ?? []}
            isLoading={ordersLoading}
            selected={selectedOrders}
            onToggle={setSelectedOrders}
            onUpload={(e) => handleUpload(e, uploadOrderMutation.mutateAsync)}
            actionLabel="Bestellberichte konvertieren"
            actionDisabled={selectedOrders.length === 0}
            actionLoading={convertOrdersMutation.isPending}
            onAction={() => convertOrdersMutation.mutate()}
            onEditFile={(filename) => openFileEditor('orders', filename)}
            icon={<FileText className="w-5 h-5" />}
          />

          <FileSection
            title="Zahlungsberichte"
            description="CSV-Dateien mit Zahlungen auswählen oder hochladen."
            files={paymentsData?.files ?? []}
            isLoading={paymentsLoading}
            selected={selectedPayments}
            onToggle={setSelectedPayments}
            onUpload={(e) => handleUpload(e, uploadPaymentMutation.mutateAsync)}
            actionLabel="Zahlungsberichte konvertieren"
            actionDisabled={selectedPayments.length === 0}
            actionLoading={convertPaymentsMutation.isPending}
            onAction={() => convertPaymentsMutation.mutate()}
            onEditFile={(filename) => openFileEditor('payments', filename)}
            icon={<Banknote className="w-5 h-5" />}
          />
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle>OP-Analyse</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-text-secondary">
                Erstellt die Offene-Posten-Analyse basierend auf den letzten DATEV-Exporten.
              </p>
              <Button
                variant="secondary"
                onClick={() => opMutation.mutate()}
                loading={opMutation.isPending}
              >
                <RefreshCw className={`w-4 h-4 ${opMutation.isPending ? 'animate-spin' : ''}`} />
                OP-Analyse starten
              </Button>
              {opResult?.summary && (
                <Button variant="ghost" onClick={() => setOpDialogOpen(true)}>
                  Ergebnis im Popup
                </Button>
              )}
            </CardContent>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Exporte</CardTitle>
            </CardHeader>
            <CardContent>
              {exportsLoading ? (
                <div className="flex justify-center py-6">
                  <LoadingSpinner />
                </div>
              ) : exportsData && exportsData.files.length > 0 ? (
                <div className="space-y-3">
                  {exportsData.files.map((file) => (
                    <div
                      key={file.name}
                      className="flex items-center justify-between gap-3 bg-white/70 border border-border rounded-lg px-4 py-3"
                    >
                      <div>
                        <p className="font-medium text-text">{file.name}</p>
                        <p className="text-xs text-text-secondary">
                          {formatBytes(file.size)} • {formatDate(file.modified)}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => openExportPreview(file.name)}
                        >
                          <FolderOpen className="w-4 h-4" />
                          Öffnen
                        </Button>
                        <a
                          className="inline-flex items-center gap-2 text-sm text-primary hover:text-primary-hover"
                          href={exportsApi.downloadUrl(file.name)}
                        >
                          <Download className="w-4 h-4" />
                          Download
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  icon="stats"
                  title="Noch keine Exporte"
                  description="Sobald Konvertierungen laufen, erscheinen die Exporte hier."
                />
              )}
            </CardContent>
          </Card>
        </section>

        {opResult?.summary && (
          <section>
            <Card>
              <CardHeader>
                <CardTitle>OP-Analyse Ergebnis</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-3 text-center">
                    <p className="text-2xl font-semibold text-emerald-700">{opResult.summary.ausgeglichen_count}</p>
                    <p className="text-xs text-emerald-600 mt-1">Ausgeglichen</p>
                  </div>
                  <div className={`rounded-lg border px-4 py-3 text-center ${
                    opResult.summary.bestellungen_ohne_zahlung > 0
                      ? 'bg-amber-50 border-amber-200'
                      : 'bg-emerald-50 border-emerald-200'
                  }`}>
                    <p className={`text-2xl font-semibold ${
                      opResult.summary.bestellungen_ohne_zahlung > 0 ? 'text-amber-700' : 'text-emerald-700'
                    }`}>{opResult.summary.bestellungen_ohne_zahlung}</p>
                    <p className={`text-xs mt-1 ${
                      opResult.summary.bestellungen_ohne_zahlung > 0 ? 'text-amber-600' : 'text-emerald-600'
                    }`}>Offen (Bestellungen)</p>
                  </div>
                  <div className={`rounded-lg border px-4 py-3 text-center ${
                    opResult.summary.zahlungen_ohne_bestellung > 0
                      ? 'bg-blue-50 border-blue-200'
                      : 'bg-emerald-50 border-emerald-200'
                  }`}>
                    <p className={`text-2xl font-semibold ${
                      opResult.summary.zahlungen_ohne_bestellung > 0 ? 'text-blue-700' : 'text-emerald-700'
                    }`}>{opResult.summary.zahlungen_ohne_bestellung}</p>
                    <p className={`text-xs mt-1 ${
                      opResult.summary.zahlungen_ohne_bestellung > 0 ? 'text-blue-600' : 'text-emerald-600'
                    }`}>Zahlungen ohne Bestellung</p>
                  </div>
                  <div className={`rounded-lg border px-4 py-3 text-center ${
                    opResult.summary.gesamt_offen_eur > 0
                      ? 'bg-amber-50 border-amber-200'
                      : 'bg-emerald-50 border-emerald-200'
                  }`}>
                    <p className={`text-2xl font-semibold ${
                      opResult.summary.gesamt_offen_eur > 0 ? 'text-amber-700' : 'text-emerald-700'
                    }`}>{formatEur(opResult.summary.gesamt_offen_eur)}</p>
                    <p className={`text-xs mt-1 ${
                      opResult.summary.gesamt_offen_eur > 0 ? 'text-amber-600' : 'text-emerald-600'
                    }`}>Gesamt offen</p>
                  </div>
                </div>

                {opResult.summary.top_offen.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-text mb-3">
                      Offene Bestellungen ({opResult.summary.bestellungen_ohne_zahlung} gesamt
                      {opResult.summary.bestellungen_ohne_zahlung > opResult.summary.top_offen.length
                        ? `, erste ${opResult.summary.top_offen.length} angezeigt`
                        : ''})
                    </h3>
                    <div className="overflow-x-auto rounded-lg border border-border">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="bg-gray-50 border-b border-border">
                            <th className="text-left px-4 py-2 font-medium text-text-secondary">Bestellnummer</th>
                            <th className="text-right px-4 py-2 font-medium text-text-secondary">Offener Saldo</th>
                          </tr>
                        </thead>
                        <tbody>
                          {opResult.summary.top_offen.map((item) => (
                            <tr key={item.belegfeld1} className="border-b border-border last:border-0 hover:bg-gray-50/50">
                              <td className="px-4 py-2 font-mono text-xs text-text">{item.belegfeld1}</td>
                              <td className="px-4 py-2 text-right text-amber-700 font-medium">{formatEur(item.saldo)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {opResult.summary.bestellungen_ohne_zahlung === 0 && (
                  <p className="text-sm text-emerald-700 font-medium flex items-center gap-2">
                    <CircleCheck className="w-4 h-4" />
                    Alle Bestellungen sind ausgeglichen!
                  </p>
                )}
              </CardContent>
            </Card>
          </section>
        )}
      </div>

      <ConversionDetailsDialog
        result={convertResult}
        onClose={() => setConvertResult(null)}
      />

      <OpDetailsDialog
        summary={opResult?.summary}
        open={opDialogOpen}
        onClose={() => setOpDialogOpen(false)}
      />

      <Dialog
        open={editorOpen}
        onClose={() => setEditorOpen(false)}
        title={`Datei bearbeiten: ${editorFilename}`}
        className="max-w-6xl"
      >
        {editorLoading ? (
          <div className="py-10 flex justify-center">
            <LoadingSpinner />
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-text-secondary">
              Du kannst die CSV direkt bearbeiten und speichern.
            </p>
            <textarea
              value={editorContent}
              onChange={(e) => setEditorContent(e.target.value)}
              className="w-full min-h-[60vh] rounded-lg border border-border bg-white px-3 py-2 text-sm font-mono text-text"
              spellCheck={false}
            />
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setEditorOpen(false)}>
                Abbrechen
              </Button>
              <Button variant="primary" onClick={saveFileEditor} loading={editorSaving}>
                Speichern
              </Button>
            </div>
          </div>
        )}
      </Dialog>

      <Dialog
        open={exportPreviewOpen}
        onClose={() => setExportPreviewOpen(false)}
        title={`Export ansehen: ${exportPreviewFilename}`}
        className="max-w-6xl"
      >
        {exportPreviewLoading ? (
          <div className="py-10 flex justify-center">
            <LoadingSpinner />
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-text-secondary">
              Vorschau des Export-Inhalts (nur lesen).
            </p>
            <textarea
              value={exportPreviewContent}
              readOnly
              className="w-full min-h-[60vh] rounded-lg border border-border bg-white px-3 py-2 text-sm font-mono text-text"
              spellCheck={false}
            />
            <div className="flex justify-end">
              <Button variant="primary" onClick={() => setExportPreviewOpen(false)}>
                Schliessen
              </Button>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}

interface FileSectionProps {
  title: string;
  description: string;
  files: FileInfo[];
  isLoading: boolean;
  selected: string[];
  onToggle: (files: string[]) => void;
  onUpload: (event: React.ChangeEvent<HTMLInputElement>) => void;
  actionLabel: string;
  actionDisabled: boolean;
  actionLoading: boolean;
  onAction: () => void;
  onEditFile: (filename: string) => void;
  icon: React.ReactNode;
}

interface ConversionDetailsDialogProps {
  result: ConvertResponse | null;
  onClose: () => void;
}

function ConversionDetailsDialog({ result, onClose }: ConversionDetailsDialogProps) {
  if (!result) {
    return null;
  }

  const details = result.details;
  const isOrders = details?.mode === 'orders';

  return (
    <Dialog
      open={Boolean(result)}
      onClose={onClose}
      title={isOrders ? 'Bestellberichte Ergebnis' : 'Zahlungsberichte Ergebnis'}
      className="max-w-3xl"
    >
      <div className="space-y-5">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="rounded-lg border border-blue-200 bg-blue-50 px-3 py-2">
            <p className="text-xs text-blue-700">Dateien</p>
            <p className="text-xl font-semibold text-blue-800">{result.processed_files.length}</p>
          </div>
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2">
            <p className="text-xs text-emerald-700">Datensaetze</p>
            <p className="text-xl font-semibold text-emerald-800">
              {result.totals.orders ?? result.totals.transactions ?? 0}
            </p>
          </div>
          <div className="rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2">
            <p className="text-xs text-indigo-700">Buchungen</p>
            <p className="text-xl font-semibold text-indigo-800">{result.totals.bookings ?? 0}</p>
          </div>
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
            <p className="text-xs text-amber-700">Uebersprungen</p>
            <p className="text-xl font-semibold text-amber-800">{result.totals.skipped ?? 0}</p>
          </div>
          <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2">
            <p className="text-xs text-rose-700">Ignoriert</p>
            <p className="text-xl font-semibold text-rose-800">{result.totals.ignored ?? 0}</p>
          </div>
        </div>

        {details?.files && details.files.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-border">
                  <th className="text-left px-4 py-2 font-medium text-text-secondary">Datei</th>
                  <th className="text-right px-4 py-2 font-medium text-text-secondary">Datensaetze</th>
                  <th className="text-right px-4 py-2 font-medium text-text-secondary">Buchungen</th>
                  <th className="text-right px-4 py-2 font-medium text-text-secondary">Uebersprungen</th>
                  <th className="text-right px-4 py-2 font-medium text-text-secondary">Ignoriert</th>
                </tr>
              </thead>
              <tbody>
                {details.files.map((file) => (
                  <tr key={file.filename} className="border-b border-border last:border-0">
                    <td className="px-4 py-2 text-text">{file.filename}</td>
                    <td className="px-4 py-2 text-right text-text">{file.records}</td>
                    <td className="px-4 py-2 text-right text-text">{file.bookings}</td>
                    <td className="px-4 py-2 text-right text-text">{file.skipped}</td>
                    <td className="px-4 py-2 text-right text-text">{file.ignored}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {details?.notes && details.notes.length > 0 && (
          <div className="rounded-lg border border-border bg-white/70 p-3 space-y-1">
            {details.notes.map((note) => (
              <p key={note} className="text-sm text-text-secondary">- {note}</p>
            ))}
          </div>
        )}

        {isOrders && details?.ignored_rows && details.ignored_rows.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-text">Ignorierte Zeilen (erste {details.ignored_rows.length})</p>
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-border">
                    <th className="text-left px-4 py-2 font-medium text-text-secondary">Datei</th>
                    <th className="text-left px-4 py-2 font-medium text-text-secondary">Bestellnummer</th>
                    <th className="text-left px-4 py-2 font-medium text-text-secondary">Rechnungsnummer</th>
                    <th className="text-left px-4 py-2 font-medium text-text-secondary">Verkaufsart</th>
                    <th className="text-left px-4 py-2 font-medium text-text-secondary">Grund</th>
                  </tr>
                </thead>
                <tbody>
                  {details.ignored_rows.map((row, idx) => (
                    <tr key={`${row.filename}-${row.bestellnummer}-${idx}`} className="border-b border-border last:border-0">
                      <td className="px-4 py-2 text-text">{row.filename}</td>
                      <td className="px-4 py-2 font-mono text-xs text-text">{row.bestellnummer || '-'}</td>
                      <td className="px-4 py-2 text-text">{row.rechnungsnummer || '-'}</td>
                      <td className="px-4 py-2 text-text">{row.verkaufsart || '-'}</td>
                      <td className="px-4 py-2 text-text-secondary">{row.grund}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="flex justify-end">
          <Button variant="primary" onClick={onClose}>Schliessen</Button>
        </div>
      </div>
    </Dialog>
  );
}

interface OpDetailsDialogProps {
  summary: OpAnalysisResponse['summary'];
  open: boolean;
  onClose: () => void;
}

function OpDetailsDialog({ summary, open, onClose }: OpDetailsDialogProps) {
  if (!summary) {
    return null;
  }

  return (
    <Dialog open={open} onClose={onClose} title="OP-Analyse Ergebnis" className="max-w-4xl">
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-3 text-center">
            <p className="text-2xl font-semibold text-emerald-700">{summary.ausgeglichen_count}</p>
            <p className="text-xs text-emerald-600 mt-1">Ausgeglichen</p>
          </div>
          <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-center">
            <p className="text-2xl font-semibold text-amber-700">{summary.bestellungen_ohne_zahlung}</p>
            <p className="text-xs text-amber-600 mt-1">Offen (Bestellungen)</p>
          </div>
          <div className="rounded-lg bg-blue-50 border border-blue-200 px-4 py-3 text-center">
            <p className="text-2xl font-semibold text-blue-700">{summary.zahlungen_ohne_bestellung}</p>
            <p className="text-xs text-blue-600 mt-1">Zahlungen ohne Bestellung</p>
          </div>
          <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-center">
            <p className="text-2xl font-semibold text-amber-700">{formatEur(summary.gesamt_offen_eur)}</p>
            <p className="text-xs text-amber-600 mt-1">Gesamt offen</p>
          </div>
        </div>

        {summary.top_offen.length > 0 ? (
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-border">
                  <th className="text-left px-4 py-2 font-medium text-text-secondary">Bestellnummer</th>
                  <th className="text-right px-4 py-2 font-medium text-text-secondary">Offener Saldo</th>
                </tr>
              </thead>
              <tbody>
                {summary.top_offen.map((item) => (
                  <tr key={item.belegfeld1} className="border-b border-border last:border-0">
                    <td className="px-4 py-2 font-mono text-xs text-text">{item.belegfeld1}</td>
                    <td className="px-4 py-2 text-right text-amber-700 font-medium">{formatEur(item.saldo)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-emerald-700 font-medium flex items-center gap-2">
            <CircleCheck className="w-4 h-4" />
            Alle Bestellungen sind ausgeglichen.
          </p>
        )}

        <div className="flex justify-end">
          <Button variant="primary" onClick={onClose}>Schliessen</Button>
        </div>
      </div>
    </Dialog>
  );
}

function FileSection({
  title,
  description,
  files,
  isLoading,
  selected,
  onToggle,
  onUpload,
  actionLabel,
  actionDisabled,
  actionLoading,
  onAction,
  onEditFile,
  icon,
}: FileSectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-text-secondary">{description}</p>

        <div className="flex flex-wrap items-center gap-3">
          <label className="inline-flex items-center gap-2 text-sm text-primary cursor-pointer">
            <UploadCloud className="w-4 h-4" />
            Upload CSV
            <input type="file" accept=".csv" onChange={onUpload} className="hidden" />
          </label>
          <span className="text-xs text-text-secondary">CSV-Dateien (.csv)</span>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-6">
            <LoadingSpinner />
          </div>
        ) : files.length > 0 ? (
          <div className="space-y-2">
            {files.map((file) => {
              const isChecked = selected.includes(file.name);
              return (
                <label
                  key={file.name}
                  className={`flex items-center justify-between gap-3 rounded-lg border border-border px-3 py-2 cursor-pointer transition ${
                    isChecked ? 'bg-primary/10 border-primary/30' : 'bg-white/70'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => {
                        if (isChecked) {
                          onToggle(selected.filter((name) => name !== file.name));
                        } else {
                          onToggle([...selected, file.name]);
                        }
                      }}
                    />
                    <div>
                      <p className="text-sm font-medium text-text">{file.name}</p>
                      <p className="text-xs text-text-secondary">
                        {formatBytes(file.size)} • {formatDate(file.modified)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        onEditFile(file.name);
                      }}
                    >
                      <FolderOpen className="w-4 h-4" />
                      Öffnen
                    </Button>
                    <div className="text-text-secondary">{icon}</div>
                  </div>
                </label>
              );
            })}
          </div>
        ) : (
          <EmptyState
            icon="csv"
            title="Keine Dateien gefunden"
            description="Bitte lade zuerst CSV-Dateien hoch."
          />
        )}

        <Button
          variant="primary"
          onClick={onAction}
          loading={actionLoading}
          disabled={actionDisabled || actionLoading}
        >
          <RefreshCw className={`w-4 h-4 ${actionLoading ? 'animate-spin' : ''}`} />
          {actionLabel}
        </Button>
      </CardContent>
    </Card>
  );
}

function formatEur(value: number) {
  return value.toLocaleString('de-DE', { style: 'currency', currency: 'EUR' });
}

function formatBytes(bytes: number) {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let value = bytes;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(value < 10 && unitIndex > 0 ? 1 : 0)} ${units[unitIndex]}`;
}

function formatDate(dateValue: string) {
  const date = new Date(dateValue);
  if (Number.isNaN(date.getTime())) {
    return dateValue;
  }
  return date.toLocaleString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
