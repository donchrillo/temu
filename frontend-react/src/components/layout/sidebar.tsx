import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  FileText, 
  Table, 
  Settings,
  ShoppingCart,
  ChevronDown,
  ChevronUp,
  Users,
  ClipboardList,
  Package,
  Truck
} from 'lucide-react';
import { cn } from '../../lib/utils';

// Oberste Ebene - nicht einklappbar
const mainMenuItems = [
  { id: 'kunden', label: 'Kundenzahl', path: '/kunden', icon: <Users className="w-4 h-4" />, disabled: true },
  { id: 'auftraege', label: 'Aufträge', path: '/auftraege', icon: <ClipboardList className="w-4 h-4" />, disabled: true },
  { id: 'artikel', label: 'Artikel', path: '/artikel', icon: <Package className="w-4 h-4" />, disabled: true },
  { id: 'versand', label: 'Versand', path: '/versand', icon: <Truck className="w-4 h-4" />, disabled: true },
];

// Werkzeuge (einklappbar)
const toolItems = [
  { id: 'csv', label: 'CSV-Verarbeiter', path: '/csv', icon: <Table className="w-4 h-4" /> },
  { id: 'pdf', label: 'PDF-Reader', path: '/pdf', icon: <FileText className="w-4 h-4" /> },
];

// Marktplatz-Einträge (unter Verwaltung)
const marktplatzItems = [
  { id: 'temu', label: 'TEMU', path: '/temu', icon: <ShoppingCart className="w-4 h-4" /> },
  { id: 'amazon', label: 'Amazon', path: '/amazon', icon: <ShoppingCart className="w-4 h-4" />, disabled: true },
  { id: 'ebay', label: 'eBay', path: '/ebay', icon: <ShoppingCart className="w-4 h-4" />, disabled: true },
  { id: 'otto', label: 'Otto', path: '/otto', icon: <ShoppingCart className="w-4 h-4" />, disabled: true },
  { id: 'kaufland', label: 'Kaufland', path: '/kaufland', icon: <ShoppingCart className="w-4 h-4" />, disabled: true },
];

export function Sidebar() {
  const location = useLocation();
  const [toolsOpen, setToolsOpen] = useState(true);
  const [verwaltungOpen, setVerwaltungOpen] = useState(false);
  const [marktplatzOpen, setMarktplatzOpen] = useState(false);

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <aside className="w-60 bg-card border-r border-border h-screen sticky top-0 flex flex-col">
      {/* Logo */}
      <div className="p-4 border-b border-border">
        <h1 className="text-lg font-semibold text-text">Toci Tools</h1>
        <p className="text-xs text-text-secondary">JTL-Wawi ERP</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4">
        {/* Hauptmenü - NICHT einklappbar */}
        <div className="mb-4">
          <ul className="space-y-1">
            {mainMenuItems.map((item) => (
              <li key={item.id}>
                {item.disabled ? (
                  <div className="px-4 py-2 mx-2 rounded-md text-sm flex items-center gap-3 text-text-secondary cursor-not-allowed opacity-50">
                    {item.icon}
                    <span>{item.label}</span>
                  </div>
                ) : (
                  <Link
                    to={item.path}
                    className={cn(
                      "px-4 py-2 mx-2 rounded-md text-sm flex items-center gap-3",
                      "text-text hover:bg-background transition-colors",
                      isActive(item.path) && "bg-primary text-white hover:bg-primary-hover"
                    )}
                  >
                    {item.icon}
                    <span>{item.label}</span>
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </div>

        {/* Trennlinie */}
        <div className="border-t border-border my-2"></div>

        {/* Werkzeuge - collapsible */}
        <div className="mb-2">
          <button
            onClick={() => setToolsOpen(!toolsOpen)}
            className="w-full px-4 py-2 mx-2 flex items-center justify-between text-xs font-semibold text-text-secondary uppercase tracking-wider hover:bg-background rounded-md transition-colors"
          >
            <div className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              <span>Werkzeuge</span>
            </div>
            {toolsOpen ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
          
          {toolsOpen && (
            <ul className="space-y-1 mt-1 animate-fade-in">
              {toolItems.map((item) => (
                <li key={item.id}>
                  <Link
                    to={item.path}
                    className={cn(
                      "px-4 py-2 mx-2 rounded-md text-sm flex items-center gap-3",
                      "text-text hover:bg-background transition-colors",
                      isActive(item.path) && "bg-primary text-white hover:bg-primary-hover"
                    )}
                  >
                    {item.icon}
                    <span>{item.label}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Trennlinie */}
        <div className="border-t border-border my-2"></div>

        {/* Verwaltung - collapsible */}
        <div className="mb-2">
          <button
            onClick={() => setVerwaltungOpen(!verwaltungOpen)}
            className="w-full px-4 py-2 mx-2 flex items-center justify-between text-xs font-semibold text-text-secondary uppercase tracking-wider hover:bg-background rounded-md transition-colors"
          >
            <div className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              <span>Verwaltung</span>
            </div>
            {verwaltungOpen ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
          
          {verwaltungOpen && (
            <div className="mt-1 animate-fade-in">
              {/* Marktplätze - collapsible */}
              <div className="mb-1">
                <button
                  onClick={() => setMarktplatzOpen(!marktplatzOpen)}
                  className="w-full px-4 py-2 mx-2 flex items-center justify-between text-sm text-text-secondary hover:bg-background rounded-md transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <span>📦 Marktplätze</span>
                  </div>
                  {marktplatzOpen ? (
                    <ChevronUp className="w-3 h-3" />
                  ) : (
                    <ChevronDown className="w-3 h-3" />
                  )}
                </button>
                
                {marktplatzOpen && (
                  <ul className="space-y-1 ml-4 mt-1 border-l border-border pl-2 animate-fade-in">
                    {marktplatzItems.map((item) => (
                      <li key={item.id}>
                        {item.disabled ? (
                          <div className="px-4 py-2 rounded-md text-sm flex items-center gap-3 text-text-secondary cursor-not-allowed opacity-50">
                            {item.icon}
                            <span>{item.label}</span>
                          </div>
                        ) : (
                          <Link
                            to={item.path}
                            className={cn(
                              "px-4 py-2 rounded-md text-sm flex items-center gap-3",
                              "text-text hover:bg-background transition-colors",
                              isActive(item.path) && "bg-primary text-white hover:bg-primary-hover"
                            )}
                          >
                            {item.icon}
                            <span>{item.label}</span>
                          </Link>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-2 text-xs text-text-secondary">
          <div className="w-2 h-2 rounded-full bg-success animate-pulse-slow" />
          <span>System Online</span>
        </div>
      </div>
    </aside>
  );
}
