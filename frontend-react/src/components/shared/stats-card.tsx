import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import type { ReactNode } from 'react';

interface StatsCardProps {
  title: string;
  value: number | string;
  icon: ReactNode;
  iconBgColor?: string;
  isLoading?: boolean;
  className?: string;
}

export function StatsCard({
  title,
  value,
  icon,
  iconBgColor = 'bg-primary/10 text-primary',
  isLoading = false,
  className,
}: StatsCardProps) {
  return (
    <Card className={cn('hover:shadow-card-hover transition-shadow', className)}>
      <CardContent className="flex items-center gap-4 p-4">
        <div className={cn('p-3 rounded-lg', iconBgColor)}>
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-text-secondary truncate">{title}</p>
          {isLoading ? (
            <div className="h-8 w-16 bg-gray-200 animate-pulse rounded" />
          ) : (
            <p className="text-2xl font-bold text-text truncate">{value}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
