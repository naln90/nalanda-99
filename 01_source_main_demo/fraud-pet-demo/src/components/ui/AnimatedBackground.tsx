/**
 * 应用内动态背景 — 高级感网格 + 流动光斑 + 顶部柔光
 *
 * 满足规则:
 * - reduced-motion (尊重 prefers-reduced-motion，禁用浮动动画)
 * - parallax-subtle (微妙的视差感，不致眩晕)
 * - effects-match-style (与玻璃拟态风格一致的柔光)
 * - z-index-management (固定 -z-10，不干扰内容层)
 */
export default function AnimatedBackground() {
  return (
    <div
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
      aria-hidden="true"
    >
      {/* 基底网格 — 微透明 */}
      <div className="absolute inset-0 bg-grid opacity-50" />

      {/* 渐变光斑层 — prefers-reduced-motion 下静止 */}
      <div
        className="absolute -top-32 -left-24 h-[460px] w-[460px] rounded-full blur-3xl motion-safe:animate-float-slow"
        style={{
          background:
            'radial-gradient(circle, rgba(79,124,255,0.20), transparent 70%)',
        }}
      />
      <div
        className="absolute top-1/3 -right-32 h-[520px] w-[520px] rounded-full blur-3xl motion-safe:animate-float"
        style={{
          background:
            'radial-gradient(circle, rgba(139,92,246,0.18), transparent 70%)',
        }}
      />
      <div
        className="absolute -bottom-40 left-1/3 h-[460px] w-[460px] rounded-full blur-3xl motion-safe:animate-float-slow"
        style={{
          background:
            'radial-gradient(circle, rgba(6,182,212,0.12), transparent 70%)',
        }}
      />

      {/* 装饰性环形光晕 */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[800px] w-[800px] rounded-full opacity-[0.04] motion-safe:animate-spin-slow"
        style={{
          background:
            'conic-gradient(from 0deg, transparent, rgba(79,124,255,0.4), transparent, rgba(139,92,246,0.4), transparent)',
        }}
      />

      {/* 顶部柔和高光 */}
      <div className="absolute inset-x-0 top-0 h-64 bg-gradient-to-b from-white/80 to-transparent" />

      {/* 底部渐隐 */}
      <div className="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-white/60 to-transparent" />
    </div>
  );
}
