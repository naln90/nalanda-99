/**
 * CountUp — 数字滚动跳动动画
 *
 * 从 0 平滑递增到目标值，适合展示成长值/分数/排名等数字。
 * 尊重 prefers-reduced-motion：直接显示目标值，无动画。
 */
import { useEffect, useRef, useState } from 'react';

type CountUpProps = {
  /** 目标数值 */
  value: number;
  /** 动画时长（ms），默认 800 */
  duration?: number;
  /** 是否添加 "+" 前缀（默认 false） */
  showPlus?: boolean;
  /** 自定义类名 */
  className?: string;
  /** 是否在数值变化时播放跳动动画 */
  pulseOnComplete?: boolean;
};

export default function CountUp({ value, duration = 800, showPlus = false, className = '', pulseOnComplete = true }: CountUpProps) {
  const [display, setDisplay] = useState(0);
  const [pulsing, setPulsing] = useState(false);
  const frameRef = useRef<number>(0);
  const prefersReduced = useRef(false);

  useEffect(() => {
    // 检测 reduced-motion
    prefersReduced.current = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced.current) {
      setDisplay(value);
      return;
    }
    const startTime = performance.now();
    const startValue = display;
    const delta = value - startValue;

    const step = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // easeOutCubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(startValue + delta * eased));
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(step);
      } else {
        if (pulseOnComplete) {
          setPulsing(true);
          setTimeout(() => setPulsing(false), 400);
        }
      }
    };
    frameRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frameRef.current);
  }, [value]);

  return (
    <span
      className={`inline-block ${pulsing ? 'motion-safe:animate-count-up' : ''} ${className}`}
      aria-label={`${value}`}
    >
      {showPlus && value > 0 ? '+' : ''}{prefersReduced.current ? value : display}
    </span>
  );
}
