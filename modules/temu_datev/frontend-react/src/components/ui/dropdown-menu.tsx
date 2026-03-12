import { useState, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';

export interface DropdownItem {
  label: string;
  value: string;
  icon?: React.ReactNode;
  disabled?: boolean;
  danger?: boolean;
  onClick?: () => void;
}

export interface DropdownMenuProps {
  trigger: React.ReactNode;
  items: DropdownItem[];
  align?: 'start' | 'center' | 'end';
  className?: string;
}

export function DropdownMenu({
  trigger,
  items,
  align = 'end',
  className,
}: DropdownMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen]);

  const alignClasses = {
    start: 'left-0',
    center: 'left-1/2 -translate-x-1/2',
    end: 'right-0',
  };

  const handleItemClick = (item: DropdownItem) => {
    if (!item.disabled && item.onClick) {
      item.onClick();
    }
    setIsOpen(false);
  };

  return (
    <div ref={dropdownRef} className={cn('relative inline-block', className)}>
      {/* Trigger */}
      <div onClick={() => setIsOpen(!isOpen)} className="cursor-pointer">
        {trigger}
      </div>

      {/* Dropdown Content */}
      {isOpen && (
        <div
          className={cn(
            'absolute z-50 mt-1 min-w-[160px] bg-card rounded-md shadow-lg border border-border py-1 animate-fade-in',
            alignClasses[align]
          )}
        >
          {items.map((item, index) => (
            <button
              key={item.value || index}
              onClick={() => handleItemClick(item)}
              disabled={item.disabled}
              className={cn(
                'w-full flex items-center gap-2 px-3 py-2 text-sm text-left transition-colors',
                item.disabled
                  ? 'opacity-50 cursor-not-allowed'
                  : item.danger
                  ? 'text-danger hover:bg-danger/10'
                  : 'text-text hover:bg-gray-100'
              )}
            >
              {item.icon}
              <span className="flex-1">{item.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
