import { type ReactNode } from 'react';
import { cn } from '../../lib/utils';
import { Card, CardAction, CardDescription, CardFooter, CardHeader, CardTitle } from './Card';
import { Badge } from './Badge';

/**
 * StatCard — 统计卡片
 * 参考 shadcn/ui dashboard-01 SectionCards 模式
 * 含 CardHeader / CardTitle / CardDescription / CardAction(Badge) / CardFooter
 */
export interface StatCardProps {
  label: string;
  value: ReactNode;
  trend?: {
    value: string;
    direction: 'up' | 'down' | 'neutral';
  };
  footer?: {
    title: ReactNode;
    description: ReactNode;
  };
  className?: string;
  accent?: 'primary' | 'success' | 'warning' | 'danger';
}

const accentGradient: Record<NonNullable<StatCardProps['accent']>, string> = {
  primary: 'from-primary/5 to-card',
  success: 'from-safe-50 to-card',
  warning: 'from-warning-50 to-card',
  danger: 'from-danger-50 to-card',
};

export function StatCard({ label, value, trend, footer, className, accent = 'primary' }: StatCardProps) {
  const trendIcon = trend?.direction === 'up' ? '↗' : trend?.direction === 'down' ? '↘' : '→';
  const trendClass =
    trend?.direction === 'up'
      ? 'text-safe-600'
      : trend?.direction === 'down'
        ? 'text-danger-600'
        : 'text-subtext';
  return (
    <Card className={cn('@container/card bg-gradient-to-t shadow-xs', accentGradient[accent], className)}>
      <CardHeader>
        <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
          {value}
        </CardTitle>
        {trend && (
          <CardAction>
            <Badge variant="outline" className={trendClass}>
              <span aria-hidden>{trendIcon}</span>
              {trend.value}
            </Badge>
          </CardAction>
        )}
      </CardHeader>
      {footer && (
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium text-ink">{footer.title}</div>
          <div className="text-muted-foreground">{footer.description}</div>
        </CardFooter>
      )}
    </Card>
  );
}
