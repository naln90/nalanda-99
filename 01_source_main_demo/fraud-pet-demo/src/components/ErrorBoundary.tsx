import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  message: string;
}

/**
 * 全局错误边界：捕获渲染期异常，避免整页白屏（健壮性 / 跨浏览器兼容）。
 * 任何子树渲染崩溃都会回退到友好提示，而非丢失整个应用。
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: '' };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message || '页面渲染出现异常' };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // 仅记录错误类型与组件栈，避免泄露敏感上下文
    console.error('[ErrorBoundary]', error.name, info.componentStack);
  }

  private handleReload = (): void => {
    this.setState({ hasError: false, message: '' });
    window.location.reload();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div
          role="alert"
          style={{
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 16,
            padding: 24,
            textAlign: 'center',
            fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
            color: '#1f2937',
            background: '#f8fafc',
          }}
        >
          <h1 style={{ fontSize: 22, margin: 0 }}>页面遇到了一个小问题</h1>
          <p style={{ margin: 0, color: '#64748b', maxWidth: 420 }}>
            部分内容暂时无法显示，您可以重试恢复。若多次出现，请刷新页面或联系管理员。
          </p>
          <button
            type="button"
            onClick={this.handleReload}
            style={{
              marginTop: 8,
              padding: '10px 22px',
              borderRadius: 10,
              border: 'none',
              background: '#2563eb',
              color: '#fff',
              fontSize: 15,
              cursor: 'pointer',
            }}
          >
            重新加载
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
