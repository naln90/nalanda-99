import { type HTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

/**
 * Progress — 渐变进度条组件
 * 支持 shimmer 流光效果与自定义渐变
 *
 * 满足规则:
 * - loading-states (可视化进度反馈)
 * - transform-performance (用 transform/opacity 动画)
 */
export interface ProgressProps extends HTMLAttributes<HTMLDivElement> {
  /** 0-100 */
  value: number;
  /** 渐变方向色，默认品牌→紫 */
  gradient?: 'primary' | 'success' | 'warning' | 'danger';
  /** 高度 px */
  height?: number;
  /** 显示 shimmer 流光 */
  shimmer?: boolean;
  /** 显示数值标签 */
  showLabel?: boolean;
}

const gradientClasses = {
  primary: 'from-primary to-violet-500',
  success: 'from-safe-500 to-emerald-400',
  warning: 'from-warning-500 to-amber-400',
  danger: 'from-danger-500 to-rose-400',
};

export function Progress({
  value,
  gradient = 'primary',
  height = 10,
  shimmer = true,
  showLabel = false,
  className,
  ...props
}: ProgressProps) {
  const clamped = Math.max(0, Math.min(100, value));

  return (
    <div className={cn('w-full', className)} {...props}>
      <div
        className="w-full bg-gray-100 rounded-full overflow-hidden"
        style={{ height: `${height}px` }}
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className={cn(
            'h-full rounded-full bg-gradient-to-r transition-all duration-700 ease-out relative',
            gradientClasses[gradient],
          )}
          style={{ width: `${clamped}%` }}
        >
          {shimmer && (
            <div
              className="absolute inset-0 animate-shimmer"
              style={{
                background:
                  'linear-gradient(90deg, transparent, rgb(255 255 255 / 0.35), transparent)',
                backgroundSize: '200% 100%',
              }}
            />
          )}
        </div>
      </div>
      {showLabel && (
        <div className="flex justify-between mt-1.5 text-xs text-subtext">
          <span>进度</span>
          <span className="font-semibold text-ink">{clamped}%</span>
        </div>
      )}
    </div>
  );
}
