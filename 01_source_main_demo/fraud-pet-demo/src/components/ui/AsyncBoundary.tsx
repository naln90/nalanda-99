import type { ReactNode } from 'react';
import { RefreshCw } from 'lucide-react';
import { Alert } from './Alert';
import { Skeleton } from './Skeleton';
import { EmptyState } from './EmptyState';
import { Button } from './Button';

/**
 * AsyncBoundary — 统一异步数据获取的「三态 + 空态」视觉边界
 *
 * 与 <useAsync> 配套使用，把此前散落在各页面的 loading/error/空态 渲染归一为
 * 一处声明式封装：
 *   - loading  → Skeleton 骨架（可自定义 loadingFallback）
 *   - error    → Alert(danger) + 带「重试」按钮（点击调用 onRetry）
 *   - 无数据   → EmptyState（可自定义 emptyFallback）
 *   - 成功     → children(data)
 *
 * 用法：
 *   <AsyncBoundary
 *     loading={loading}
 *     error={error}
 *     data={data}
 *     isEmpty={(d) => d.list.length === 0}
 *     onRetry={refetch}
 *   >
 *     {(d) => <MyList items={d.list} />}
 *   </AsyncBoundary>
 */
export interface AsyncBoundaryProps<T> {
  loading: boolean;
  /** 友好错误对象（至少有 message 字段），null 表示无错误 */
  error: { message: string } | null;
  /** 成功数据；undefined 视为尚未加载（优先于 error 展示 loading） */
  data: T | undefined;
  /** 判断是否「空数据」（如空数组/空对象），用于展示空态 */
  isEmpty?: (data: T) => boolean;
  /** 重试回调，传入后错误态展示「重试」按钮 */
  onRetry?: () => void;
  /** 自定义加载态；不传则用默认骨架 */
  loadingFallback?: ReactNode;
  /** 自定义空态；不传则用默认 EmptyState */
  emptyFallback?: ReactNode;
  /** 成功态渲染函数，接收已保证非空的数据 */
  children: (data: T) => ReactNode;
}

function DefaultLoading() {
  return (
    <div className="space-y-3 py-4" aria-busy="true" aria-live="polite">
      {[0, 1, 2].map((i) => (
        <Skeleton key={i} className="h-20 w-full rounded-2xl" />
      ))}
    </div>
  );
}

function DefaultEmpty() {
  return (
    <EmptyState
      title="暂无数据"
      description="这里还没有内容，稍后再来看看吧。"
    />
  );
}

export function AsyncBoundary<T>({
  loading,
  error,
  data,
  isEmpty,
  onRetry,
  loadingFallback,
  emptyFallback,
  children,
}: AsyncBoundaryProps<T>) {
  if (loading) {
    return <>{loadingFallback ?? <DefaultLoading />}</>;
  }
  if (error) {
    return (
      <Alert variant="danger" title="加载失败">
        <div className="flex flex-col gap-3">
          <span>{error.message}</span>
          {onRetry && (
            <div>
              <Button variant="outline" size="sm" onClick={onRetry}>
                <RefreshCw size={14} />
                重试
              </Button>
            </div>
          )}
        </div>
      </Alert>
    );
  }
  const isEmptyData = data === undefined || (isEmpty ? isEmpty(data) : false);
  if (isEmptyData) {
    return <>{emptyFallback ?? <DefaultEmpty />}</>;
  }
  return <>{children(data as T)}</>;
}
