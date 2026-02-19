import { Bell, Search } from 'lucide-react';

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export function Header({ title, subtitle }: HeaderProps) {
  return (
    <header className="bg-card border-b border-border px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-text">{title}</h1>
          {subtitle && <p className="text-sm text-text-secondary">{subtitle}</p>}
        </div>
        
        <div className="flex items-center gap-4">
          {/* Search (optional) */}
          <button className="p-2 hover:bg-background rounded-md transition-colors">
            <Search className="w-5 h-5 text-text-secondary" />
          </button>
          
          {/* Notifications */}
          <button className="p-2 hover:bg-background rounded-md transition-colors relative">
            <Bell className="w-5 h-5 text-text-secondary" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-danger rounded-full" />
          </button>
        </div>
      </div>
    </header>
  );
}