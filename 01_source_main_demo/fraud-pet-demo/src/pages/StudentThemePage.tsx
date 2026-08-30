import { useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, BookOpen, CheckCircle2, Circle, Loader2, Rocket, Shield, Sparkles, Zap } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Progress } from '../components/ui/Progress';
import { useToast } from '../components/ui/Toast';
import type { ThemeItem } from '../types';

const CATEGORY_META: Record<string, { label: string; variant: 'default' | 'info' | 'warning' }> = {
  required: { label: '基础必修', variant: 'default' },
  elective: { label: '兴趣选修', variant: 'info' },
  outcome: { label: '成果任务', variant: 'warning' },
};

/**
 * StudentThemePage — 学生端：主题学习（V3.0 §2.2）
 * 展示校方发布的月度主题任务包；加入后完成任务获得盾能
 */
export default function StudentThemePage() {
  const currentUser = useAppStore((s) => s.currentUser);
  const activeTheme = useAppStore((s) => s.activeTheme);
  const energyBalance = useAppStore((s) => s.energyBalance);
  const isLoading = useAppStore((s) => s.isLoading);
  const navigate = useNavigate();
  const loadActiveTheme = useAppStore((s) => s.loadActiveTheme);
  const joinActiveTheme = useAppStore((s) => s.joinActiveTheme);
  const loadEnergy = useAppStore((s) => s.loadEnergy);
  const { success } = useToast();

  const ownerId = currentUser?.ownerId ?? '';

  useEffect(() => {
    if (!ownerId) return;
    loadActiveTheme(ownerId);
    loadEnergy(ownerId);
  }, [ownerId, loadActiveTheme, loadEnergy]);

  const theme = activeTheme?.theme ?? null;
  const items = useMemo(() => activeTheme?.items ?? [], [activeTheme]);
  const joined = activeTheme?.joined ?? false;

  const doneCount = items.filter((i) => i.status === 'done').length;
  const progressPct = items.length ? Math.round((doneCount / items.length) * 100) : 0;

  const grouped = useMemo(() => {
    return (['required', 'elective', 'outcome'] as const)
      .map((c) => ({ category: c, list: items.filter((i) => i.category === c) }))
      .filter((g) => g.list.length > 0);
  }, [items]);

  const handleJoin = async () => {
    if (!theme) return;
    await joinActiveTheme(ownerId, theme.id);
    if (!useAppStore.getState().error) success('已加入本月主题，开始学习吧！');
  };

  const handleOpenTask = (item: ThemeItem) => {
    navigate(`/learning/task/${item.id}`);
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-xl font-extrabold text-ink flex items-center gap-2">
            <BookOpen size={20} className="text-primary" aria-hidden="true" />
            主题学习
          </h1>
        </div>
        {energyBalance && (
          <div className="flex items-center gap-2">
            <Badge variant="default" className="gap-1">
              <Zap size={11} aria-hidden="true" />
              可用盾能 {energyBalance.availableEnergy}
            </Badge>
            <Badge variant="outline" className="gap-1">
              <Shield size={11} aria-hidden="true" />
              Lv.{energyBalance.level}
            </Badge>
          </div>
        )}
      </div>

      {!theme && (
        <Card>
          <CardContent className="text-center py-10 space-y-2">
            <Sparkles size={28} className="text-primary mx-auto" aria-hidden="true" />
            <p className="text-sm font-semibold text-ink">本月主题尚未发布</p>
          </CardContent>
        </Card>
      )}

      {theme && (
        <>
          {/* 主题卡 */}
          <Card variant="elevated">
            <CardHeader>
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <div>
                  <CardTitle className="text-lg">{theme.title}</CardTitle>
                </div>
                {!joined ? (
                  <Button onClick={handleJoin} disabled={isLoading} variant="gradient">
                    {isLoading ? (
                      <Loader2 size={14} className="animate-spin" aria-hidden="true" />
                    ) : (
                      <Rocket size={14} aria-hidden="true" />
                    )}
                    加入本月主题
                  </Button>
                ) : (
                  <Badge variant="success" className="gap-1">
                    <CheckCircle2 size={11} aria-hidden="true" />
                    已加入
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center gap-3 text-[11px] text-subtext flex-wrap">
                <span>周期 {theme.periodDays} 天</span>
                {theme.expectedOutcome && <span>预期成果：{theme.expectedOutcome}</span>}
                {theme.baseAssessment && <span>考核：{theme.baseAssessment}</span>}
              </div>
              {joined && items.length > 0 && (
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-[11px] text-subtext">
                    <span>我的完成进度</span>
                    <span className="font-semibold text-ink">
                      {doneCount}/{items.length}（{progressPct}%）
                    </span>
                  </div>
                  <Progress value={progressPct} height={8} />
                </div>
              )}
            </CardContent>
          </Card>

          {/* 任务列表 */}
          {joined ? (
            grouped.map(({ category, list }) => {
              const meta = CATEGORY_META[category];
              return (
                <div key={category} className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Badge variant={meta.variant}>{meta.label}</Badge>
                    <span className="text-[11px] text-subtext">
                      {list.filter((i) => i.status === 'done').length}/{list.length} 已完成
                    </span>
                  </div>
                  <div className="space-y-2">
                    {list.map((item) => {
                      const done = item.status === 'done' || item.status === 'completed';
                      return (
                        <Card
                          key={item.id}
                          variant={done ? 'outline' : 'interactive'}
                          className="cursor-pointer group"
                          onClick={() => handleOpenTask(item)}
                        >
                          <CardContent className="flex items-start gap-3">
                            <div className="mt-0.5 flex-shrink-0" aria-hidden="true">
                              {done ? (
                                <CheckCircle2 size={20} className="text-safe-500" />
                              ) : (
                                <Circle size={20} className="text-subtext group-hover:text-primary transition-colors" />
                              )}
                            </div>
                            <div className="min-w-0 flex-1">
                              <div className={done ? 'text-sm font-semibold text-subtext line-through' : 'text-sm font-semibold text-ink'}>
                                {item.title}
                              </div>
                              {item.acceptanceCriteria && (
                                <p className="text-[10px] text-subtext/80 mt-1">验收：{item.acceptanceCriteria}</p>
                              )}
                              <div className="flex items-center gap-2 mt-1.5 text-[10px] text-subtext">
                                <span>约 {item.estimatedMinutes} 分钟</span>
                                <span>·</span>
                                <span>第 {item.dueDay} 天前完成</span>
                              </div>
                            </div>
                            <div className="flex flex-col items-end gap-1 flex-shrink-0">
                              <Badge variant={done ? 'outline' : 'default'} className="gap-0.5">
                                <Zap size={10} aria-hidden="true" />+{item.energyReward}
                              </Badge>
                              {!done && <ArrowRight size={14} className="text-subtext group-hover:text-primary transition-colors" aria-hidden="true" />}
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                </div>
              );
            })
          ) : (
            <Card>
              <CardContent className="text-center text-sm text-subtext py-8">
                加入主题后即可查看并完成任务包
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
