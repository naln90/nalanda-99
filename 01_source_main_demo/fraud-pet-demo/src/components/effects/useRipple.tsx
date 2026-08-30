/**
 * useRipple — 点击波纹效果 Hook
 *
 * 返回 rippleProps 和 rippleElement，在需要波纹的容器上使用。
 * 容器需要 `overflow-hidden relative` 样式。
 *
 * 用法：
 *   const { rippleProps, rippleElement } = useRipple();
 *   <button {...rippleProps} className="relative overflow-hidden">
 *     {rippleElement}
 *     点击我
 *   </button>
 */
import { useCallback, useState } from 'react';

type RippleState = { id: number; x: number; y: number };

export default function useRipple(color = 'rgba(255,255,255,0.3)') {
  const [ripple, setRipple] = useState<RippleState | null>(null);

  const handleClick = useCallback((e: React.MouseEvent<HTMLElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const id = Date.now();
    setRipple({ id, x, y });
    setTimeout(() => setRipple(null), 600);
  }, []);

  const rippleProps = { onClick: handleClick };

  const rippleElement = ripple ? (
    <span
      key={ripple.id}
      className="pointer-events-none absolute rounded-full motion-safe:animate-ripple"
      style={{
        left: ripple.x,
        top: ripple.y,
        width: 80,
        height: 80,
        marginLeft: -40,
        marginTop: -40,
        background: color,
      }}
      aria-hidden="true"
    />
  ) : null;

  return { rippleProps, rippleElement };
}
