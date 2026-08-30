import { Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  Bell,
  BookOpen,
  CalendarCheck,
  ClipboardList,
  FileUp,
  FileSearch,
  HandHeart,
  Home,
  LayoutList,
  Lightbulb,
  LogOut,
  Menu,
  Shield,
  Sparkles,
  Sprout,
  Store,
  Target,
  TrendingUp,
  X,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { resolvePetAvatar, resolvePetName } from '../../lib/pet-utils';
import AnimatedBackground from '../ui/AnimatedBackground';
import { FloatingParticles } from '../effects';
import Brand from '../ui/Brand';
import { siteConfig } from '../../config/site';
import { cleanTheme } from '../../lib/themeProfile';
import { cn } from '../../lib/utils';

export default function StudentLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const currentUser = useAppStore((state) => state.currentUser);
  const pet = useAppStore((state) => state.pet);
  const logout = useAppStore((state) => state.logout);
  const activeLearningTheme = useAppStore((state) => state.activeLearningTheme);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  // 路由切换时关闭移动端导航
  useEffect(() => {
    setMobileNavOpen(false);
  }, [location.pathname]);

  // 未登录时用 <Navigate> 组件重定向
  if (!currentUser) {
    return <Navigate to="/login" replace />;
  }

  // 主题专区标题：已激活学习计划时动态显示当前主题名，否则回退中性“主题专区”
  const themeSectionTitle = activeLearningTheme
    ? `当前主题 · ${cleanTheme(activeLearningTheme)}`
    : siteConfig.navGroups.theme;

  // 导航按功能分组，移动端抽屉与桌面侧栏共用，功能入口全部保留
  const navSections: { title: string; items: { path: string; name: string; icon: typeof Home }[] }[] = [
    {
      title: '主导航',
      items: [
        { path: '/home', name: '首页', icon: Home },
        { path: '/learning', name: '主题学习', icon: BookOpen },
        { path: '/guard', name: '守护共建', icon: HandHeart },
      ],
    },
    {
      title: '我的学习',
      items: [
        { path: '/learning/goal', name: '发布学习目标', icon: Target },
        { path: '/learning/workspace', name: '学习工作台', icon: CalendarCheck },
        { path: '/learning/artifacts', name: '成果工坊', icon: FileUp },
        { path: '/learning/market', name: '学习集市', icon: Store },
        { path: '/learning/collaboration', name: '协作与社交', icon: LayoutList },
        { path: '/learning/recommend', name: '推荐与督促', icon: Lightbulb },
        { path: '/learning/activities', name: '守护活动', icon: Sprout },
      ],
    },
    {
      title: themeSectionTitle,
      items: [
        { path: '/training', name: siteConfig.themeNavNames.training, icon: ClipboardList },
        { path: '/pet', name: siteConfig.themeNavNames.pet, icon: Shield },
        { path: '/knowledge', name: siteConfig.themeNavNames.knowledge, icon: BookOpen },
        ...(import.meta.env.VITE_ENABLE_EVIDENCE_CENTER === 'true'
          ? [{ path: '/evidence-center', name: '证据中心', icon: FileSearch } as const]
          : []),
      ],
    },
    // 以下功能按方案§1.3暂缓：导航隐藏，路由保留
    // { path: '/case-library', name: '案例库', icon: BookOpen },
    // { path: '/counselor/dashboard', name: '辅导员看板', icon: TrendingUp },
    // { path: '/admin/audit', name: '人工审核', icon: Shield },
    // { path: '/ranking', name: '成长榜', icon: Award },
  ];

  const isActive = (path: string) => {
    // 主题学习为精确匹配，避免与 /learning/* 学习集市链路冲突
    if (path === '/learning') {
      return location.pathname === '/learning';
    }
    if (path === '/training') {
      return ['/training', '/assessment', '/free-training', '/pet-select'].some(
        (p) => location.pathname.startsWith(p),
      );
    }
    if (path === '/learning/workspace') {
      return ['/learning/workspace', '/task-package', '/training/scenario'].some((p) => location.pathname.startsWith(p));
    }
    return location.pathname.startsWith(path);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* 主导航（分区渲染） */}
      <nav className="flex-1 px-2.5 pt-4 space-y-4 overflow-y-auto scrollbar-thin" aria-label="主导航">
        {navSections.map((section) => (
          <div key={section.title} className="space-y-1">
            <div className="px-2.5 pt-1.5 pb-1">
              <span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-subtext/80">
                {section.title}
              </span>
            </div>
            {section.items.map((nav) => {
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
                    className={cn(
                      'flex-shrink-0 transition-colors',
                      active ? 'text-white' : 'text-subtext group-hover:text-ink',
                    )}
                    aria-hidden="true"
                  />
                  <div className="min-w-0 flex-1">
                    <div className="truncate leading-tight">{nav.name}</div>
                  </div>
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      {/* 中部数据概览 */}
      <div className="px-2.5 pb-2.5">
        <div className="rounded-2xl bg-gradient-to-br from-primary/10 via-primary/5 to-transparent border border-primary/15 p-3">
          <div className="flex items-center gap-1.5 mb-2">
            <TrendingUp size={14} className="text-primary" aria-hidden="true" />
            <span className="text-[11px] font-semibold text-ink">我的训练</span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-xl bg-white/60 border border-white/60 p-2 text-center">
              <div className="text-base font-extrabold text-primary leading-none">
                {pet?.growthValue ?? 0}
              </div>
            </div>
            <div className="rounded-xl bg-white/60 border border-white/60 p-2 text-center">
              <div className="text-base font-extrabold text-ink leading-none">
                {pet?.level ?? 1}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 底部：宠物简况 */}
      <div className="px-2.5 pb-3 pt-2.5 border-t border-white/60">
        {/* 宠物简况 */}
        {pet && (
          <button
            onClick={() => navigate('/pet')}
            className="w-full bg-white/70 border border-white/60 rounded-xl p-2.5 hover:shadow-glow-sm hover:border-primary/30 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 text-left"
            aria-label={`查看宠物 ${resolvePetName(pet)}，等级 ${pet.level}，成长值 ${pet.growthValue}`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl flex-shrink-0" aria-hidden="true">
                {resolvePetAvatar(pet)}
              </span>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-bold text-ink truncate leading-tight">
                  {resolvePetName(pet)}
                </div>
                <div className="text-[10px] text-subtext truncate">
                  Lv.{pet.level} · {pet.growthValue} 成长值
                </div>
              </div>
              <Shield
                size={14}
                className="text-primary/50 flex-shrink-0"
                aria-hidden="true"
              />
            </div>
            {/* 成长进度条 */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-[9px] text-subtext">
                <span>距下一级</span>
                <span>{Math.max(0, (pet.level * 200) - pet.growthValue)} 成长值</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-primary/10 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-primary to-primary-deep transition-all"
                  style={{ width: `${Math.min(100, ((pet.growthValue - (pet.level - 1) * 200) / 200) * 100)}%` }}
                />
              </div>
            </div>
          </button>
        )}

      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-bg text-ink font-sans flex relative">
      <AnimatedBackground />

      {/* Skip link — 键盘用户跳过导航直达内容 */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-toast focus:px-4 focus:py-2 focus:bg-primary focus:text-white focus:rounded-lg focus:shadow-glow"
      >
        跳到主内容
      </a>

      {/* 桌面端左侧边栏 */}
      <aside
        className="hidden md:flex flex-col fixed left-0 top-0 h-screen w-[200px] glass border-r border-white/60 z-sticky"
        role="navigation"
        aria-label="侧边导航"
      >
        {sidebarContent}
      </aside>

      {/* 移动端顶部导航栏 */}
      <header
        className="md:hidden fixed top-0 left-0 right-0 z-sticky glass border-b border-white/60"
        role="banner"
      >
        <div className="px-4 flex items-center h-[60px]">
          <button
            onClick={() => navigate('/home')}
            className="mr-auto transition-transform motion-safe:hover:scale-[1.02] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded-lg"
            aria-label="返回首页"
          >
            <Brand size="md" />
          </button>
          <NotificationBell />
          <button
            onClick={() => setMobileNavOpen((v) => !v)}
            className="w-10 h-10 rounded-xl bg-white/70 border border-white/60 flex items-center justify-center text-ink transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            aria-label={mobileNavOpen ? '关闭导航菜单' : '打开导航菜单'}
            aria-expanded={mobileNavOpen}
            aria-controls="mobile-nav"
          >
            {mobileNavOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* 移动端导航抽屉 */}
        {mobileNavOpen && (
          <nav
            id="mobile-nav"
            className="border-t border-white/60 glass animate-slide-up"
            aria-label="移动端导航"
          >
            <div className="px-4 py-3 space-y-4">
              {navSections.map((section) => (
                <div key={section.title} className="space-y-1">
                  <div className="px-4 pb-1">
                    <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-subtext/80">
                      {section.title}
                    </span>
                  </div>
                  {section.items.map((nav) => {
                    const Icon = nav.icon;
                    const active = isActive(nav.path);
                    return (
                      <button
                        key={nav.path}
                        onClick={() => navigate(nav.path)}
                        aria-current={active ? 'page' : undefined}
                        className={cn(
                          'w-full flex items-center gap-3.5 px-4 py-3 rounded-xl text-base font-medium transition-all',
                          active
                            ? 'bg-gradient-to-r from-primary to-primary-deep text-white shadow-glow-sm'
                            : 'text-ink hover:bg-white/60',
                        )}
                      >
                        <Icon size={20} aria-hidden="true" />
                        <div className="text-left">
                          <div>{nav.name}</div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              ))}
            </div>
          </nav>
        )}
      </header>

      {/* 桌面端顶部导航栏 */}
      <header
        className="hidden md:flex fixed top-0 left-[200px] right-0 h-[60px] glass border-b border-white/60 z-sticky items-center justify-between px-6"
        role="banner"
        aria-label="顶部导航"
      >
        <button
          onClick={() => navigate('/home')}
          className="transition-transform motion-safe:hover:scale-[1.02] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background rounded-lg"
          aria-label="返回首页"
        >
          <Brand size="sm" />
        </button>
        <div className="flex items-center gap-3">
          <NotificationBell />
          <div className="flex items-center gap-2 pl-3 border-l border-white/60">
            <div
              className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary-deep flex items-center justify-center text-white text-xs font-bold shadow-glow-sm flex-shrink-0"
              aria-hidden="true"
            >
              {currentUser.ownerId.slice(-2)}
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

      {/* 桌面端主内容区 + 底部 footer 包裹在一起，统一左侧偏移 */}
      <div className="flex-1 md:ml-[200px] min-w-0 flex flex-col">
        <main
          id="main-content"
          className="relative flex-1 w-full pt-[60px] md:pt-[72px]"
          role="main"
          tabIndex={-1}
        >
          <FloatingParticles count={8} theme="primary" />
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
            <div key={location.pathname} className="page-enter">
              <Outlet />
            </div>
          </div>
        </main>

        {/* 底部声明 */}
        <footer className="border-t border-white/60 glass" role="contentinfo">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-[11px] text-subtext">
            <span className="flex items-center gap-1.5">
              <Sparkles size={12} className="text-primary" aria-hidden="true" />
              {siteConfig.brandName} · {siteConfig.tagline}
            </span>
            <span className="sm:text-right leading-relaxed">
              {siteConfig.disclaimer}
            </span>
          </div>
        </footer>
      </div>

      {/* 移动端底部声明 */}
      <footer
        className="md:hidden fixed bottom-0 left-0 right-0 border-t border-white/60 glass z-sticky"
        role="contentinfo"
      >
        <div className="px-4 py-2 text-[10px] text-subtext text-center leading-tight">
          <span className="inline-flex items-center gap-1">
            <Sparkles size={10} className="text-primary" aria-hidden="true" />
            {siteConfig.brandName} · {siteConfig.tagline}
          </span>
          <span className="block mt-0.5 opacity-80">
            {siteConfig.disclaimer}
          </span>
        </div>
      </footer>
    </div>
  );
}

function NotificationBell() {
  const navigate = useNavigate();
  const unreadCount = useAppStore((state) => state.unreadCount);
  const notifications = useAppStore((state) => state.notifications);
  const loadNotifications = useAppStore((state) => state.loadNotifications);
  const markNotificationRead = useAppStore((state) => state.markNotificationRead);
  const markAllNotificationsRead = useAppStore((state) => state.markAllNotificationsRead);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    void loadNotifications();
  }, [loadNotifications]);

  const handleOpen = () => {
    setOpen((v) => !v);
    void loadNotifications();
  };

  const handleRead = async (id: number) => {
    await markNotificationRead(id);
  };

  const handleReadAll = async () => {
    await markAllNotificationsRead();
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={handleOpen}
        aria-label={unreadCount > 0 ? `消息通知（${unreadCount} 条未读）` : '消息通知'}
        aria-expanded={open}
        className="relative w-8 h-8 md:w-8 md:h-8 flex items-center justify-center rounded-xl bg-white/70 border border-white/60 text-subtext hover:text-primary hover:border-primary/40 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary flex-shrink-0"
      >
        <Bell size={15} aria-hidden="true" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 min-w-[16px] h-4 px-1 rounded-full bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <>
          <div
            className="fixed inset-0 z-40"
            aria-hidden="true"
            onClick={() => setOpen(false)}
          />
          <div
            role="dialog"
            aria-label="消息通知列表"
            className="absolute right-0 mt-2 w-72 max-h-96 overflow-y-auto rounded-2xl border border-white/70 bg-white shadow-glow z-50 p-2 space-y-1"
          >
            <div className="flex items-center justify-between px-2 py-1.5">
              <span className="text-xs font-bold text-ink">消息通知</span>
              {unreadCount > 0 && (
                <button
                  type="button"
                  onClick={handleReadAll}
                  className="text-[11px] text-primary hover:underline"
                >
                  全部已读
                </button>
              )}
            </div>
            {notifications.length === 0 ? null
 : (
              notifications.map((n) => (
                <button
                  key={n.id}
                  type="button"
                  onClick={() => handleRead(n.id)}
                  className={`w-full text-left rounded-xl px-2.5 py-2 transition-colors ${
                    n.isRead ? 'bg-white hover:bg-muted/60' : 'bg-primary-soft/60 hover:bg-primary-soft'
                  }`}
                >
                  <div className="flex items-center gap-1.5">
                    <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${n.isRead ? 'bg-transparent' : 'bg-primary'}`} />
                    <span className="text-[12px] font-semibold text-ink truncate">{n.title}</span>
                  </div>
                  <p className="mt-0.5 text-[11px] leading-5 text-subtext line-clamp-2">{n.content}</p>
                  <p className="mt-0.5 text-[10px] text-subtext">
                    {new Date(n.createdAt).toLocaleString('zh-CN', { hour12: false })}
                  </p>
                </button>
              ))
            )}
            <button
              type="button"
              onClick={() => { setOpen(false); navigate('/learning/market'); }}
              className="w-full mt-1 rounded-xl border border-border py-1.5 text-[11px] text-subtext hover:text-primary"
            >
              去集市互动看看
            </button>
          </div>
        </>
      )}
    </div>
  );
}
