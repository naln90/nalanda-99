import { useEffect } from 'react';
import { Activity, CalendarRange, Gauge, GraduationCap, TrendingUp, Users } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Progress } from '../components/ui/Progress';

/**
 * SchoolLearningPage — 校方发布端：学习情况总览（V3.0 §3.2）
 * 数据粒度：聚合统计（学生数 / 任务完成率 / 当前主题 / 活动共建概况），不下钻个人明细
 */
export default function SchoolLearningPage() {
  const currentUser = useAppStore((s) => s.currentUser);
  const dashboard = useAppStore((s) => s.schoolDashboard);
  const loadSchoolDashboard = useAppStore((s) => s.loadSchoolDashboard);

  useEffect(() => {
    if (currentUser?.ownerId) loadSchoolDashboard(currentUser.ownerId);
  }, [currentUser?.ownerId, loadSchoolDashboard]);

  const completionPct = Math.round((dashboard?.taskCompletionRate ?? 0) * 100);

  const stats = [
    { label: '注册学生数', value: dashboard?.studentCount ?? '—', icon: Users },
    { label: '全部用户数', value: dashboard?.totalUsers ?? '—', icon: GraduationCap },
    { label: '主题任务完成率', value: dashboard ? `${completionPct}%` : '—', icon: Gauge },
    { label: '进行中活动', value: dashboard?.activities?.filter((a) => a.status === 'building').length ?? '—', icon: Activity },
  ];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-extrabold text-ink flex items-center gap-2">
          <TrendingUp size={20} className="text-primary" aria-hidden="true" />
          学习情况
        </h1>
      </div>

      {/* 核心指标 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {stats.map((s) => {
          const Icon = s.icon;
          return (
            <Card key={s.label}>
              <CardContent className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Icon size={18} className="text-primary" aria-hidden="true" />
                </div>
                <div className="min-w-0">
                  <div className="text-lg font-extrabold text-ink leading-tight">{s.value}</div>
                  <div className="text-[11px] text-subtext">{s.label}</div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* 当前主题 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <CalendarRange size={16} className="text-primary" aria-hidden="true" />
            当前发布主题
          </CardTitle>
        </CardHeader>
        <CardContent>
          {dashboard?.activeTheme ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[15px] font-bold text-ink">{dashboard.activeTheme.title}</span>
                <Badge variant="success">进行中</Badge>
              </div>
              <div className="space-y-1">
                <div className="flex items-center justify-between text-[11px] text-subtext">
                  <span>全校任务完成率</span>
                  <span className="font-semibold text-ink">{completionPct}%</span>
                </div>
                <Progress value={completionPct} height={8} />
              </div>
            </div>
) : null
}
        </CardContent>
      </Card>

      {/* 活动共建概况 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Activity size={16} className="text-primary" aria-hidden="true" />
            守护活动共建概况
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {dashboard?.activities?.length ? (
            dashboard.activities.map((act) => {
              const ratio = Math.min(100, Math.round((act.currentProgress / Math.max(1, act.targetEnergy)) * 100));
              return (
                <div key={act.id} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-ink truncate">{act.title}</span>
                    <span className="text-subtext flex-shrink-0 ml-2">
                      {act.contributorCount} 人 · {act.currentProgress}/{act.targetEnergy}
                      <p className="text-sm text-subtext">暂无守护活动</p>
                    </span>
                  </div>
                  <Progress value={ratio} gradient={act.status === 'building' ? 'primary' : 'success'} height={6} shimmer={false} />
                </div>
              );
            })
) : null
}
        </CardContent>
      </Card>
    </div>
  );
}
