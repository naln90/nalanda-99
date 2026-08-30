import { createContext, useContext, useId, useState, type ReactNode } from 'react';
import { cn } from '../../lib/utils';

/**
 * Tabs — shadcn/ui 风格标签页（轻量自实现）
 * 参考 shadcn/ui tabs.tsx API，不依赖 radix-ui
 * 含 Tabs / TabsList / TabsTrigger / TabsContent
 */

interface TabsContextValue {
  value: string;
  setValue: (v: string) => void;
  baseId: string;
}

const TabsContext = createContext<TabsContextValue | null>(null);

function useTabsContext() {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error('Tabs 子组件必须在 <Tabs> 内使用');
  return ctx;
}

export interface TabsProps {
  value?: string;
  defaultValue?: string;
  onValueChange?: (v: string) => void;
  className?: string;
  children: ReactNode;
}

export function Tabs({ value: controlled, defaultValue, onValueChange, className, children }: TabsProps) {
  const [uncontrolled, setUncontrolled] = useState(defaultValue ?? '');
  const value = controlled ?? uncontrolled;
  const baseId = useId();
  const setValue = (v: string) => {
    if (controlled === undefined) setUncontrolled(v);
    onValueChange?.(v);
  };
  return (
    <TabsContext.Provider value={{ value, setValue, baseId }}>
      <div data-slot="tabs" className={cn('flex flex-col gap-2', className)}>
        {children}
      </div>
    </TabsContext.Provider>
  );
}

export interface TabsListProps {
  className?: string;
  children: ReactNode;
}

export function TabsList({ className, children }: TabsListProps) {
  return (
    <div
      data-slot="tabs-list"
      role="tablist"
      className={cn(
        'inline-flex h-10 w-fit items-center justify-center rounded-lg bg-muted p-1 text-muted-foreground',
        className,
      )}
    >
      {children}
    </div>
  );
}

export interface TabsTriggerProps {
  value: string;
  className?: string;
  children: ReactNode;
  disabled?: boolean;
}

export function TabsTrigger({ value, className, children, disabled }: TabsTriggerProps) {
  const { value: current, setValue, baseId } = useTabsContext();
  const active = current === value;
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      aria-controls={`${baseId}-content-${value}`}
      id={`${baseId}-trigger-${value}`}
      data-slot="tabs-trigger"
      data-state={active ? 'active' : 'inactive'}
      disabled={disabled}
      onClick={() => setValue(value)}
      className={cn(
        'relative inline-flex h-8 flex-1 items-center justify-center gap-1.5 rounded-md border border-transparent px-3 py-1 text-sm font-medium whitespace-nowrap transition-all',
        'focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/40',
        'disabled:pointer-events-none disabled:opacity-50',
        active
          ? 'bg-background text-foreground shadow-sm'
          : 'text-foreground/60 hover:text-foreground',
        className,
      )}
    >
      {children}
    </button>
  );
}

export interface TabsContentProps {
  value: string;
  className?: string;
  children: ReactNode;
}

export function TabsContent({ value, className, children }: TabsContentProps) {
  const { value: current, baseId } = useTabsContext();
  if (current !== value) return null;
  return (
    <div
      role="tabpanel"
      id={`${baseId}-content-${value}`}
      aria-labelledby={`${baseId}-trigger-${value}`}
      data-slot="tabs-content"
      data-state={current === value ? 'active' : 'inactive'}
      className={cn('flex-1 outline-none animate-fade-in', className)}
    >
      {children}
    </div>
  );
}
