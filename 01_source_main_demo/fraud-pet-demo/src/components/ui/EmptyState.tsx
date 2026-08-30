import { type HTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

/**
 * EmptyState — 空状态组件
 * 参考 ui-ux-pro-max empty-states 规则
 *
 * 用法: <EmptyState icon={...} title="还没有数据" description="..." action={<Button>...</Button>} />
 *
 * 满足规则:
 * - empty-states (有意义的信息 + 行动引导)
 * - visual-hierarchy (图标→标题→描述→行动 层级清晰)
 */
export interface EmptyStateProps extends HTMLAttributes<HTMLDivElement> {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({
  className,
  icon,
  title,
  description,
  action,
  ...props
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-center py-12 px-6',
        className,
      )}
      {...props}
    >
      {icon && (
        <div className="mb-4 w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-soft to-gray-100 border border-primary/10 flex items-center justify-center text-primary">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-bold text-ink mb-1.5">{title}</h3>
      {description && (
        <p className="text-sm text-subtext leading-relaxed max-w-sm mb-5">{description}</p>
      )}
      {action}
    </div>
  );
}
