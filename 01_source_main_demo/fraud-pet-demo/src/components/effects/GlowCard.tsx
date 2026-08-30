/**
 * GlowCard — 光泽扫过 / 浮动光晕卡片
 *
 * 在普通卡片基础上增加 hover 时光泽扫过效果，
 * 以及微光边框光晕。
 */
import type { ReactNode } from 'react';

type GlowCardProps = {
  children: ReactNode;
  className?: string;
  /** 光泽颜色，默认 primary 蓝 */
  glowColor?: string;
  /** 是否禁用 hover 光效 */
  noHover?: boolean;
};

const DEFAULT_GLOW = 'rgba(59,130,246,0.15)';

export default function GlowCard({ children, className = '', glowColor = DEFAULT_GLOW, noHover = false }: GlowCardProps) {
  return (
    <div
      className={`relative group overflow-hidden rounded-2xl bg-surface-strong border border-border shadow-sm ${noHover ? '' : 'transition-shadow duration-300 hover:shadow-lg'} ${className}`}
    >
      {/* 光泽扫过层 */}
      {!noHover && (
        <div
          className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 motion-safe:animate-shine z-10"
          style={{
            background: `linear-gradient(105deg, transparent 35%, ${glowColor} 48%, transparent 62%)`,
            backgroundSize: '200% 100%',
          }}
          aria-hidden="true"
        />
      )}
      {/* 边框光晕 */}
      <div
        className="pointer-events-none absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"
        style={{
          boxShadow: `inset 0 0 24px ${glowColor}`,
        }}
        aria-hidden="true"
      />
      {children}
    </div>
  );
}
