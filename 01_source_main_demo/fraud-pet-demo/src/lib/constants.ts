/**
 * 诈醒学集 — 全局共享常量
 * 避免在多个组件中重复定义维度颜色、图标等映射
 */

/** 综合能力维度颜色映射 */
export const DIMENSION_COLORS: Record<string, string> = {
  '辨识力': '#ef4444',
  '判断力': '#f97316',
  '应变力': '#22c55e',
  '实证力': '#3b82f6',
  '协作力': '#a855f7',
};

/** 综合能力维度图标映射 */
export const DIMENSION_ICONS: Record<string, string> = {
  '辨识力': '🔍',
  '判断力': '🧠',
  '应变力': '🛡️',
  '实证力': '📋',
  '协作力': '🤝',
};

/** 获取维度颜色，缺省返回 fallback 色 */
export function getDimensionColor(dim: string, fallback = '#f97316'): string {
  return DIMENSION_COLORS[dim] ?? fallback;
}
