import { createContext, useContext, useState } from 'react';
import { cn } from '@/lib/utils';

interface TabsContextType {
  activeTab: string;
  setActiveTab: (value: string) => void;
}

const TabsContext = createContext<TabsContextType | null>(null);

function useTabsContext() {
  const context = useContext(TabsContext);
  if (!context) {
    throw new Error('Tabs components must be used within a Tabs provider');
  }
  return context;
}

export interface TabItem {
  value: string;
  label: string;
  icon?: React.ReactNode;
  content: React.ReactNode;
  disabled?: boolean;
}

export interface TabsProps {
  tabs: TabItem[];
  defaultValue: string;
  className?: string;
  onChange?: (value: string) => void;
}

export function Tabs({ tabs, defaultValue, className, onChange }: TabsProps) {
  const [activeTab, setActiveTab] = useState(defaultValue);

  const handleTabChange = (value: string) => {
    setActiveTab(value);
    onChange?.(value);
  };

  const activeTabContent = tabs.find((tab) => tab.value === activeTab)?.content;

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab: handleTabChange }}>
      <div className={cn('w-full', className)}>
        {activeTabContent}
      </div>
    </TabsContext.Provider>
  );
}

export interface TabsListProps extends React.HTMLAttributes<HTMLDivElement> {}

export function TabsList({ className, children, ...props }: TabsListProps) {
  return (
    <div
      className={cn(
        'flex gap-1 p-1 bg-gray-100 rounded-lg',
        className
      )}
      role="tablist"
      {...props}
    >
      {children}
    </div>
  );
}

export interface TabProps {
  value: string;
  children: React.ReactNode;
  disabled?: boolean;
  className?: string;
}

export function Tab({ value, children, disabled, className }: TabProps) {
  const { activeTab, setActiveTab } = useTabsContext();
  const isActive = activeTab === value;

  return (
    <button
      role="tab"
      aria-selected={isActive}
      aria-disabled={disabled}
      disabled={disabled}
      onClick={() => setActiveTab(value)}
      className={cn(
        'flex-1 flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-all duration-200',
        isActive
          ? 'bg-white text-primary shadow-sm'
          : 'text-text-secondary hover:text-text',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
    >
      {children}
    </button>
  );
}

export interface TabContentProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

export function TabContent({ value, children, className }: TabContentProps) {
  const { activeTab } = useTabsContext();

  if (activeTab !== value) return null;

  return (
    <div
      role="tabpanel"
      className={cn('mt-4 animate-fade-in', className)}
    >
      {children}
    </div>
  );
}