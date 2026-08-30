import { type HTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

/**
 * Skeleton — 骨架屏加载占位
 * 参考 ui-ux-pro-max progressive-loading 规则
 *
 * 用法: <Skeleton className="h-4 w-3/4" />
 * shimmer 动画由 .skeleton 工具类提供，prefers-reduced-motion 下自动禁用
 */
export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  rounded?: 'sm' | 'md' | 'lg' | 'full';
}

const roundedMap = {
  sm: 'rounded-md',
  md: 'rounded-lg',
  lg: 'rounded-xl',
  full: 'rounded-full',
};

export function Skeleton({ className, rounded = 'md', ...props }: SkeletonProps) {
  return (
    <div
      className={cn('skeleton', roundedMap[rounded], className)}
      aria-hidden="true"
      {...props}
    />
  );
}
