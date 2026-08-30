import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Award,
  Check,
  CheckCircle2,
  ExternalLink,
  Info,
  Leaf,
  Loader2,
  TreePine,
  Users,
} from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/useAppStore';
import type { CampusActivity } from '../types/learning';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

function activityIcon(activity: CampusActivity) {
  if (activity.title.includes('植树')) return <TreePine size={26} />;
  if (activity.title.includes('作品')) return <Leaf size={26} />;
  return <Users size={26} />;
}

export default function ActivityIntroPage() {
  const { activityId } = useParams<{ activityId: string }>();
  const navigate = useNavigate();
  const ownerId = useAppStore((state) => state.currentUser?.ownerId) ?? '';

  const [activity, setActivity] = useState<CampusActivity | null>(null);
  const [plan, setPlan] = useState<{ id: string; shieldEnergy: number; guardianValue: number } | null>(null);
  const [boundaryNotice, setBoundaryNotice] = useState('');
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const load = useCallback(async () => {
    if (!activityId) return;
    setLoading(true);
    try {
      const result = await api.getCampusActivity(ownerId, activityId);
      setActivity(result.activity);
      setPlan(result.plan);
      setBoundaryNotice(result.boundaryNotice);
      setNotFound(false);
    } catch {
      setNotFound(true);
    } finally {
      setLoading(false);
    }
  }, [ownerId, activityId]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return (
      <div className="flex min-h-[420px] items-center justify-center text-subtext">
        <Loader2 className="mr-2 animate-spin" size={20} />小盾灵正在同步活动详情...
      </div>
    );
  }

  if (notFound || !activity) {
    return (
      <div className="app-card mx-auto max-w-xl p-8 text-center">
        <Info className="mx-auto text-amber-500" size={42} />
        <h1 className="mt-3 text-xl font-extrabold text-ink">活动不存在或已下架</h1>
        <p className="mt-2 text-sm leading-6 text-subtext">该活动可能已被学校团委调整，或链接已失效。</p>
        <Button className="mt-5" onClick={() => navigate('/learning/activities')}>
          返回活动列表 <ArrowLeft size={16} />
        </Button>
      </div>
    );
  }

  const unlocked = activity.status === 'unlocked';

  return (
    <div className="space-y-5 animate-slide-up">
      <button
        onClick={() => navigate('/learning/activities')}
        className="inline-flex items-center gap-1.5 text-sm font-bold text-subtext transition hover:text-primary"
      >
        <ArrowLeft size={16} />返回守护域
      </button>

      <section className="rounded-3xl border border-emerald-200/70 bg-gradient-to-br from-emerald-50 via-white to-cyan-50 p-6 shadow-card">
        <div className="flex items-start gap-5">
          <div
            className={`flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl ${
              unlocked ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'
            }`}
          >
            {activityIcon(activity)}
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="border-emerald-200/70 bg-white/80 text-emerald-700">
                {unlocked ? '已解锁' : '学习中'}
              </Badge>
              <Badge variant="outline" className="border-emerald-200/70 text-emerald-700">
                {activity.category}
              </Badge>
            </div>
            <h1 className="mt-2 text-2xl font-extrabold text-ink sm:text-3xl">{activity.title}</h1>
            <p className="mt-1 text-xs text-subtext">
              主办：{activity.organizer}
              {activity.interestDirection ? ` · 兴趣方向：${activity.interestDirection}` : ''}
            </p>
          </div>
        </div>

        {plan && (
          <div className="mt-5 flex flex-wrap gap-3">
            <HeroMetric label="盾能" value={plan.shieldEnergy} />
            <HeroMetric label="永久守护值" value={plan.guardianValue} />
            <HeroMetric label="活动进度" value={activity.progress} suffix="%" />
          </div>
        )}
      </section>

      <section className="app-card p-6">
        <h2 className="text-sm font-extrabold text-ink">活动简介</h2>
        <p className="mt-2 text-sm leading-7 text-subtext">{activity.description}</p>
      </section>

      <section className="app-card p-6">
        <p className="text-sm font-extrabold text-ink">学习解锁条件</p>
        <div className="mt-3 space-y-3">
          {activity.requirements.map((requirement) => (
            <div key={requirement.label} className="flex items-center justify-between gap-3">
              <span className="flex items-center gap-2 text-sm text-subtext">
                <span
                  className={`flex h-6 w-6 items-center justify-center rounded-full ${
                    requirement.completed ? 'bg-safe-500 text-white' : 'bg-white text-subtext ring-1 ring-border'
                  }`}
                >
                  <Check size={12} />
                </span>
                {requirement.label}
              </span>
              <span className="font-bold text-ink">
                {requirement.current}/{requirement.target}
              </span>
            </div>
          ))}
        </div>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            className={`h-full rounded-full ${unlocked ? 'bg-emerald-500' : 'bg-primary'}`}
            style={{ width: `${activity.progress}%` }}
          />
        </div>
      </section>

      {unlocked ? (
        <section className="space-y-3">
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
            <div className="flex items-center gap-2 text-sm font-extrabold text-emerald-800">
              <CheckCircle2 size={16} />已获得活动认知、成长荣誉与参与资格
            </div>
            <p className="mt-1 text-xs leading-6 text-emerald-900/70">
              你可以仅保留解锁纪念、关注启动仪式，也可以在学校发布正式通知后按团委规定程序报名。
            </p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Button variant="outline" className="flex-1">
              <Award size={15} />保留解锁纪念
            </Button>
            <Button className="flex-1" disabled={!activity.noticeUrl}>
              <ExternalLink size={15} />
              {activity.noticeUrl ? '查看团委通知' : '等待团委通知'}
            </Button>
          </div>
        </section>
      ) : (
        <Button fullWidth onClick={() => navigate('/learning/workspace')}>
          继续主题学习 <ArrowLeft size={15} className="rotate-180" />
        </Button>
      )}

      <div className="rounded-2xl border border-border bg-muted/40 p-4">
        <div className="flex gap-2">
          <Info className="mt-0.5 shrink-0 text-blue-600" size={16} />
          <p className="text-[11px] leading-5 text-subtext">{boundaryNotice}</p>
        </div>
      </div>
    </div>
  );
}

function HeroMetric({ label, value, suffix }: { label: string; value: number; suffix?: string }) {
  return (
    <div className="rounded-2xl border border-emerald-200/60 bg-white/80 px-3 py-2 shadow-sm">
      <div className="text-[10px] text-subtext">{label}</div>
      <div className="mt-0.5 text-lg font-extrabold text-ink">
        {value}
        {suffix}
      </div>
    </div>
  );
}
