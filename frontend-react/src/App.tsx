import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from './contexts/ThemeContext';
import { LayoutProvider } from './contexts/LayoutContext';
import { AppShell } from './components/layout/app-shell';
import Dashboard from './pages/dashboard';
import { TemuOrders } from './pages/temu/orders';
import { PdfReader } from './pages/pdf/reader';
import { CsvProcessor } from './pages/csv/processor';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <LayoutProvider>
          <BrowserRouter>
            <Routes>
              {/* Dashboard */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<AppShell><Dashboard /></AppShell>} />
              
              {/* TEMU Connector - alles zusammen */}
              <Route path="/temu" element={<AppShell title="TEMU-Connector" subtitle="Marktplatz-Anbindung"><TemuOrders /></AppShell>} />
              <Route path="/temu/orders" element={<AppShell title="TEMU-Connector" subtitle="Marktplatz-Anbindung"><TemuOrders /></AppShell>} />
              <Route path="/temu/inventory" element={<AppShell title="TEMU-Connector" subtitle="Marktplatz-Anbindung"><TemuOrders /></AppShell>} />
              
              {/* Tool Routes */}
              <Route path="/pdf" element={<AppShell title="PDF Reader" subtitle="Rechnung & Werbung"><PdfReader /></AppShell>} />
              <Route path="/csv" element={<AppShell title="CSV Verarbeiter" subtitle="Amazon DATEV Export"><CsvProcessor /></AppShell>} />
              
              {/* Fallback */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </BrowserRouter>
        </LayoutProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;