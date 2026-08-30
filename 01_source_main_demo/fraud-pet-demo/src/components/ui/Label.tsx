import { forwardRef, type LabelHTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

/**
 * Label — shadcn/ui 风格标签
 * 参考 shadcn/ui label.tsx
 */
export const Label = forwardRef<HTMLLabelElement, LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => (
    <label
      ref={ref}
      data-slot="label"
      className={cn(
        'flex items-center gap-2 text-sm leading-none font-medium text-ink select-none',
        'group-data-[disabled=true]:pointer-events-none group-data-[disabled=true]:opacity-50',
        'peer-disabled:cursor-not-allowed peer-disabled:opacity-50',
        className,
      )}
      {...props}
    />
  ),
);
Label.displayName = 'Label';
