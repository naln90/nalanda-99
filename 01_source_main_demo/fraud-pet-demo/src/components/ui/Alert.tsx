import { type HTMLAttributes } from 'react';
import { AlertCircle, CheckCircle2, Info, AlertTriangle, X } from 'lucide-react';
import { cn } from '../../lib/utils';

/**
 * Alert — 反馈提示组件
 * 参考 ui-ux-pro-max component-specs.md Alert 规范
 *
 * Variants: info | success | warning | danger
 *
 * 满足规则:
 * - error-feedback (清晰错误信息)
 * - error-clarity (原因 + 如何修复)
 * - aria-live-errors (role="alert")
 * - color-not-only (图标 + 文字)
 */
export type AlertVariant = 'info' | 'success' | 'warning' | 'danger';

export interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: AlertVariant;
  title?: string;
  onClose?: () => void;
}

const config = {
  info: {
    icon: Info,
    bg: 'bg-primary-soft/60',
    border: 'border-primary/20',
    iconColor: 'text-primary',
    titleColor: 'text-ink',
  },
  success: {
    icon: CheckCircle2,
    bg: 'bg-safe-50/60',
    border: 'border-safe-500/20',
    iconColor: 'text-safe-600',
    titleColor: 'text-ink',
  },
  warning: {
    icon: AlertTriangle,
    bg: 'bg-warning-50/60',
    border: 'border-warning-500/20',
    iconColor: 'text-warning-600',
    titleColor: 'text-ink',
  },
  danger: {
    icon: AlertCircle,
    bg: 'bg-danger-50/60',
    border: 'border-danger-500/20',
    iconColor: 'text-danger-600',
    titleColor: 'text-ink',
  },
} as const;

export function Alert({
  className,
  variant = 'info',
  title,
  onClose,
  children,
  ...props
}: AlertProps) {
  const c = config[variant];
  const Icon = c.icon;

  return (
    <div
      role="alert"
      className={cn(
        'relative flex items-start gap-3 p-4 rounded-xl border',
        c.bg,
        c.border,
        className,
      )}
      {...props}
    >
      <div className={cn('flex-shrink-0 mt-0.5', c.iconColor)}>
        <Icon size={18} aria-hidden="true" />
      </div>
      <div className="flex-1 min-w-0">
        {title && (
          <p className={cn('font-semibold text-sm mb-0.5', c.titleColor)}>{title}</p>
        )}
        {children && (
          <div className="text-sm text-subtext leading-relaxed">{children}</div>
        )}
      </div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          aria-label="关闭提示"
          className="flex-shrink-0 -mr-1 -mt-1 p-1 rounded-md text-subtext hover:text-ink hover:bg-white/60 transition-colors"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}
