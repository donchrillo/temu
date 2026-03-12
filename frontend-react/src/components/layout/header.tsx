import { Bell, Search, Menu, Sun, Moon } from 'lucide-react';
import { useLayout } from '../../contexts/LayoutContext';
import { useTheme } from '../../contexts/ThemeContext';

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export function Header({ title, subtitle }: HeaderProps) {
  const { openMobileMenu } = useLayout();
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="bg-card border-b border-border px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Burger Menu - Mobile only */}
          <button
            onClick={openMobileMenu}
            className="lg:hidden p-2 hover:bg-background rounded-md transition-colors"
            aria-label="Menü öffnen"
          >
            <Menu className="w-5 h-5 text-text" />
          </button>
          
          <div>
            <h1 className="text-xl font-semibold text-text">{title}</h1>
            {subtitle && <p className="text-sm text-text-secondary">{subtitle}</p>}
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Search (optional) */}
          <button className="p-2 hover:bg-background rounded-md transition-colors">
            <Search className="w-5 h-5 text-text-secondary" />
          </button>
          
          {/* Dark Mode Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 hover:bg-background rounded-md transition-colors"
            aria-label={theme === 'dark' ? "Light Mode aktivieren" : "Dark Mode aktivieren"}
          >
            {theme === 'dark' ? (
              <Sun className="w-5 h-5 text-text-secondary" />
            ) : (
              <Moon className="w-5 h-5 text-text-secondary" />
            )}
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