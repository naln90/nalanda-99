/**
 * Confetti — 撒花庆祝粒子动画
 *
 * 在指定时长内从顶部散落彩色粒子，用于训练完成、等级提升等庆祝时刻。
 * 尊重 prefers-reduced-motion：启用时粒子静止为柔光点缀。
 */
import { useEffect, useState } from 'react';

type Particle = {
  id: number;
  left: number; // %
  delay: number; // s
  duration: number; // s
  size: number; // px
  color: string;
  rotate: number;
};

const COLORS = ['#F59E0B', '#10B981', '#3B82F6', '#8B5CF6', '#EC4899', '#EF4444', '#FBBF24'];

const SHAPES = ['■', '●', '▲', '★', '◆', '♥'];

type ConfettiProps = {
  /** 是否激活 */
  active: boolean;
  /** 粒子数量，默认 40 */
  count?: number;
  /** 持续时长（ms），结束后自动清理，默认 4000 */
  duration?: number;
  /** 结束回调 */
  onComplete?: () => void;
};

export default function Confetti({ active, count = 40, duration = 4000, onComplete }: ConfettiProps) {
  const [particles, setParticles] = useState<Particle[]>([]);

  useEffect(() => {
    if (!active) {
      setParticles([]);
      return;
    }
    const next: Particle[] = Array.from({ length: count }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      delay: Math.random() * 0.6,
      duration: 2.2 + Math.random() * 1.6,
      size: 8 + Math.random() * 10,
      color: COLORS[i % COLORS.length],
      rotate: Math.random() * 360,
    }));
    setParticles(next);
    const timer = setTimeout(() => {
      setParticles([]);
      onComplete?.();
    }, duration);
    return () => clearTimeout(timer);
  }, [active, count, duration, onComplete]);

  if (!active || particles.length === 0) return null;

  return (
    <div className="pointer-events-none fixed inset-0 z-50 overflow-hidden" aria-hidden="true">
      {particles.map((p) => (
        <span
          key={p.id}
          className="absolute top-0 motion-safe:animate-confetti"
          style={{
            left: `${p.left}%`,
            fontSize: `${p.size}px`,
            color: p.color,
            animationDelay: `${p.delay}s`,
            animationDuration: `${p.duration}s`,
            transform: `rotate(${p.rotate}deg)`,
            lineHeight: 1,
          }}
        >
          {SHAPES[p.id % SHAPES.length]}
        </span>
      ))}
    </div>
  );
}
