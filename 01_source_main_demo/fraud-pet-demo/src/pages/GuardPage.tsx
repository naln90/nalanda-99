import { useEffect, useState } from 'react';
import { HandHeart, Megaphone, Sprout, Users, Zap } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Progress } from '../components/ui/Progress';
import { useToast } from '../components/ui/Toast';

const STATUS_META: Record<string, { label: string; variant: 'secondary' | 'info' | 'success' | 'outline' }> = {
  building: { label: '共建中', variant: 'info' },
  unlocked: { label: '已解锁', variant: 'success' },
  notice_released: { label: '通知已发布', variant: 'success' },
  archived: { label: '已归档', variant: 'outline' },
};

const QUICK_AMOUNTS = [10, 50, 100];

/**
 * GuardPage — 学生端：守护共建（V3.0 §2.4 蚂蚁森林式集体共建）
 * 投放可用盾能 → 推动活动进度 → 达标解锁 → 查看校方落地通知
 * 盾能三口径：投放只消耗「可用」，不影响「累计获得」（个人等级不受影响）
 */
export default function GuardPage() {
  const currentUser = useAppStore((s) => s.currentUser);
  const activities = useAppStore((s) => s.activities);
  const energyBalance = useAppStore((s) => s.energyBalance);
  const error = useAppStore((s) => s.error);
  const loadActivities = useAppStore((s) => s.loadActivities);
  const loadEnergy = useAppStore((s) => s.loadEnergy);
  const contributeActivity = useAppStore((s) => s.contributeActivity);
  const { success, error: toastError } = useToast();

  const [pendingId, setPendingId] = useState<string | null>(null);

  const ownerId = currentUser?.ownerId ?? '';

  useEffect(() => {
    if (!ownerId) return;
    loadActivities(ownerId);
    loadEnergy(ownerId);
  }, [ownerId, loadActivities, loadEnergy]);

  const handleContribute = async (activityId: string, amount: number) => {
    if ((energyBalance?.availableEnergy ?? 0) < amount) {
      toastError('可用盾能不足，先去完成主题学习任务吧');
      return;
    }
    setPendingId(activityId);
    const ok = await contributeActivity(activityId, ownerId, amount);
    setPendingId(null);
    if (ok) success(`已投放 ${amount} 盾能，感谢共建！`);
  };

  const visible = activities.filter((a) => a.status !== 'draft');

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-xl font-extrabold text-ink flex items-center gap-2">
            <HandHeart size={20} className="text-primary" aria-hidden="true" />
            守护共建
          </h1>
        </div>
      </div>

      {/* 盾能三口径 */}
      {energyBalance && (
        <div className="grid grid-cols-3 gap-3">
          <Card>
            <CardContent className="text-center">
              <div className="text-lg font-extrabold text-primary leading-tight">{energyBalance.cumulativeEnergy}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="text-center">
              <div className="text-lg font-extrabold text-ink leading-tight">{energyBalance.availableEnergy}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="text-center">
              <div className="text-lg font-extrabold text-safe-600 leading-tight">{energyBalance.contributedEnergy}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {error && <div className="rounded-xl bg-danger/5 border border-danger/20 text-danger text-xs px-3 py-2">{error}</div>}

      {visible.length === 0 ? (
        <Card>
          <CardContent className="text-center py-10 space-y-2">
            <Sprout size={28} className="text-primary mx-auto" aria-hidden="true" />
            <p className="text-sm font-semibold text-ink">暂无进行中的守护活动</p>
            <p className="text-xs text-subtext">校方发布共建活动后将在此展示</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {visible.map((act) => {
            const meta = STATUS_META[act.status] ?? { label: act.status, variant: 'outline' as const };
            const ratio = Math.min(100, Math.round((act.currentProgress / Math.max(1, act.targetEnergy)) * 100));
            const building = act.status === 'building';
            return (
              <Card key={act.id} variant={building ? 'interactive' : 'default'}>
                <CardHeader>
                  <div className="flex items-center justify-between gap-3 flex-wrap">
                    <div className="flex items-center gap-2 min-w-0">
                      <CardTitle className="text-base truncate">{act.title}</CardTitle>
                      <Badge variant={meta.variant}>{meta.label}</Badge>
                    </div>
                    <div className="flex items-center gap-1.5 text-[11px] text-subtext flex-shrink-0">
                      <Users size={12} aria-hidden="true" />
                      {act.contributorCount} 人共建
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-[11px] text-subtext">
                      <span>
                        共建进度
                        {act.myContribution > 0 && (
                          <span className="ml-2 text-primary font-semibold">我已投放 {act.myContribution}</span>
                        )}
                      </span>
                      <span className="font-semibold text-ink">
                        {act.currentProgress} / {act.targetEnergy}（{ratio}%）
                      </span>
                    </div>
                    <Progress value={ratio} gradient={building ? 'primary' : 'success'} height={8} />
                  </div>

                  {building && (
                    <div className="flex items-center gap-2 flex-wrap">
                      {QUICK_AMOUNTS.map((amount) => (
                        <Button
                          key={amount}
                          size="sm"
                          variant={amount === 100 ? 'gradient' : 'outline'}
                          onClick={() => handleContribute(act.id, amount)}
                          disabled={pendingId === act.id || (energyBalance?.availableEnergy ?? 0) < amount}
                        >
                          <Zap size={12} aria-hidden="true" />
                          投放 {amount}
                        </Button>
                      ))}
                    </div>
                  )}

                  {act.status === 'unlocked' && (
                    <div className="rounded-xl bg-safe-50/60 border border-safe-500/20 p-3 text-xs text-ink">
                      活动已解锁！等待校方发布线下落地通知
                    </div>
                  )}

                  {act.status === 'notice_released' && act.noticeText && (
                    <div className="rounded-xl bg-primary/5 border border-primary/15 p-3 space-y-1">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-ink">
                        <Megaphone size={13} className="text-primary" aria-hidden="true" />
                        落地通知
                      </div>
                      <p className="text-xs text-ink leading-relaxed">{act.noticeText}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
