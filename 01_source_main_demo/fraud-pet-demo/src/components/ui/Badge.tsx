import { type HTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

/**
 * Badge — shadcn/ui 风格徽标
 * 采用 cva + data-slot 模式，参考 shadcn/ui badge.tsx
 *
 * Variants: default | secondary | outline | ghost | link | success | warning | danger | info
 * Sizes: sm | default | lg
 */
const badgeVariants = cva(
  'inline-flex w-fit shrink-0 items-center justify-center gap-1 overflow-hidden rounded-full border border-transparent px-2.5 py-1 text-xs font-medium whitespace-nowrap transition-[color,box-shadow] [&>svg]:pointer-events-none [&>svg]:size-3',
  {
    variants: {
      variant: {
        default: 'bg-primary text-white [a&]:hover:bg-primary/90',
        secondary: 'bg-secondary text-secondary-foreground [a&]:hover:bg-secondary/90',
        outline: 'border-border text-ink [a&]:hover:bg-accent [a&]:hover:text-accent-foreground',
        ghost: '[a&]:hover:bg-accent [a&]:hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 [a&]:hover:underline',
        success: 'bg-safe-50 text-safe-600 border border-safe-500/20',
        warning: 'bg-warning-50 text-warning-600 border border-warning-500/20',
        danger: 'bg-danger-50 text-danger-600 border border-danger-500/20',
        info: 'bg-primary-soft text-primary border border-primary/15',
      },
      size: {
        sm: 'text-[11px] px-2 py-0.5 h-5',
        default: 'text-xs px-2.5 py-1',
        lg: 'text-sm px-3 py-1.5 h-7',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
);

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, size, ...props }: BadgeProps) {
  return (
    <span
      data-slot="badge"
      data-variant={variant}
      className={cn(badgeVariants({ variant, size }), className)}
      {...props}
    />
  );
}

export { badgeVariants };
