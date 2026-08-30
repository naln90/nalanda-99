import { useEffect, useState } from 'react';
import { BookMarked, CalendarRange, CheckCircle2, Loader2, Plus, Sparkles, Wand2 } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { api } from '../api/client';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Label } from '../components/ui/Label';
import { useToast } from '../components/ui/Toast';
import type { ThemeInfo, ThemeItem } from '../types';

/** 主题状态 → 展示文案与徽标样式 */
const STATUS_META: Record<string, { label: string; variant: 'secondary' | 'warning' | 'success' | 'info' | 'outline' }> = {
  draft: { label: '草稿', variant: 'secondary' },
  ai_generating: { label: 'AI生成中', variant: 'warning' },
  pending_confirm: { label: '待确认', variant: 'warning' },
  published: { label: '已发布', variant: 'success' },
  ended: { label: '已结束', variant: 'outline' },
  archived: { label: '已归档', variant: 'outline' },
};

const CATEGORY_LABEL: Record<string, string> = {
  required: '基础必修',
  elective: '兴趣选修',
  outcome: '成果任务',
};

/**
 * SchoolThemePage — 校方发布端：主题与任务包管理（V3.0 §3.1）
 * 流程：创建主题 → AI 生成任务包 → 校方确认发布
 */
export default function SchoolThemePage() {
  const currentUser = useAppStore((s) => s.currentUser);
  const schoolThemes = useAppStore((s) => s.schoolThemes);
  const isLoading = useAppStore((s) => s.isLoading);
  const error = useAppStore((s) => s.error);
  const schoolCreateTheme = useAppStore((s) => s.schoolCreateTheme);
  const schoolGenerateTheme = useAppStore((s) => s.schoolGenerateTheme);
  const schoolConfirmTheme = useAppStore((s) => s.schoolConfirmTheme);
  const { success, error: toastError } = useToast();

  const [showForm, setShowForm] = useState(false);
  const [expandedThemeId, setExpandedThemeId] = useState<string | null>(null);
  const [form, setForm] = useState({
    title: '',
    description: '',
    periodDays: 30,
    baseRequired: '识别刷单返利、冒充客服、校园贷等高发骗局',
    electiveDirection: '短视频创作 / 海报设计 / 情景剧本',
    expectedOutcome: '每人产出 1 份反诈宣传作品',
    baseAssessment: '完成基础测评并达到 60 分以上',
  });

  const ownerId = currentUser?.ownerId ?? '';

  // 首次加载主题列表
  useEffect(() => {
    if (!ownerId) return;
    api
      .listThemes(ownerId)
      .then((themes) => useAppStore.setState({ schoolThemes: themes }))
      .catch((err) => toastError(err instanceof Error ? err.message : '主题列表加载失败，请稍后重试'));
  }, [ownerId]);

  const handleCreate = async () => {
    if (!form.title.trim()) {
      toastError('请填写主题名称');
      return;
    }
    const theme = await schoolCreateTheme({ ownerId, ...form, title: form.title.trim() });
    if (theme) {
      success('主题已创建，可点击「AI 生成任务包」');
      setShowForm(false);
      setForm((f) => ({ ...f, title: '', description: '' }));
    }
  };

  const handleGenerate = async (themeId: string) => {
    await schoolGenerateTheme(themeId, ownerId);
    if (!useAppStore.getState().error) success('AI 任务包已生成，请审核确认');
  };

  const handleConfirm = async (themeId: string) => {
    await schoolConfirmTheme(themeId, ownerId);
    if (!useAppStore.getState().error) success('主题已确认发布，学生端可见');
  };

  const renderItems = (theme: ThemeInfo) => {
    const items = (theme.aiMetadata?.items ?? []) as ThemeItem[];
    if (!items.length) return null;
    const groups: Array<[string, ThemeItem[]]> = ['required', 'elective', 'outcome']
      .map((c) => [c, items.filter((i) => i.category === c)] as [string, ThemeItem[]])
      .filter(([, list]) => list.length > 0);
    return (
      <div className="space-y-3 mt-3">
        {groups.map(([category, list]) => (
          <div key={category}>
            <div className="text-xs font-bold text-subtext mb-1.5">{CATEGORY_LABEL[category] ?? category}</div>
            <div className="space-y-1.5">
              {list.map((item) => (
                <div key={item.id || item.title} className="flex items-start gap-2 rounded-xl bg-white/60 border border-white/60 p-2.5">
                  <BookMarked size={14} className="text-primary mt-0.5 flex-shrink-0" aria-hidden="true" />
                  <div className="min-w-0 flex-1">
                    <div className="text-[13px] font-semibold text-ink">{item.title}</div>
                    <div className="text-[11px] text-subtext leading-relaxed">{item.description}</div>
                    <div className="flex items-center gap-2 mt-1 text-[10px] text-subtext">
                      <span>约 {item.estimatedMinutes} 分钟</span>
                      <span>·</span>
                      <span>第 {item.dueDay} 天前</span>
                      <span>·</span>
                      <span className="text-primary font-semibold">+{item.energyReward} 盾能</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-5">
      {/* 页头 */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-xl font-extrabold text-ink flex items-center gap-2">
            <CalendarRange size={20} className="text-primary" aria-hidden="true" />
            主题与任务包
          </h1>
        </div>
        <Button onClick={() => setShowForm((v) => !v)} size="sm">
          <Plus size={14} aria-hidden="true" />
          {showForm ? '收起' : '创建新主题'}
        </Button>
      </div>

      {error && <div className="rounded-xl bg-danger/5 border border-danger/20 text-danger text-xs px-3 py-2">{error}</div>}

      {/* 创建表单 */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">创建月度主题</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid sm:grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="theme-title">主题名称 *</Label>
                <Input
                  id="theme-title"
                  placeholder="如：警惕刷单返利骗局"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="theme-period">周期（天）</Label>
                <Input
                  id="theme-period"
                  type="number"
                  min={7}
                  max={60}
                  value={form.periodDays}
                  onChange={(e) => setForm({ ...form, periodDays: Number(e.target.value) || 30 })}
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="theme-desc">主题说明</Label>
              <Input
                id="theme-desc"
                placeholder="主题背景与目标（可选）"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
            </div>
            <div className="grid sm:grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="theme-required">基础必修要求</Label>
                <Input
                  id="theme-required"
                  value={form.baseRequired}
                  onChange={(e) => setForm({ ...form, baseRequired: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="theme-elective">兴趣选修方向</Label>
                <Input
                  id="theme-elective"
                  value={form.electiveDirection}
                  onChange={(e) => setForm({ ...form, electiveDirection: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="theme-outcome">预期成果</Label>
                <Input
                  id="theme-outcome"
                  value={form.expectedOutcome}
                  onChange={(e) => setForm({ ...form, expectedOutcome: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="theme-assessment">基础考核标准</Label>
                <Input
                  id="theme-assessment"
                  value={form.baseAssessment}
                  onChange={(e) => setForm({ ...form, baseAssessment: e.target.value })}
                />
              </div>
            </div>
            <Button onClick={handleCreate} disabled={isLoading}>
              {isLoading ? <Loader2 size={14} className="animate-spin" aria-hidden="true" /> : <Plus size={14} aria-hidden="true" />}
              创建主题
            </Button>
          </CardContent>
        </Card>
      )}

      {/* 主题列表 */}
      <div className="space-y-3">
        {schoolThemes.length === 0 && !showForm && (
          <Card>
            <CardContent className="text-center text-sm text-subtext py-8">
              暂无主题，点击右上角「创建新主题」开始本月反诈主题发布
            </CardContent>
          </Card>
        )}
        {schoolThemes.map((theme) => {
          const meta = STATUS_META[theme.status] ?? { label: theme.status, variant: 'outline' as const };
          const expanded = expandedThemeId === theme.id;
          const hasDraftItems = Boolean((theme.aiMetadata?.items as ThemeItem[] | undefined)?.length);
          return (
            <Card key={theme.id}>
              <CardContent className="space-y-2">
                <div className="flex items-center justify-between gap-3 flex-wrap">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-[15px] font-bold text-ink truncate">{theme.title}</span>
                    <Badge variant={meta.variant}>{meta.label}</Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    {theme.status === 'draft' && (
                      <Button size="sm" onClick={() => handleGenerate(theme.id)} disabled={isLoading}>
                        <Wand2 size={13} aria-hidden="true" />
                        AI 生成任务包
                      </Button>
                    )}
                    {theme.status === 'pending_confirm' && (
                      <Button size="sm" variant="gradient" onClick={() => handleConfirm(theme.id)} disabled={isLoading}>
                        <CheckCircle2 size={13} aria-hidden="true" />
                        确认发布
                      </Button>
                    )}
                    {hasDraftItems && (
                      <Button size="sm" variant="outline" onClick={() => setExpandedThemeId(expanded ? null : theme.id)}>
                        {expanded ? '收起任务包' : '查看任务包'}
                      </Button>
                    )}
                  </div>
                </div>
                {theme.description && <p className="text-xs text-subtext">{theme.description}</p>}
                <div className="flex items-center gap-3 text-[11px] text-subtext flex-wrap">
                  <span className="inline-flex items-center gap-1">
                    <Sparkles size={11} className="text-primary" aria-hidden="true" />
                    周期 {theme.periodDays} 天
                  </span>
                  {theme.publishedAt && <span>发布于 {new Date(theme.publishedAt).toLocaleDateString('zh-CN')}</span>}
                  {theme.expectedOutcome && <span>预期成果：{theme.expectedOutcome}</span>}
                </div>
                {expanded && renderItems(theme)}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
