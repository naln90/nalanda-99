import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import { AlertCircle, CheckCircle2, Info, X, XCircle } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastItem {
  id: number;
  type: ToastType;
  message: string;
}

interface ToastContextValue {
  toast: (type: ToastType, message: string) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  warning: (message: string) => void;
  info: (message: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

let toastIdCounter = 0;

// 模块级 toast 总线：允许非 React 上下文（如 Zustand store action）触发 toast，
// 避免后台静默加载失败时「完全无提示」。Provider 挂载时注册，卸载时注销。
type ExternalToastFn = (type: ToastType, message: string) => void;
let externalToast: ExternalToastFn | null = null;
export function registerExternalToast(fn: ExternalToastFn | null): void {
  externalToast = fn;
}
export function emitToast(type: ToastType, message: string): void {
  externalToast?.(type, message);
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const remove = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    (type: ToastType, message: string) => {
      const id = ++toastIdCounter;
      setToasts((prev) => [...prev, { id, type, message }]);
      // 自动消失：错误 5s，其他 3s
      const duration = type === 'error' ? 5000 : 3000;
      window.setTimeout(() => remove(id), duration);
    },
    [remove],
  );

  // 向模块级总线注册，供 store 等非组件代码触发 toast
  useEffect(() => {
    registerExternalToast(toast);
    return () => registerExternalToast(null);
  }, [toast]);

  const value: ToastContextValue = {
    toast,
    success: (m) => toast('success', m),
    error: (m) => toast('error', m),
    warning: (m) => toast('warning', m),
    info: (m) => toast('info', m),
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} onClose={remove} />
    </ToastContext.Provider>
  );
}

const TOAST_CONFIG: Record<ToastType, { icon: typeof Info; iconColor: string; barColor: string; bg: string }> = {
  success: { icon: CheckCircle2, iconColor: 'text-emerald-500', barColor: 'bg-emerald-400', bg: 'bg-white' },
  error: { icon: XCircle, iconColor: 'text-rose-500', barColor: 'bg-rose-400', bg: 'bg-white' },
  warning: { icon: AlertCircle, iconColor: 'text-amber-500', barColor: 'bg-amber-400', bg: 'bg-white' },
  info: { icon: Info, iconColor: 'text-blue-500', barColor: 'bg-blue-400', bg: 'bg-white' },
};

function ToastContainer({ toasts, onClose }: { toasts: ToastItem[]; onClose: (id: number) => void }) {
  return (
    <div
      className="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none"
      role="region"
      aria-label="通知"
      aria-live="polite"
    >
      {toasts.map((t) => {
        const config = TOAST_CONFIG[t.type];
        const Icon = config.icon;
        return (
          <div
            key={t.id}
            className={`pointer-events-auto flex items-start gap-3 ${config.bg} rounded-xl shadow-lg border border-slate-100 overflow-hidden min-w-[280px] max-w-[400px] animate-slide-up`}
            role="alert"
          >
            <div className={`w-1 self-stretch ${config.barColor}`} aria-hidden="true" />
            <Icon size={18} className={`mt-3 flex-shrink-0 ${config.iconColor}`} aria-hidden="true" />
            <p className="flex-1 text-sm text-ink py-3 pr-2 leading-relaxed">{t.message}</p>
            <button
              onClick={() => onClose(t.id)}
              className="mt-2.5 mr-2 p-1 rounded-md text-subtext hover:text-ink hover:bg-slate-100 transition flex-shrink-0"
              aria-label="关闭通知"
            >
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    // 在 Provider 之外使用时返回一个 no-op 实现，避免页面崩溃
    const noop = () => {};
    return { toast: noop, success: noop, error: noop, warning: noop, info: noop };
  }
  return ctx;
}

/** 便捷 hook：传入一个异步函数，自动捕获错误并弹出 toast */
export function useAsyncToast() {
  const { error, success } = useToast();
  const [isLoading, setIsLoading] = useState(false);

  const run = useCallback(
    async <T,>(fn: () => Promise<T>, opts?: { successMessage?: string; errorMessage?: string }): Promise<T | null> => {
      setIsLoading(true);
      try {
        const result = await fn();
        if (opts?.successMessage) success(opts.successMessage);
        return result;
      } catch (e) {
        const msg = opts?.errorMessage || (e instanceof Error ? e.message : '操作失败');
        error(msg);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [error, success],
  );

  return { run, isLoading };
}
