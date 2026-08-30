import { Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { CalendarRange, LogOut, Megaphone, Menu, School, Sparkles, TrendingUp, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import AnimatedBackground from '../ui/AnimatedBackground';
import Brand from '../ui/Brand';
import { cn } from '../../lib/utils';

/**
 * SchoolLayout — 校方发布端布局（V3.0 双端口）
 * 导航：主题与任务包 / 学习情况 / 守护活动管理
 * 仅 role === 'school' 可进入；学生访问自动跳回学生端首页
 */
export default function SchoolLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const currentUser = useAppStore((state) => state.currentUser);
  const role = useAppStore((state) => state.role);
  const logout = useAppStore((state) => state.logout);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    setMobileNavOpen(false);
  }, [location.pathname]);

  if (!currentUser) {
    return <Navigate to="/login" replace />;
  }
  const effectiveRole = role ?? currentUser.role ?? 'student';
  if (effectiveRole !== 'school') {
    return <Navigate to="/home" replace />;
  }

  const navs = [
    { path: '/school/theme', name: '主题与任务包', icon: CalendarRange },
    { path: '/school/learning', name: '学习情况', icon: TrendingUp },
    { path: '/school/activity', name: '守护活动管理', icon: Megaphone },
  ];

  const isActive = (path: string) => location.pathname.startsWith(path);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const sidebarContent = (
    <div className="flex flex-col h-full">
      <div className="px-4 pt-4 pb-1.5 flex items-center gap-1.5">
        <School size={12} className="text-primary" aria-hidden="true" />
      </div>

      <nav className="flex-1 px-2.5 space-y-1 overflow-y-auto scrollbar-thin" aria-label="校方主导航">
        {navs.map((nav) => {
          const Icon = nav.icon;
          const active = isActive(nav.path);
          return (
            <button
              key={nav.path}
              onClick={() => navigate(nav.path)}
              aria-current={active ? 'page' : undefined}
              className={cn(
                'group w-full flex items-center gap-2.5 px-2.5 py-2.5 rounded-xl text-[13px] font-semibold transition-all duration-200 text-left',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background',
                active
                  ? 'bg-gradient-to-r from-primary to-primary-deep text-white shadow-glow'
                  : 'text-subtext hover:text-ink hover:bg-white/70',
              )}
            >
              <Icon
                size={16}
                className={cn('flex-shrink-0 transition-colors', active ? 'text-white' : 'text-subtext group-hover:text-ink')}
                aria-hidden="true"
              />
              <div className="min-w-0 flex-1">
                <div className="truncate leading-tight">{nav.name}</div>
              </div>
            </button>
          );
        })}
      </nav>

      {/* 边界提示 */}
      <div className="px-2.5 pb-2.5">
        <div className="rounded-2xl bg-gradient-to-br from-primary/10 via-primary/5 to-transparent border border-primary/15 p-3 text-[10px] text-subtext leading-relaxed">
          系统仅负责活动展示、共建解锁与通知衔接；活动报名、签到与执行由学校线下完成。
        </div>
      </div>

    </div>
  );

  return (
    <div className="min-h-screen bg-bg text-ink font-sans flex relative">
      <AnimatedBackground />

      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-toast focus:px-4 focus:py-2 focus:bg-primary focus:text-white focus:rounded-lg focus:shadow-glow"
      >
        跳到主内容
      </a>

      {/* 桌面端侧边栏 */}
      <aside
        className="hidden md:flex flex-col fixed left-0 top-0 h-screen w-[200px] glass border-r border-white/60 z-sticky"
        role="navigation"
        aria-label="校方侧边导航"
      >
        {sidebarContent}
      </aside>

      {/* 移动端顶部导航 */}
      <header className="md:hidden fixed top-0 left-0 right-0 z-sticky glass border-b border-white/60" role="banner">
        <div className="px-4 flex items-center h-[60px]">
          <button
            onClick={() => navigate('/school/theme')}
            className="mr-auto transition-transform motion-safe:hover:scale-[1.02] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded-lg"
            aria-label="返回校方首页"
          >
            <Brand size="md" />
          </button>
          <button
            onClick={() => setMobileNavOpen((v) => !v)}
            className="w-10 h-10 rounded-xl bg-white/70 border border-white/60 flex items-center justify-center text-ink transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            aria-label={mobileNavOpen ? '关闭导航菜单' : '打开导航菜单'}
            aria-expanded={mobileNavOpen}
            aria-controls="school-mobile-nav"
          >
            {mobileNavOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {mobileNavOpen && (
          <nav id="school-mobile-nav" className="border-t border-white/60 glass animate-slide-up" aria-label="校方移动端导航">
            <div className="px-4 py-3 space-y-1">
              {navs.map((nav) => {
                const Icon = nav.icon;
                const active = isActive(nav.path);
                return (
                  <button
                    key={nav.path}
                    onClick={() => navigate(nav.path)}
                    aria-current={active ? 'page' : undefined}
                    className={cn(
                      'w-full flex items-center gap-3.5 px-4 py-3 rounded-xl text-base font-medium transition-all',
                      active ? 'bg-gradient-to-r from-primary to-primary-deep text-white shadow-glow-sm' : 'text-ink hover:bg-white/60',
                    )}
                  >
                    <Icon size={20} aria-hidden="true" />
                    <div className="text-left">{nav.name}</div>
                  </button>
                );
              })}
            </div>
          </nav>
        )}
      </header>

      {/* 桌面端顶部导航栏 */}
      <header
        className="hidden md:flex fixed top-0 left-[200px] right-0 h-[60px] glass border-b border-white/60 z-sticky items-center justify-between px-6"
        role="banner"
        aria-label="校方顶部导航"
      >
        <button
          onClick={() => navigate('/school/theme')}
          className="transition-transform motion-safe:hover:scale-[1.02] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background rounded-lg"
          aria-label="返回校方首页"
        >
          <Brand size="sm" />
        </button>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 pl-3 border-l border-white/60">
            <div
              className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary-deep flex items-center justify-center text-white text-xs font-bold shadow-glow-sm flex-shrink-0"
              aria-hidden="true"
            >
              校
            </div>
            <div className="leading-tight hidden lg:block text-left">
              <p className="text-xs font-bold text-ink truncate max-w-[120px]">{currentUser.ownerId}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            title="退出登录"
            aria-label="退出登录"
            className="w-8 h-8 flex items-center justify-center rounded-xl bg-white/70 border border-white/60 text-subtext hover:text-danger hover:border-danger/40 hover:bg-danger/5 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 flex-shrink-0"
          >
            <LogOut size={16} aria-hidden="true" />
          </button>
        </div>
      </header>

      <div className="flex-1 md:ml-[200px] min-w-0 flex flex-col">
        <main id="main-content" className="relative flex-1 w-full pt-[60px] md:pt-[72px]" role="main" tabIndex={-1}>
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
            <div key={location.pathname} className="page-enter">
              <Outlet />
            </div>
          </div>
        </main>

        <footer className="border-t border-white/60 glass" role="contentinfo">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-[11px] text-subtext">
            <span className="flex items-center gap-1.5">
              <Sparkles size={12} className="text-primary" aria-hidden="true" />
              诈醒学集 · 校方发布端
            </span>
            <span className="sm:text-right leading-relaxed">
              仅用于校园反诈教育管理，不替代公安机关、金融机构或学校管理部门判断
            </span>
          </div>
        </footer>
      </div>
    </div>
  );
}
