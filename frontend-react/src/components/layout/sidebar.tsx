import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  FileText, 
  Table, 
  Settings,
  ShoppingCart,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  Users,
  ClipboardList,
  Package,
  Truck
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useLayout } from '../../contexts/LayoutContext';

// Oberste Ebene - nicht einklappbar
const mainMenuItems = [
  { id: 'kunden', label: 'Kundenzahl', path: '/kunden', icon: <Users className="w-4 h-4" />, disabled: true },
  { id: 'auftraege', label: 'Aufträge', path: '/auftraege', icon: <ClipboardList className="w-4 h-4" />, disabled: true },
  { id: 'artikel', label: 'Artikel', path: '/artikel', icon: <Package className="w-4 h-4" />, disabled: true },
  { id: 'versand', label: 'Versand', path: '/versand', icon: <Truck className="w-4 h-4" />, disabled: true },
];

// Werkzeuge (einklappbar)
const toolItems: Array<{ id: string; label: string; path: string; icon: React.ReactNode; disabled?: boolean }> = [
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

interface SidebarProps {
  mobile?: boolean;
}

export function Sidebar({ mobile = false }: SidebarProps) {
  const location = useLocation();
  const { sidebarCollapsed, toggleSidebar, closeMobileMenu } = useLayout();
  const [toolsOpen, setToolsOpen] = useState(true);
  const [verwaltungOpen, setVerwaltungOpen] = useState(false);
  const [marktplatzOpen, setMarktplatzOpen] = useState(false);

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const handleLinkClick = () => {
    if (mobile) {
      closeMobileMenu();
    }
  };

  const sidebarWidth = sidebarCollapsed ? 'w-16' : 'w-60';

  const renderMenuItem = (item: typeof mainMenuItems[0], key: string | number) => {
    if (item.disabled) {
      return (
        <div
          key={key}
          className={cn(
            "flex items-center gap-3 text-text-secondary cursor-not-allowed opacity-50",
            sidebarCollapsed ? "px-2 py-2 mx-auto justify-center" : "px-4 py-2 mx-2 rounded-md text-sm"
          )}
          title={sidebarCollapsed ? item.label : undefined}
        >
          {item.icon}
          {!sidebarCollapsed && <span>{item.label}</span>}
        </div>
      );
    }

    return (
      <Link
        key={key}
        to={item.path}
        onClick={handleLinkClick}
        className={cn(
          "flex items-center gap-3 text-text hover:bg-background transition-colors",
          isActive(item.path) && "bg-primary text-white hover:bg-primary-hover",
          sidebarCollapsed ? "px-2 py-2 mx-auto justify-center" : "px-4 py-2 mx-2 rounded-md text-sm"
        )}
        title={sidebarCollapsed ? item.label : undefined}
      >
        {item.icon}
        {!sidebarCollapsed && <span>{item.label}</span>}
      </Link>
    );
  };

  const renderToolItem = (item: typeof toolItems[0], key: string | number) => {
    if (item.disabled) {
      return (
        <div
          key={key}
          className="flex items-center gap-3 text-text-secondary cursor-not-allowed opacity-50 px-4 py-2 mx-2 rounded-md text-sm"
        >
          {item.icon}
          <span>{item.label}</span>
        </div>
      );
    }

    return (
      <Link
        key={key}
        to={item.path}
        onClick={handleLinkClick}
        className={cn(
          "flex items-center gap-3 text-text hover:bg-background transition-colors",
          isActive(item.path) && "bg-primary text-white hover:bg-primary-hover",
          sidebarCollapsed ? "px-2 py-2 mx-auto justify-center" : "px-4 py-2 mx-2 rounded-md text-sm"
        )}
        title={sidebarCollapsed ? item.label : undefined}
      >
        {item.icon}
        {!sidebarCollapsed && <span>{item.label}</span>}
      </Link>
    );
  };

  const renderMarktplatzItem = (item: typeof marktplatzItems[0], key: string | number) => {
    if (item.disabled) {
      return (
        <div
          key={key}
          className="flex items-center gap-3 text-text-secondary cursor-not-allowed opacity-50 px-4 py-2 rounded-md text-sm"
        >
          {item.icon}
          <span>{item.label}</span>
        </div>
      );
    }

    return (
      <Link
        key={key}
        to={item.path}
        onClick={handleLinkClick}
        className={cn(
          "flex items-center gap-3 text-text hover:bg-background transition-colors",
          isActive(item.path) && "bg-primary text-white hover:bg-primary-hover",
          sidebarCollapsed ? "px-2 py-2 mx-auto justify-center" : "px-4 py-2 rounded-md text-sm"
        )}
        title={sidebarCollapsed ? item.label : undefined}
      >
        {item.icon}
        {!sidebarCollapsed && <span>{item.label}</span>}
      </Link>
    );
  };

  return (
    <aside
      className={cn(
        "bg-card border-r border-border h-screen sticky top-0 flex flex-col transition-all duration-300",
        sidebarWidth,
        mobile && "fixed inset-y-0 left-0 z-50 w-60 animate-slide-in-left"
      )}
    >
      {/* Logo */}
      <div className={cn(
        "p-4 border-b border-border",
        sidebarCollapsed && !mobile ? "flex justify-center" : ""
      )}>
        {!sidebarCollapsed || mobile ? (
          <>
            <h1 className="text-lg font-semibold text-text">Toci Tools</h1>
            <p className="text-xs text-text-secondary">JTL-Wawi ERP</p>
          </>
        ) : (
          <h1 className="text-lg font-semibold text-text">TT</h1>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4">
        {/* Hauptmenü - NICHT einklappbar */}
        <div className="mb-4">
          <ul className="space-y-1">
            {mainMenuItems.map((item) => renderMenuItem(item, item.id))}
          </ul>
        </div>

        {/* Trennlinie */}
        <div className="border-t border-border my-2"></div>

        {/* Werkzeuge - collapsible */}
        <div className="mb-2">
          <button
            onClick={() => setToolsOpen(!toolsOpen)}
            className={cn(
              "w-full flex items-center justify-between text-xs font-semibold text-text-secondary uppercase tracking-wider hover:bg-background rounded-md transition-colors",
              sidebarCollapsed && !mobile ? "px-2 py-2 mx-auto" : "px-4 py-2 mx-2"
            )}
            title={sidebarCollapsed && !mobile ? "Werkzeuge" : undefined}
          >
            <div className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              {!sidebarCollapsed || mobile ? <span>Werkzeuge</span> : null}
            </div>
            {!sidebarCollapsed || mobile ? (
              toolsOpen ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )
            ) : null}
          </button>
          
          {(toolsOpen || mobile) && (
            <ul className="space-y-1 mt-1 animate-fade-in">
              {toolItems.map((item) => renderToolItem(item, item.id))}
            </ul>
          )}
        </div>

        {/* Trennlinie */}
        <div className="border-t border-border my-2"></div>

        {/* Verwaltung - collapsible */}
        <div className="mb-2">
          <button
            onClick={() => setVerwaltungOpen(!verwaltungOpen)}
            className={cn(
              "w-full flex items-center justify-between text-xs font-semibold text-text-secondary uppercase tracking-wider hover:bg-background rounded-md transition-colors",
              sidebarCollapsed && !mobile ? "px-2 py-2 mx-auto" : "px-4 py-2 mx-2"
            )}
            title={sidebarCollapsed && !mobile ? "Verwaltung" : undefined}
          >
            <div className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              {!sidebarCollapsed || mobile ? <span>Verwaltung</span> : null}
            </div>
            {!sidebarCollapsed || mobile ? (
              verwaltungOpen ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )
            ) : null}
          </button>
          
          {(verwaltungOpen || mobile) && (
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
                      <li key={item.id}>{renderMarktplatzItem(item, item.id)}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}
        </div>
      </nav>

      {/* Footer */}
      <div className={cn(
        "border-t border-border",
        sidebarCollapsed && !mobile ? "flex justify-center p-4" : "p-4"
      )}>
        {!sidebarCollapsed || mobile ? (
          <div className="flex items-center gap-2 text-xs text-text-secondary">
            <div className="w-2 h-2 rounded-full bg-success animate-pulse-slow" />
            <span>System Online</span>
          </div>
        ) : (
          <div className="w-2 h-2 rounded-full bg-success animate-pulse-slow" title="System Online" />
        )}
      </div>

      {/* Toggle Button (Desktop only) */}
      {!mobile && (
        <button
          onClick={toggleSidebar}
          className="absolute -right-3 top-20 bg-card border border-border rounded-full p-1 shadow-sm hover:bg-background transition-colors"
          title={sidebarCollapsed ? "Sidebar ausklappen" : "Sidebar einklappen"}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="w-4 h-4 text-text-secondary" />
          ) : (
            <ChevronLeft className="w-4 h-4 text-text-secondary" />
          )}
        </button>
      )}
    </aside>
  );
}
