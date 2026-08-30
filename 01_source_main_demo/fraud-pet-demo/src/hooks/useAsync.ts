import { useCallback, useEffect, useRef, useState } from 'react';
import { toFriendlyError, type ApiError } from '../api/client';

/**
 * useAsync — 统一异步数据获取 hook（补齐前端数据获取层一致性）
 *
 * 解决痛点：此前 36 个页面各自在 useEffect 中手写 `setLoading + try/catch +
 * toast`，错误处理与加载态不统一，易漏 catch。本 hook 将 `data / loading /
 * error / refetch` 三态归一，并自动用 `toFriendlyError` 把网络/HTTP 错误转成
 * 对用户友好的 ApiError；支持依赖变化自动重取，并内置请求竞态保护（deps
 * 变化触发的旧请求结果不会覆盖新请求）。
 *
 * 用法：
 *   const { data, loading, error, refetch } = useAsync(
 *     () => api.getLearningMarket(tab),
 *     { deps: [tab] },
 *   );
 *   // data 为 undefined 表示尚未成功加载；loading 表示进行中；error 为 ApiError
 *
 * 配合 <AsyncBoundary> 可一次性封装 loading/error/空态 视觉。
 */

export interface AsyncResult<T> {
  /** 最近一次成功的数据；初始为 undefined */
  data: T | undefined;
  loading: boolean;
  error: ApiError | null;
  /** 手动重新拉取（会重置 loading/error） */
  refetch: () => void;
}

export function useAsync<T>(
  asyncFn: () => Promise<T>,
  options: { immediate?: boolean; deps?: ReadonlyArray<unknown> } = {},
): AsyncResult<T> {
  const { immediate = true, deps = [] } = options;
  const [data, setData] = useState<T | undefined>(undefined);
  const [loading, setLoading] = useState<boolean>(immediate);
  const [error, setError] = useState<ApiError | null>(null);

  // 始终引用最新闭包，避免把 asyncFn 放进 deps 导致无限循环
  const fnRef = useRef(asyncFn);
  fnRef.current = asyncFn;
  // 请求序号：用于竞态保护
  const reqIdRef = useRef(0);

  const run = useCallback(() => {
    const reqId = ++reqIdRef.current;
    setLoading(true);
    setError(null);
    fnRef.current().then(
      (result) => {
        if (reqId === reqIdRef.current) {
          setData(result);
          setLoading(false);
        }
      },
      (err: unknown) => {
        if (reqId === reqIdRef.current) {
          setError(toFriendlyError(err));
          setLoading(false);
        }
      },
    );
  }, []);

  useEffect(() => {
    if (immediate) run();
    // deps 由调用方显式提供；immediate 仅控制首次是否自动执行
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading, error, refetch: run };
}
