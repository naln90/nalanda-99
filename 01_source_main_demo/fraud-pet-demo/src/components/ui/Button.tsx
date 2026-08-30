import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

/**
 * Button — shadcn/ui 风格按钮组件
 * 采用 cva + data-slot 模式，参考 shadcn/ui button.tsx
 *
 * Variants: default | secondary | outline | ghost | destructive | gradient
 * Sizes: xs | sm | default | lg | icon | icon-xs | icon-sm | icon-lg
 * States: hover | active | focus | disabled | loading
 */
const buttonVariants = cva(
  [
    'inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap font-semibold',
    'rounded-xl transition-all duration-200 ease-out active:scale-[0.98]',
    'outline-none focus-visible:ring-[3px] focus-visible:ring-ring/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background',
    'disabled:pointer-events-none disabled:opacity-40 disabled:active:scale-100',
    'aria-invalid:border-destructive aria-invalid:ring-destructive/20',
    '[&>svg]:pointer-events-none [&>svg]:shrink-0 [&>svg:not([class*=size-])]:size-4',
  ].join(' '),
  {
    variants: {
      variant: {
        default: 'bg-primary text-white shadow-glow-sm hover:shadow-glow hover:bg-primary-deep',
        secondary: 'bg-muted text-ink border border-border hover:bg-gray-100',
        outline: 'bg-transparent text-ink border border-border hover:border-primary/40 hover:text-primary hover:shadow-glow-sm',
        ghost: 'bg-transparent text-subtext hover:text-ink hover:bg-white/60',
        destructive: 'bg-destructive text-white shadow-sm hover:bg-danger-600 hover:shadow-md',
        gradient: 'bg-gradient-to-r from-primary via-primary-deep to-violet-600 text-white shadow-glow-sm hover:shadow-glow',
      },
      size: {
        xs: 'h-6 gap-1 rounded-md px-2 text-xs',
        sm: 'h-9 px-3 text-sm rounded-lg gap-1.5',
        default: 'h-10 px-4 text-sm rounded-xl gap-2',
        lg: 'h-12 px-6 text-base rounded-xl gap-2',
        icon: 'h-10 w-10 rounded-xl',
        'icon-xs': 'size-6 rounded-md',
        'icon-sm': 'size-9 rounded-lg',
        'icon-lg': 'size-12 rounded-xl',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
  fullWidth?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading = false, fullWidth = false, disabled, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        data-slot="button"
        data-variant={variant}
        data-size={size}
        disabled={disabled || loading}
        aria-busy={loading || undefined}
        className={cn(buttonVariants({ variant, size }), fullWidth && 'w-full', className)}
        {...props}
      >
        {loading && (
          <svg
            className="animate-spin h-4 w-4 -ml-0.5"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        )}
        {children}
      </button>
    );
  },
);

Button.displayName = 'Button';

export { buttonVariants };
