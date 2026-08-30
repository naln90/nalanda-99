import { useEffect, useState } from 'react';
import { Loader2, Megaphone, Plus, Send, Sprout, Users } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Label } from '../components/ui/Label';
import { Progress } from '../components/ui/Progress';
import { useToast } from '../components/ui/Toast';

const ACTIVITY_STATUS_META: Record<string, { label: string; variant: 'secondary' | 'warning' | 'success' | 'info' | 'outline' }> = {
  draft: { label: '草稿', variant: 'secondary' },
  building: { label: '共建中', variant: 'info' },
  unlocked: { label: '已解锁', variant: 'success' },
  notice_released: { label: '通知已发布', variant: 'success' },
  archived: { label: '已归档', variant: 'outline' },
};

/**
 * SchoolActivityPage — 校方发布端：守护活动管理（V3.0 §3.3 集体共建）
 * 校方创建活动 → 全体学生投放盾能 → 达标解锁 → 校方发布落地通知
 * 边界：系统仅展示/解锁/衔接通知，报名签到执行由学校线下完成
 */
export default function SchoolActivityPage() {
  const currentUser = useAppStore((s) => s.currentUser);
  const activities = useAppStore((s) => s.activities);
  const isLoading = useAppStore((s) => s.isLoading);
  const error = useAppStore((s) => s.error);
  const loadActivities = useAppStore((s) => s.loadActivities);
  const schoolCreateActivity = useAppStore((s) => s.schoolCreateActivity);
  const schoolReleaseNotice = useAppStore((s) => s.schoolReleaseNotice);
  const { success, error: toastError } = useToast();

  const [showForm, setShowForm] = useState(false);
  const [noticeDrafts, setNoticeDrafts] = useState<Record<string, string>>({});
  const [form, setForm] = useState({
    title: '',
    category: '线下讲座',
    description: '',
    organizer: '学生处 · 保卫处',
    interestDirection: '',
    targetEnergy: 500,
  });

  const ownerId = currentUser?.ownerId ?? '';

  useEffect(() => {
    if (ownerId) loadActivities(ownerId);
  }, [ownerId, loadActivities]);

  const handleCreate = async () => {
    if (!form.title.trim()) {
      toastError('请填写活动名称');
      return;
    }
    await schoolCreateActivity({ ownerId, ...form, title: form.title.trim() });
    if (!useAppStore.getState().error) {
      success('守护活动已创建，进入共建期');
      setShowForm(false);
      setForm((f) => ({ ...f, title: '', description: '' }));
    }
  };

  const handleRelease = async (activityId: string) => {
    const text = (noticeDrafts[activityId] ?? '').trim();
    if (!text) {
      toastError('请填写落地通知内容（时间/地点/参与方式）');
      return;
    }
    await schoolReleaseNotice(activityId, ownerId, text);
    if (!useAppStore.getState().error) success('落地通知已发布，学生端可见');
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-xl font-extrabold text-ink flex items-center gap-2">
            <Megaphone size={20} className="text-primary" aria-hidden="true" />
            守护活动管理
          </h1>
        </div>
        <Button onClick={() => setShowForm((v) => !v)} size="sm">
          <Plus size={14} aria-hidden="true" />
          {showForm ? '收起' : '创建守护活动'}
        </Button>
      </div>

      {error && <div className="rounded-xl bg-danger/5 border border-danger/20 text-danger text-xs px-3 py-2">{error}</div>}

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">创建集体共建活动</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid sm:grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="act-title">活动名称 *</Label>
                <Input
                  id="act-title"
                  placeholder="如：反诈情景剧专场"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="act-target">共建目标（盾能）</Label>
                <Input
                  id="act-target"
                  type="number"
                  min={100}
                  step={100}
                  value={form.targetEnergy}
                  onChange={(e) => setForm({ ...form, targetEnergy: Number(e.target.value) || 500 })}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="act-category">活动类型</Label>
                <Input
                  id="act-category"
                  placeholder="线下讲座 / 展演 / 工作坊"
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="act-organizer">主办方</Label>
                <Input
                  id="act-organizer"
                  value={form.organizer}
                  onChange={(e) => setForm({ ...form, organizer: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="act-desc">活动说明</Label>
              <Input
                id="act-desc"
                placeholder="活动内容简介（可选）"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
            </div>
            <Button onClick={handleCreate} disabled={isLoading}>
              {isLoading ? <Loader2 size={14} className="animate-spin" aria-hidden="true" /> : <Sprout size={14} aria-hidden="true" />}
              创建并开启共建
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="space-y-3">
        {activities.length === 0 && !showForm && (
          <Card>
            <CardContent className="text-center text-sm text-subtext py-8">
              暂无守护活动，点击右上角「创建守护活动」开启集体共建
            </CardContent>
          </Card>
        )}
        {activities.map((act) => {
          const meta = ACTIVITY_STATUS_META[act.status] ?? { label: act.status, variant: 'outline' as const };
          const ratio = Math.min(100, Math.round((act.currentProgress / Math.max(1, act.targetEnergy)) * 100));
          const canRelease = act.status === 'unlocked';
          return (
            <Card key={act.id}>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between gap-3 flex-wrap">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-[15px] font-bold text-ink truncate">{act.title}</span>
                    <Badge variant={meta.variant}>{meta.label}</Badge>
                    {act.category && <Badge variant="outline">{act.category}</Badge>}
                  </div>
                  <div className="flex items-center gap-1.5 text-[11px] text-subtext">
                    <Users size={12} aria-hidden="true" />
                    {act.contributorCount} 人参与共建
                  </div>
                </div>

                {act.description && <p className="text-xs text-subtext">{act.description}</p>}

                <div className="space-y-1">
                  <div className="flex items-center justify-between text-[11px] text-subtext">
                    <span>共建进度</span>
                    <span className="font-semibold text-ink">
                      {act.currentProgress} / {act.targetEnergy} 盾能（{ratio}%）
                    </span>
                  </div>
                  <Progress value={ratio} gradient={act.status === 'building' ? 'primary' : 'success'} height={8} />
                </div>

                {canRelease && (
                  <div className="rounded-xl bg-safe-50/60 border border-safe-500/20 p-3 space-y-2">
                    <div className="text-xs font-bold text-ink">活动已解锁，请发布落地通知</div>
                    <Input
                      placeholder="填写时间 / 地点 / 参与方式，如：11月15日 14:00 大学生活动中心报告厅"
                      value={noticeDrafts[act.id] ?? ''}
                      onChange={(e) => setNoticeDrafts({ ...noticeDrafts, [act.id]: e.target.value })}
                    />
                    <Button size="sm" onClick={() => handleRelease(act.id)} disabled={isLoading}>
                      <Send size={13} aria-hidden="true" />
                      发布通知
                    </Button>
                  </div>
                )}

                {act.status === 'notice_released' && act.noticeText && (
                  <div className="rounded-xl bg-primary/5 border border-primary/15 p-3 text-xs text-ink">
                    <span className="font-bold">落地通知：</span>
                    {act.noticeText}
                  </div>
                )}

                <p className="text-[10px] text-subtext/80 leading-relaxed">{act.boundaryNotice}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
