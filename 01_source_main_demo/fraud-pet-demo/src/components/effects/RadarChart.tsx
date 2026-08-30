/**
 * RadarChart — SVG 雷达图
 *
 * 展示综合能力多维度得分，可用于测评结果页 / 宠物档案页。
 * 支持 3-6 个维度，自动计算多边形顶点，含动画过渡。
 */
import { useEffect, useState } from 'react';

type Dimension = {
  label: string;
  value: number; // 0-100
  color?: string;
};

type RadarChartProps = {
  dimensions: Dimension[];
  /** 图表大小（px），默认 280 */
  size?: number;
  /** 维度标签字号 */
  labelSize?: number;
  className?: string;
};

function polarToCartesian(cx: number, cy: number, r: number, angle: number) {
  const rad = ((angle - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

export default function RadarChart({ dimensions, size = 280, labelSize = 12, className = '' }: RadarChartProps) {
  const n = dimensions.length;
  const cx = size / 2;
  const cy = size / 2;
  const maxR = size * 0.36;
  const levels = 4; // 同心圆层数

  const [animated, setAnimated] = useState(false);
  useEffect(() => { setAnimated(true); }, []);

  const fillColor = 'rgba(59,130,246,0.15)';
  const strokeColor = 'rgba(59,130,246,0.55)';
  const gridColor = 'rgba(148,163,184,0.18)';
  const labelColor = '#64748b';

  // 数据多边形顶点
  const dataPoints = dimensions.map((d, i) => {
    const angle = (360 / n) * i;
    const r = (d.value / 100) * maxR;
    return polarToCartesian(cx, cy, r, angle);
  });
  const dataPath = dataPoints.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ') + 'Z';

  // 背景网格
  const gridLines = Array.from({ length: levels + 1 }, (_, lv) => {
    const r = (lv / levels) * maxR;
    const pts = Array.from({ length: n }, (_, i) => polarToCartesian(cx, cy, r, (360 / n) * i));
    return pts.map((p, j) => `${j === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ') + 'Z';
  });

  const axes = dimensions.map((_, i) => {
    const outer = polarToCartesian(cx, cy, maxR, (360 / n) * i);
    return `M${cx},${cy} L${outer.x},${outer.y}`;
  });

  return (
    <svg
      viewBox={`0 0 ${size} ${size}`}
      width={size}
      height={size}
      className={`overflow-visible ${className}`}
      role="img"
      aria-label={`雷达图：${dimensions.map((d) => `${d.label} ${d.value}分`).join('，')}`}
    >
      {/* 同心网格 */}
      {gridLines.map((path, i) => (
        <path key={`grid-${i}`} d={path} fill="none" stroke={gridColor} strokeWidth={i === levels ? 1.5 : 0.8} />
      ))}
      {/* 轴线 */}
      {axes.map((_, i) => (
        <line key={`axis-${i}`} x1={cx} y1={cy} x2={cx} y2={cy - maxR} stroke={gridColor} strokeWidth={0.8}
          transform={`rotate(${(360/n)*i}, ${cx}, ${cy})`} />
      ))}
      {/* 数据多边形 */}
      {animated && (
        <path
          d={dataPath}
          fill={fillColor}
          stroke={strokeColor}
          strokeWidth={2}
          className="transition-all duration-700 ease-out"
          style={{ transitionProperty: 'd' }}
        />
      )}
      {/* 数据节点 */}
      {dataPoints.map((pt, i) => (
        <circle key={`dot-${i}`} cx={pt.x} cy={pt.y} r={4} fill="white" stroke={strokeColor} strokeWidth={2.5}
          className="motion-safe:animate-radar-pulse" style={{ animationDelay: `${i * 0.12}s` }} />
      ))}
      {/* 标签 */}
      {dimensions.map((d, i) => {
        const angle = (360 / n) * i;
        const labelR = maxR + 22;
        const pos = polarToCartesian(cx, cy, labelR, angle);
        const textAnchor = pos.x < cx - 4 ? 'end' : pos.x > cx + 4 ? 'start' : 'middle';
        return (
          <text
            key={`label-${i}`}
            x={pos.x}
            y={pos.y}
            textAnchor={textAnchor}
            dominantBaseline="middle"
            fontSize={labelSize}
            fill={labelColor}
            fontWeight={600}
          >
            {d.label}
          </text>
        );
      })}
    </svg>
  );
}
