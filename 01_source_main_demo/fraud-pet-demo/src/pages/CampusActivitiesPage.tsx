import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  Award,
  Leaf,
  Loader2,
  Megaphone,
  ShieldCheck,
  Sparkles,
  Sprout,
  TreePine,
  Users,
} from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/useAppStore';
import type { CampusActivity } from '../types/learning';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

export default function CampusActivitiesPage() {
  const navigate = useNavigate();
  const ownerId = useAppStore((state) => state.currentUser?.ownerId) ?? '';
  const pet = useAppStore((state) => state.pet);
  const [activities, setActivities] = useState<CampusActivity[]>([]);
  const [plan, setPlan] = useState<{ id: string; shieldEnergy: number; guardianValue: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.getCampusActivities(ownerId);
      setActivities(result.activities);
      setPlan(result.plan);
    } catch (err) {
      setError(err instanceof Error ? err.message : '校园活动加载失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, [ownerId]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return (
      <div className="flex min-h-[420px] items-center justify-center text-subtext">
        <Loader2 className="mr-2 animate-spin" size={20} />小盾灵正在同步成长记录...
      </div>
    );
  }

  if (error) {
    return (
      <div className="app-card mx-auto max-w-xl p-8 text-center">
        <h1 className="mt-3 text-xl font-extrabold text-ink">加载失败</h1>
        <p className="mt-2 text-sm leading-6 text-subtext">{error}</p>
        <Button className="mt-5" onClick={load}>
          重试 <ArrowRight size={16} />
        </Button>
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="app-card mx-auto max-w-xl p-8 text-center">
        <Sprout className="mx-auto text-emerald-600" size={42} />
        <h1 className="mt-3 text-xl font-extrabold text-ink">学习成长从一个目标开始</h1>
        <Button className="mt-5" onClick={() => navigate('/learning/goal')}>
          发布学习目标 <ArrowRight size={16} />
        </Button>
      </div>
    );
  }

  const unlockedCount = activities.filter((activity) => activity.status === 'unlocked').length;
  const guardianStage =
    plan.guardianValue >= 100 ? '校园守护者' : plan.guardianValue >= 60 ? '辨诈之盾' : plan.guardianValue >= 30 ? '识诈幼苗' : '警觉之种';
    <span className="text-[12px] text-subtext">蚂蚁森林式学习激励 · 辅助层</span>

  return (
    <div className="space-y-5 animate-slide-up">
      <section className="rounded-2xl border border-blue-200/70 bg-gradient-to-br from-blue-50 via-white to-indigo-50 p-5 shadow-card">

        <div className="mt-2 flex items-center justify-between gap-3">
          <h1 className="text-[24px] font-extrabold leading-tight text-ink">小盾灵守护域</h1>
          <div className="flex shrink-0 items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-100 text-lg text-blue-700">
              {pet?.avatarEmoji ?? '🛡️'}
            </div>
            <span className="text-xs font-bold text-ink">{guardianStage}</span>
          </div>
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          <Capsule icon={<Sparkles size={14} />} text={`盾能・${plan.shieldEnergy}`} />
          <Capsule icon={<ShieldCheck size={14} />} text={`守护值・${plan.guardianValue}`} />
          <Capsule icon={<Award size={14} />} text={`已解锁・${unlockedCount}`} />
        </div>

        <div className="mt-2.5 flex flex-wrap items-center gap-x-2.5 gap-y-1.5 text-[12px] text-subtext">
          <span className="flex items-center gap-1"><Sparkles size={12} />非积分商城</span>
          <span className="text-slate-300">·</span>
          <span className="flex items-center gap-1"><Users size={12} />自愿参与</span>
          <span className="text-slate-300">·</span>
          <span className="flex items-center gap-1"><Megaphone size={12} />团委落地</span>
        </div>

      </section>

      <section>
        <div className="mb-3 flex items-end justify-between">
          <div>
            <h2 className="text-lg font-extrabold text-ink">校园实践活动发现与解锁</h2>
          </div>
          <Badge variant="outline">{unlockedCount}/{activities.length} 已解锁</Badge>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {activities.map((activity) => (
            <ActivityCard
              key={activity.id}
              activity={activity}
              onOpen={() => navigate(`/learning/activities/${activity.id}`)}
            />
          ))}
        </div>
      </section>
    </div>
  );
}

function Capsule({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="flex items-center gap-1.5 rounded-full border border-blue-200/60 bg-white/80 px-3 py-1.5 text-[13px] font-bold text-ink shadow-sm">
      <span className="text-blue-600">{icon}</span>
      {text}
    </div>
  );
}

function ActivityCard({ activity, onOpen }: { activity: CampusActivity; onOpen: () => void }) {
  const unlocked = activity.status === 'unlocked';
  return (
    <button
      onClick={onOpen}
      className={`group w-full overflow-hidden rounded-3xl border p-4 text-left transition hover:-translate-y-0.5 hover:shadow-card ${
        unlocked ? 'border-emerald-200 bg-gradient-to-br from-emerald-50 to-white' : 'border-border bg-white'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className={`flex h-11 w-11 items-center justify-center rounded-2xl ${unlocked ? 'bg-emerald-600 text-white shadow-glow-sm' : 'bg-slate-100 text-slate-500'}`}>
          {activity.title.includes('植树') ? <TreePine size={21} /> : activity.title.includes('作品') ? <Leaf size={21} /> : <Users size={21} />}
        </div>
        <Badge variant={unlocked ? 'success' : 'secondary'} size="sm">
          {unlocked ? '已解锁' : `${activity.progress}%`}
        </Badge>
      </div>
      <h3 className="mt-3 text-base font-extrabold text-ink">{activity.title}</h3>
      <p className="mt-1 line-clamp-2 text-xs leading-5 text-subtext">{activity.description}</p>
      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full ${unlocked ? 'bg-emerald-500' : 'bg-primary'}`}
          style={{ width: `${activity.progress}%` }}
        />
      </div>
      <div className="mt-3 flex items-center justify-between text-[10px] text-subtext">
        <span>{activity.organizer}</span>
        <span className="font-bold text-primary group-hover:underline">查看详情</span>
      </div>
    </button>
  );
}

