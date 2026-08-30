import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  BookOpen,
  ClipboardList,
  FlaskConical,
  PlayCircle,
  Sparkles,
  Zap,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { getPetStageEmoji } from '../lib/pet-utils';
import { api } from '../api/client';
import { Card, CardContent, CardHeader, CardTitle, CardAction, CardFooter } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Progress } from '../components/ui/Progress';
import { Skeleton } from '../components/ui/Skeleton';
import { StatCard } from '../components/ui/StatCard';

export default function TrainingPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const fromTaskId = searchParams.get('fromTask') || undefined;
  const {
    currentUser,
    pet,
    loadTrainingTasks,
    trainingTasks,
    loadRanking,
    ranking,
    assessmentResult,
  } = useAppStore();
  const [tasksLoading, setTasksLoading] = useState(true);
  const [completedTaskCount, setCompletedTaskCount] = useState(0);

  useEffect(() => {
    let mounted = true;
    (async () => {
      await Promise.all([loadTrainingTasks(), loadRanking()]);
      // 加载真实训练记录，获取已完成任务数
      if (currentUser?.ownerId) {
        try {
          const records = await api.getRecords(currentUser.ownerId);
          // 去重 taskId 后计数
          const uniqueTasks = new Set(records.trainingRecords.filter((r) => r.rewardStatus === 'AWARDED').map((r) => r.taskId));
          if (mounted) setCompletedTaskCount(uniqueTasks.size);
        } catch {
          // ignore
        }
      }
      if (mounted) setTasksLoading(false);
    })();
    return () => {
      mounted = false;
    };
  }, [loadTrainingTasks, loadRanking, currentUser?.ownerId]);

  const toNextLevel = pet ? pet.nextLevelValue - pet.growthValue : 0;
  const progress = pet ? Math.min((pet.growthValue / pet.nextLevelValue) * 100, 100) : 0;

  // 统计卡数据
  const growthValue = pet?.growthValue ?? 0;
  const petLevel = pet?.level ?? 0;
  const completedTasks = completedTaskCount;
  const assessmentScore =
    assessmentResult ? Math.round((assessmentResult.accuracy ?? 0) * 100) : null;
  const myRank = ranking?.myRank?.rank ?? null;

  return (
    <div className="space-y-6">
      {/* 顶部：四个统计卡（参考 dashboard-01 SectionCards） */}
      <section
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4 animate-slide-up"
        aria-label="成长概览"
      >
        <StatCard
          label="当前成长值"
          value={
            <span className="flex items-baseline gap-1.5">
              {growthValue}
              <span className="text-sm font-normal text-subtext">/ {pet?.nextLevelValue ?? 1000}</span>
            </span>
          }
          accent="primary"
          trend={
            pet
              ? { value: `Lv.${petLevel}`, direction: 'up' }
              : { value: '未领养', direction: 'neutral' }
          }
        />
        <StatCard
          label="已完成训练"
          value={`${completedTasks} / ${trainingTasks.length || 6}`}
          accent="success"
          trend={
            completedTasks > 0
              ? { value: `${Math.round((completedTasks / Math.max(trainingTasks.length, 1)) * 100)}%`, direction: 'up' }
              : { value: '待开始', direction: 'neutral' }
          }
        />
        <StatCard
          label="测评分数"
          value={assessmentScore !== null ? `${assessmentScore} 分` : '未测评'}
          accent="warning"
          trend={
            assessmentScore !== null
              ? {
                  value: assessmentScore >= 80 ? '优秀' : assessmentScore >= 60 ? '合格' : '待提升',
                  direction: assessmentScore >= 60 ? 'up' : 'down',
                }
              : { value: '去测评', direction: 'neutral' }
          }
        />
        <StatCard
          label="校园排名"
          value={myRank !== null ? `第 ${myRank} 名` : '未上榜'}
          accent="danger"
          trend={
            myRank !== null && myRank <= 10
              ? { value: 'Top 10', direction: 'up' }
              : myRank !== null
                ? { value: '继续努力', direction: 'neutral' }
                : { value: '无排名', direction: 'neutral' }
          }
        />
      </section>

      {/* 中部：宠物状态卡 / 空宠物位（使用 Card 子组件结构） */}
      {pet ? (
        <Card className="relative overflow-hidden bg-gradient-to-br from-primary-soft/40 via-card to-card animate-slide-up">
          <div className="absolute inset-0 bg-mesh opacity-50 pointer-events-none" aria-hidden />
          <CardContent className="relative">
            <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
              <div className="flex items-center gap-5">
                <div className="relative">
                  <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-soft to-indigo-100 flex items-center justify-center border border-primary/20 shadow-glow-sm">
                    <span className="text-3xl" role="img" aria-label={`${pet.type} ${pet.stage}`}>
                      {getPetStageEmoji(pet.type, pet.stage)}
                    </span>
                  </div>
                  <Badge
                    variant="default"
                    className="absolute -bottom-1 -right-1 bg-gradient-to-r from-primary to-primary-deep text-white shadow-glow-sm"
                  >
                    Lv.{pet.level}
                  </Badge>
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1.5">
                    <h2 className="text-xl font-extrabold text-ink">{pet.type}</h2>
                    <Badge variant="secondary">{pet.category}</Badge>
                    <Badge variant="info">{pet.stage}</Badge>
                  </div>
                  <p className="text-xs text-subtext mb-1">
                    宠物 ID: <span className="font-medium text-ink">{pet.petId}</span> · 主人 ID:{' '}
                    <span className="font-medium text-ink">{currentUser?.ownerId}</span>
                  </p>
                  <p className="text-xs text-subtext">
                    成长值 <span className="font-semibold text-growth">{pet.growthValue}</span> · 最近训练{' '}
                    {pet.lastTrainingAt || '暂无'}
                  </p>
                </div>
              </div>
              <div className="w-full md:w-1/3 flex-shrink-0">
                <div className="flex justify-between text-xs text-subtext mb-1.5">
                  <span>
                    距下一级还差 <span className="font-bold text-growth">{toNextLevel}</span> 成长值
                  </span>
                  <span className="font-medium">
                    {pet.growthValue} / {pet.nextLevelValue}
                  </span>
                </div>
                <Progress
                  value={progress}
                  gradient="success"
                  height={10}
                  aria-label={`${pet.type}成长进度`}
                />
                <p className="text-xs text-subtext mt-1.5">
                  今日剩余可获得成长值: <span className="font-bold text-primary">300</span>
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="relative overflow-hidden animate-slide-up bg-gradient-to-br from-slate-50 to-card">
          <div className="absolute inset-0 bg-mesh opacity-50 pointer-events-none" aria-hidden />
          <CardContent className="relative">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-5">
                <div className="w-20 h-20 rounded-2xl bg-slate-50 flex items-center justify-center border-2 border-dashed border-slate-200">
                  <span className="text-3xl text-slate-300" aria-hidden>
                    ?
                  </span>
                </div>
                <div>
                  <h2 className="text-xl font-extrabold text-ink mb-1">空宠物位</h2>
                </div>
              </div>
              <Button size="lg" onClick={() => navigate('/assessment')} className="gap-1.5">
                开始快速测评 <ArrowRight size={16} />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 四个入口（使用 Card interactive） */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4" aria-label="功能入口">
        <EntryCard
          icon={FlaskConical}
          color="primary"
          title="快速测评"
          onClick={() => navigate('/assessment')}
          ariaLabel="进入快速测评"
        />
        <EntryCard
          icon={ClipboardList}
          color="safe"
          title="推荐训练"
          onClick={() => document.getElementById('recommended-tasks')?.scrollIntoView({ behavior: 'smooth' })}
          ariaLabel="查看推荐训练任务"
        />
        <EntryCard
          icon={BookOpen}
          color="warning"
          title="自由训练"
          onClick={() => navigate('/free-training')}
          ariaLabel="进入自由训练"
        />
      </section>

      {/* 下方：推荐任务 */}
      <div id="recommended-tasks" className="pt-2 scroll-mt-4">
        <Card>
          <CardHeader className="border-b border-border">
            <CardTitle className="text-lg flex items-center gap-2">
              <Sparkles size={18} className="text-warning" aria-hidden />
              推荐训练任务
            </CardTitle>
            <CardAction>
              <Badge variant="info">{trainingTasks.length} 个任务</Badge>
            </CardAction>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
              {tasksLoading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <Card key={i} variant="outline" className="py-4 gap-3">
                    <CardHeader className="pb-0">
                      <Skeleton className="h-5 w-2/3" />
                      <Skeleton className="h-5 w-14 rounded-full" />
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <Skeleton className="h-3 w-full" />
                      <Skeleton className="h-3 w-5/6" />
                      <Skeleton className="h-3 w-4/6" />
                    </CardContent>
                    <CardFooter className="border-t border-border pt-3 justify-between">
                      <Skeleton className="h-4 w-20" />
                      <Skeleton className="h-7 w-24 rounded-lg" />
                    </CardFooter>
                  </Card>
                ))
              ) : trainingTasks.length === 0 ? (
                <div className="col-span-full text-center py-16">
                  <div className="w-16 h-16 rounded-2xl bg-slate-50 flex items-center justify-center mx-auto mb-4 border border-slate-100">
                    <ClipboardList size={28} className="text-slate-300" aria-hidden />
                  </div>
                  <p className="text-ink font-semibold mb-1">暂无推荐训练任务</p>
                  <Button variant="ghost" size="sm" className="mt-4" onClick={() => navigate('/assessment')}>
                    去测评
                  </Button>
                </div>
              ) : (
                trainingTasks.map((task, idx) => (
                  <Card
                    key={task.id}
                    variant="interactive"
                    className="py-5 gap-3 animate-slide-up"
                    style={{ animationDelay: `${idx * 60}ms` }}
                  >
                    <CardHeader className="pb-0">
                      <CardTitle className="text-base leading-tight pr-2">{task.title}</CardTitle>
                      <CardAction>
                        <RiskBadge level={task.riskLevel} />
                      </CardAction>
                    </CardHeader>
                    <CardContent className="space-y-1.5">
                      <Row label="诈骗类型" value={task.fraudType} />
                      <Row label="预计用时" value={task.duration} />
                      <Row label="难度" value={task.difficulty} />
                    </CardContent>
                    <CardFooter className="border-t border-border pt-3 justify-between">
                      <span className="text-growth font-extrabold">
                        +{task.reward} <span className="text-xs font-normal text-subtext">成长值</span>
                      </span>
                      <Button
                        size="sm"
                        onClick={() => navigate(`/training/session/${task.id}`, { state: { fromTask: fromTaskId } })}
                        aria-label={`开始训练：${task.title}`}
                        className="gap-1"
                      >
                        <PlayCircle size={14} /> 开始训练
                      </Button>
                    </CardFooter>
                  </Card>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 今日成长值限制提示 */}
      <Card className="bg-primary-soft/40 border-primary/15">
        <CardContent className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
            <Zap size={18} className="text-primary" aria-hidden />
          </div>
          <div className="text-sm">
            <p className="text-ink font-semibold mb-0.5">成长值规则提示</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface EntryCardProps {
  icon: React.ComponentType<{ size?: number; className?: string }>;
  color: 'primary' | 'safe' | 'warning' | 'danger';
  title: string;
  onClick: () => void;
  ariaLabel?: string;
}

function EntryCard({ icon: Icon, color, title, onClick, ariaLabel }: EntryCardProps) {
  const palette = {
    primary: {
      bg: 'from-primary/10 to-primary/5',
      iconBg: 'bg-primary/10',
      iconColor: 'text-primary',
      ring: 'group-hover:bg-primary/15',
    },
    safe: {
      bg: 'from-emerald-500/10 to-emerald-500/5',
      iconBg: 'bg-emerald-500/10',
      iconColor: 'text-safe',
      ring: 'group-hover:bg-emerald-500/15',
    },
    warning: {
      bg: 'from-amber-500/10 to-amber-500/5',
      iconBg: 'bg-amber-500/10',
      iconColor: 'text-warning',
      ring: 'group-hover:bg-amber-500/15',
    },
    danger: {
      bg: 'from-rose-500/10 to-rose-500/5',
      iconBg: 'bg-rose-500/10',
      iconColor: 'text-danger',
      ring: 'group-hover:bg-rose-500/15',
    },
  }[color];

  return (
    <button
      onClick={onClick}
      aria-label={ariaLabel ?? title}
      className={`group relative app-card app-card-hover p-5 text-left bg-gradient-to-br ${palette.bg} animate-slide-up overflow-hidden focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:ring-offset-2`}
    >
      <div
        className={`w-11 h-11 rounded-xl ${palette.iconBg} ${palette.ring} flex items-center justify-center mb-3 transition-colors`}
        aria-hidden
      >
        <Icon size={20} className={palette.iconColor} />
      </div>
      <h3 className="font-bold text-ink mb-1">{title}</h3>
    </button>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <p className="text-xs text-subtext flex justify-between">
      <span>{label}</span>
      <span className="text-ink font-medium">{value}</span>
    </p>
  );
}

function RiskBadge({ level }: { level: string }) {
  const variant =
    level === '高风险' ? 'danger' : level === '中风险' ? 'warning' : 'info';
  return (
    <Badge variant={variant} size="sm">
      {level}
    </Badge>
  );
}
