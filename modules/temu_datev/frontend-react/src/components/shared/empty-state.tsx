import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Package, FileText, ShoppingCart, BarChart3, FolderOpen } from 'lucide-react';

type EmptyStateIcon = 'default' | 'orders' | 'inventory' | 'pdf' | 'csv' | 'stats';

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: EmptyStateIcon;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

const iconMap = {
  default: FolderOpen,
  orders: ShoppingCart,
  inventory: Package,
  pdf: FileText,
  csv: BarChart3,
  stats: BarChart3,
};

const defaultTitles: Record<EmptyStateIcon, string> = {
  default: 'Keine Daten vorhanden',
  orders: 'Keine Bestellungen',
  inventory: 'Keine Produkte',
  pdf: 'Keine PDFs',
  csv: 'Keine CSV-Dateien',
  stats: 'Keine Statistiken',
};

const defaultDescriptions: Record<EmptyStateIcon, string> = {
  default: 'Es gibt noch keine Daten in diesem Bereich.',
  orders: 'Es wurden noch keine Bestellungen importiert.',
  inventory: 'Ihr Inventar ist leer. Importieren Sie Produkte.',
  pdf: 'Sie haben noch keine PDF-Dateien hochgeladen.',
  csv: 'Sie haben noch keine CSV-Dateien verarbeitet.',
  stats: 'Es sind noch keine Daten für die Statistik verfügbar.',
};

export function EmptyState({
  title,
  description,
  icon = 'default',
  actionLabel,
  onAction,
  className,
}: EmptyStateProps) {
  const IconComponent = iconMap[icon];
  const defaultTitle = defaultTitles[icon];
  const defaultDescription = defaultDescriptions[icon];

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-16 px-8 text-center',
        className
      )}
    >
      <div className="bg-gray-100 rounded-full p-6 mb-4">
        <IconComponent className="w-12 h-12 text-text-secondary" />
      </div>
      <h3 className="text-lg font-semibold text-text mb-2">
        {title || defaultTitle}
      </h3>
      <p className="text-text-secondary text-sm max-w-sm mb-6">
        {description || defaultDescription}
      </p>
      {actionLabel && onAction && (
        <Button variant="primary" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}