/**
 * 类名合并工具 — 过滤 falsy 值后用空格拼接
 * 参考 shadcn/ui 的 cn() 简化实现（无 clsx/tailwind-merge 依赖）
 */
export type ClassValue = string | number | null | undefined | false;

export function cn(...inputs: ClassValue[]): string {
  return inputs.filter(Boolean).join(' ');
}
