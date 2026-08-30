/**
 * FloatingParticles — 浮动粒子背景装饰
 *
 * 在容器内渲染若干柔和浮动的光点，营造空间感。
 * 可叠加在卡片/页面顶部，pointer-events-none 不干扰交互。
 */
import { useMemo } from 'react';

type Particle = {
  id: number;
  left: number;
  top: number;
  size: number;
  duration: number;
  delay: number;
  opacity: number;
  color: string;
};

type FloatingParticlesProps = {
  /** 粒子数量，默认 14 */
  count?: number;
  /** 颜色主题，默认 primary */
  theme?: 'primary' | 'warm' | 'mixed';
  className?: string;
};

const THEMES: Record<string, string[]> = {
  primary: ['rgba(59,130,246,0.4)', 'rgba(139,92,246,0.35)', 'rgba(6,182,212,0.35)'],
  warm: ['rgba(245,158,11,0.45)', 'rgba(236,72,153,0.35)', 'rgba(251,191,36,0.45)'],
  mixed: ['rgba(59,130,246,0.4)', 'rgba(16,185,129,0.4)', 'rgba(245,158,11,0.4)', 'rgba(139,92,246,0.35)'],
};

export default function FloatingParticles({ count = 14, theme = 'primary', className = '' }: FloatingParticlesProps) {
  const particles = useMemo<Particle[]>(() => {
    const colors = THEMES[theme] ?? THEMES.primary;
    return Array.from({ length: count }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      top: Math.random() * 100,
      size: 3 + Math.random() * 7,
      duration: 4 + Math.random() * 6,
      delay: Math.random() * 3,
      opacity: 0.3 + Math.random() * 0.5,
      color: colors[i % colors.length],
    }));
  }, [count, theme]);

  return (
    <div className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`} aria-hidden="true">
      {particles.map((p) => (
        <span
          key={p.id}
          className="absolute rounded-full motion-safe:animate-float"
          style={{
            left: `${p.left}%`,
            top: `${p.top}%`,
            width: `${p.size}px`,
            height: `${p.size}px`,
            background: p.color,
            opacity: p.opacity,
            boxShadow: `0 0 ${p.size * 2}px ${p.color}`,
            animationDuration: `${p.duration}s`,
            animationDelay: `${p.delay}s`,
          }}
        />
      ))}
    </div>
  );
}
