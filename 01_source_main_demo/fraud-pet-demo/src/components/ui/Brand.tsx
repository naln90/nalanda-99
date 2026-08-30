import { GraduationCap } from 'lucide-react';
import { cn } from '../../lib/utils';
import { siteConfig } from '../../config/site';

interface BrandProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'light' | 'dark';
  showText?: boolean;
  className?: string;
}

/**
 * 诈醒学集品牌标识：中性学习图标（毕业帽）+ 渐变光环
 * 注：产品名「诈醒学集」按需求保留，但图形标识不再绑定“防护/反诈”，
 * 改为体现“AI 主题学习平台”的中性符号，使平台外壳与“可配置主题”定位一致。
 *
 * 满足规则:
 * - correct-brand-logos (品牌资产一致使用)
 * - reduced-motion (光环动画在 reduced-motion 下禁用)
 * - aria-labels (品牌区域有可访问标签)
 */
export default function Brand({
  size = 'md',
  variant = 'light',
  showText = true,
  className,
}: BrandProps) {
  const dims = {
    sm: { box: 'w-9 h-9', icon: 18, title: 'text-base', sub: 'text-[10px]' },
    md: { box: 'w-11 h-11', icon: 22, title: 'text-lg', sub: 'text-[11px]' },
    lg: { box: 'w-16 h-16', icon: 32, title: 'text-2xl', sub: 'text-xs' },
  }[size];

  return (
    <div
      className={cn('flex items-center gap-3', className)}
      role="img"
      aria-label={`${siteConfig.brandName} · ${siteConfig.tagline}`}
    >
      <div className="relative">
        <div
          className={cn(
            dims.box,
            'rounded-2xl flex items-center justify-center shadow-glow-sm',
            'bg-gradient-to-br from-primary via-primary-deep to-violet-600',
            'motion-safe:transition-transform motion-safe:hover:scale-105',
          )}
        >
          <GraduationCap size={dims.icon} className="text-white" strokeWidth={2.2} />
        </div>
        {/* 呼吸光环 — reduced-motion 下静止 */}
        <div
          className={cn(
            'absolute inset-0 rounded-2xl bg-primary/40 blur-md -z-10',
            'motion-safe:animate-pulse-soft',
          )}
          aria-hidden="true"
        />
      </div>
      {showText && (
        <div className="leading-tight">
          <h1
            className={cn(
              dims.title,
              'font-extrabold tracking-tight',
              variant === 'dark' ? 'text-white' : 'text-ink',
            )}
          >
            诈醒<span className="text-gradient">学集</span>
          </h1>
          <p
            className={cn(
              dims.sub,
              variant === 'dark' ? 'text-slate-300' : 'text-subtext',
            )}
          >
            {siteConfig.tagline}
          </p>
        </div>
      )}
    </div>
  );
}
