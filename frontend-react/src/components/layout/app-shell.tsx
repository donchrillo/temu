import { X } from 'lucide-react';
import { Sidebar } from './sidebar';
import { Header } from './header';
import { useLayout } from '../../contexts/LayoutContext';
import { cn } from '../../lib/utils';

interface AppShellProps {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
}

export function AppShell({ title, subtitle, children }: AppShellProps) {
  const { mobileMenuOpen, closeMobileMenu } = useLayout();

  return (
    <div className="flex min-h-screen bg-background dark:bg-dark-background">
      {/* Desktop Sidebar - only visible on lg screens */}
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      {/* Mobile Overlay */}
      {mobileMenuOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-40 bg-black/50 lg:hidden"
            onClick={closeMobileMenu}
            aria-label="Menü schließen"
          />
          
          {/* Mobile Sidebar */}
          <div className="lg:hidden">
            <Sidebar mobile={true} />
            
            {/* Close Button */}
            <button
              onClick={closeMobileMenu}
              className="fixed top-4 right-4 z-50 p-2 bg-card border border-border rounded-full shadow-sm hover:bg-background transition-colors"
              aria-label="Menü schließen"
            >
              <X className="w-5 h-5 text-text" />
            </button>
          </div>
        </>
      )}
      
      {/* Main Content */}
      <main 
        className={cn(
          "flex-1 flex flex-col transition-all duration-300",
          "lg:ml-0"
        )}
      >
        {title && <Header title={title} subtitle={subtitle} />}
        <div className="flex-1 p-4 md:p-6 overflow-auto">
          {children}
        </div>
      </main>
    </div>
  );
}