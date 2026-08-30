import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  CalendarClock,
  Check,
  CheckCircle2,
  Clock3,
  Code2,
  FileUp,
  Loader2,
  LockKeyhole,
  MessageCircleMore,
  Pencil,
  RefreshCw,
  Send,
  Share2,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Target,
  X,
} from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/useAppStore';
import { resolveThemeProfile } from '../lib/themeProfile';
import type {
  CodeDebugResult,
  LearningDashboard,
  LearningPlanItem,
  LearningTaskCategory,
} from '../types/learning';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { useToast } from '../components/ui/Toast';

const categoryMeta: Record<LearningTaskCategory, { label: string; desc: string; color: string }> = {
  required: {
    label: '基础必修',
    desc: '保证共同的主题学习基础',
    color: 'border-blue-200 bg-blue-50/70 text-blue-700',
  },
  elective: {
    label: '兴趣选修',
    desc: '按兴趣选择，不要求全部方向',
    color: 'border-violet-200 bg-violet-50/70 text-violet-700',
  },
  outcome: {
    label: '成果任务',
    desc: '把学习转化为可展示成果',
    color: 'border-amber-200 bg-amber-50/70 text-amber-700',
  },
};

export default function LearningWorkspacePage() {
  const navigate = useNavigate();
  const ownerId = useAppStore((state) => state.currentUser?.ownerId) ?? '';
  const { success, error: showError } = useToast();
  const [dashboard, setDashboard] = useState<LearningDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<string | null>(null);
  const [editingItem, setEditingItem] = useState<LearningPlanItem | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editMinutes, setEditMinutes] = useState(20);
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<Array<{ role: 'pet' | 'user'; text: string }>>([
    {
      role: 'pet',
      text: '我是你的学习陪伴。可以问我“今天先做什么”、某个知识点，或成果应该怎样修改。',
    },
  ]);
  const [chatLoading, setChatLoading] = useState(false);

  // 延期申请（需求#11）
  const [extendOpen, setExtendOpen] = useState(false);
  const [extraDays, setExtraDays] = useState(3);
  const [extendReason, setExtendReason] = useState('');
  const [extensions, setExtensions] = useState<Array<{ id: number; extraDays: number; reason: string; status: string; createdAt: string }>>([]);

  // 代码调试答疑（需求#16）
  const [codeOpen, setCodeOpen] = useState(false);
  const [codeLang, setCodeLang] = useState('python');
  const [codeText, setCodeText] = useState('');
  const [codeQuestion, setCodeQuestion] = useState('');
  const [codeResult, setCodeResult] = useState<CodeDebugResult | null>(null);
  const [codeLoading, setCodeLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const ld = await api.getLearningDashboard(ownerId);
      setDashboard(ld);
      useAppStore.getState().setActiveLearningTheme(ld.goal?.theme ?? ld.plan?.title ?? null);
    } catch (err) {
      showError(err instanceof Error ? err.message : '学习工作台加载失败');
    } finally {
      setLoading(false);
    }
  }, [ownerId, showError]);

  useEffect(() => {
    void load();
  }, [load]);

  const grouped = useMemo(() => {
    const items = dashboard?.plan?.items ?? [];
    return {
      required: items.filter((item) => item.category === 'required'),
      elective: items.filter((item) => item.category === 'elective'),
      outcome: items.filter((item) => item.category === 'outcome'),
    };
  }, [dashboard?.plan?.items]);

  // 陪伴角色随当前任务包主题变化（人物设计主题化）：AI素养=小盾灵，Python=小码灵，其它=小知灵
  const planTitle = dashboard?.plan?.title ?? '';
  const themeProfile = useMemo(() => resolveThemeProfile(planTitle), [planTitle]);
  useEffect(() => {
    // 仅在尚未开始对话（仅剩初始开场白）时，把陪伴角色同步为对应主题角色
    setChatMessages((prev) => {
      if (prev.length === 1 && prev[0].role === 'pet') {
        return [{ role: 'pet', text: themeProfile.companionIntro }];
      }
      return prev;
    });
  }, [themeProfile]);

  const completeTask = async (item: LearningPlanItem) => {
    setActionId(item.id);
    try {
      const result = await api.completeLearningPlanItem(item.id, ownerId, '已在学习工作台完成并记录');
      success(result.message);
      await load();
    } catch (err) {
      showError(err instanceof Error ? err.message : '任务完成失败');
    } finally {
      setActionId(null);
    }
  };

  const replaceTask = async (item: LearningPlanItem) => {
    setActionId(item.id);
    const directions = ['AI对练', '案例研判', '创意表达', '情境挑战'];
    const currentIndex = directions.findIndex((direction) => item.title.includes(direction.replace('AI', '')));
    const direction = directions[(currentIndex + 1) % directions.length];
    try {
      const result = await api.replaceLearningPlanItem(item.id, ownerId, direction);
      success(result.message);
      await load();
    } catch (err) {
      showError(err instanceof Error ? err.message : '任务替换失败');
    } finally {
      setActionId(null);
    }
  };

  const openEdit = (item: LearningPlanItem) => {
    setEditingItem(item);
    setEditTitle(item.title);
    setEditMinutes(item.estimatedMinutes);
  };

  const saveEdit = async () => {
    if (!editingItem) return;
    setActionId(editingItem.id);
    try {
      await api.updateLearningPlanItem(editingItem.id, {
        ownerId,
        title: editTitle,
        estimatedMinutes: editMinutes,
      });
      setEditingItem(null);
      success('任务已调整，修改记录已保留');
      await load();
    } catch (err) {
      showError(err instanceof Error ? err.message : '任务修改失败');
    } finally {
      setActionId(null);
    }
  };

  const sharePlan = async () => {
    if (!dashboard?.plan) return;
    try {
      const result = await api.shareLearningPlan(dashboard.plan.id, ownerId);
      success(result.message);
    } catch (err) {
      showError(err instanceof Error ? err.message : '任务包分享失败');
    }
  };

  const askCompanion = async () => {
    const message = chatInput.trim();
    if (!message || !dashboard?.plan) return;
    setChatInput('');
    setChatMessages((current) => [...current, { role: 'user', text: message }]);
    setChatLoading(true);
    try {
      const result = await api.askLearningCompanion(ownerId, dashboard.plan.id, message);
      setChatMessages((current) => [...current, { role: 'pet', text: result.reply }]);
    } catch (err) {
      setChatMessages((current) => [
        ...current,
        { role: 'pet', text: err instanceof Error ? err.message : '暂时无法回答，请稍后重试。' },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const requestExtension = async () => {
    if (!dashboard?.plan) return;
    try {
      const result = await api.requestPlanExtension(dashboard.plan.id, {
        ownerId,
        extraDays,
        reason: extendReason,
      });
      setExtensions(result.extensions);
      setExtendOpen(false);
      setExtendReason('');
      success(result.message);
      await load();
    } catch (err) {
      showError(err instanceof Error ? err.message : '延期申请失败');
    }
  };

  const runCodeDebug = async () => {
    if (!codeQuestion.trim()) {
      showError('请描述你遇到的问题');
      return;
    }
    setCodeLoading(true);
    try {
      const result = await api.codeDebug({
        ownerId,
        planId: dashboard?.plan?.id ?? '',
        language: codeLang,
        code: codeText,
        question: codeQuestion,
      });
      setCodeResult(result);
    } catch (err) {
      showError(err instanceof Error ? err.message : '代码答疑失败');
    } finally {
      setCodeLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[420px] items-center justify-center text-subtext">
        <Loader2 className="mr-2 animate-spin" size={20} />
        正在整理你的学习任务包...
      </div>
    );
  }

  if (!dashboard?.plan || !dashboard.goal) {
    return (
      <div className="app-card mx-auto max-w-xl p-8 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-primary-soft text-primary">
          <Target size={30} />
        </div>
        <h1 className="mt-4 text-xl font-extrabold text-ink">还没有正在进行的学习目标</h1>
        <Button className="mt-5" onClick={() => navigate('/learning/goal')}>
          发布学习目标
          <ArrowRight size={16} />
        </Button>
      </div>
    );
  }

  const { plan, goal } = dashboard;
  return (
    <div className="space-y-5 animate-slide-up">
      <section className="overflow-hidden rounded-3xl border border-primary/15 bg-gradient-to-br from-white via-primary-soft/35 to-cyan-50 p-5 shadow-card">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-2xl">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="info">AI任务包</Badge>
              <Badge variant="outline">{goal.learningType}</Badge>
              <span className="text-[11px] text-subtext">{plan.source}</span>
            </div>
            <h1 className="mt-3 text-xl font-extrabold text-ink sm:text-2xl">{plan.title}</h1>
            <p className="mt-2 text-sm leading-6 text-subtext">{plan.summary}</p>
            <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-subtext">
              <span className="inline-flex items-center gap-1"><Clock3 size={13} />{goal.periodDays}天</span>
              <span>每天约{goal.dailyMinutes}分钟</span>
              <span>{goal.difficulty}难度</span>
              <span>选修方向：{goal.electiveTracks.join('、')}</span>
              {plan.extensionDays > 0 && (
                <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 font-semibold text-amber-700">
                  <CalendarClock size={13} />已延期 {plan.extensionDays} 天
                </span>
              )}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={() => setExtendOpen(true)}>
              <CalendarClock size={15} />
              申请延期
            </Button>
            <Button variant="outline" size="sm" onClick={sharePlan}>
              <Share2 size={15} />
              分享任务包
            </Button>
            <Button size="sm" onClick={() => navigate('/learning/artifacts')}>
              <FileUp size={15} />
              提交成果
            </Button>
          </div>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-4">
          <Metric label="整体进度" value={`${plan.progress}%`} icon={<Target size={16} />} />
          <Metric label="已完成任务" value={`${plan.completedCount}/${plan.totalCount}`} icon={<CheckCircle2 size={16} />} />
          <Metric label="盾能" value={String(plan.shieldEnergy)} icon={<Sparkles size={16} />} />
          <Metric label="永久守护值" value={String(plan.guardianValue)} icon={<ShieldCheck size={16} />} />
        </div>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-white">
          <div
            className="h-full rounded-full bg-gradient-to-r from-primary to-cyan-500 transition-all"
            style={{ width: `${plan.progress}%` }}
          />
        </div>
      </section>

      <div className="grid gap-5 xl:grid-cols-[1.45fr_0.75fr]">
        <main className="space-y-4">
          {(['required', 'elective', 'outcome'] as const).map((category) => (
            <section key={category} className="app-card p-4">
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    {category === 'required' && <LockKeyhole className="text-blue-600" size={17} />}
                    {category === 'elective' && <Sparkles className="text-violet-600" size={17} />}
                    {category === 'outcome' && <FileUp className="text-amber-600" size={17} />}
                    <h2 className="text-sm font-extrabold text-ink">{categoryMeta[category].label}</h2>
                  </div>
                  <p className="mt-0.5 text-[11px] text-subtext">{categoryMeta[category].desc}</p>
                </div>
                <Badge variant="outline" size="sm">
                  {grouped[category].filter((item) => item.status === 'completed').length}/{grouped[category].length}
                </Badge>
              </div>
              <div className="space-y-3">
                {grouped[category].map((item) => (
                  <TaskCard
                    key={item.id}
                    item={item}
                    busy={actionId === item.id}
                    onComplete={() => completeTask(item)}
                    onEdit={() => openEdit(item)}
                    onReplace={() => replaceTask(item)}
                    onOpen={() => {
                      if (item.category === 'outcome') navigate('/learning/artifacts');
                      else if (item.title.includes('测评')) navigate('/assessment');
                      else if (item.title.includes('情境')) navigate('/training');
                      else navigate(`/learning/workspace/task/${item.id}`);
                    }}
                  />
                ))}
              </div>
            </section>
          ))}

          <section className="app-card overflow-hidden">
            <button
              onClick={() => setCodeOpen((open) => !open)}
              className="flex w-full items-center justify-between px-4 py-3 text-left"
            >
              <div className="flex items-center gap-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-primary text-white shadow-glow-sm">
                  <Code2 size={19} />
                </div>
                <div>
                  <h2 className="text-sm font-extrabold text-ink">代码调试答疑</h2>
                  <p className="text-[10px] text-subtext">贴入代码与问题，获得思路引导与安全提示（不代写）</p>
                </div>
              </div>
              <span className="text-xs text-primary">{codeOpen ? '收起' : '展开'}</span>
              <span className="text-[10px] text-subtext">选择语言以获得更精准的静态检查</span>
            </button>

            {codeOpen && (
              <div className="space-y-3 border-t border-border p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <select
                    value={codeLang}
                    onChange={(event) => setCodeLang(event.target.value)}
                    className="rounded-xl border border-border bg-white px-3 py-2 text-xs outline-none focus:border-primary"
                  >
                    <option value="python">Python</option>
                    <option value="javascript">JavaScript</option>
                    <option value="typescript">TypeScript</option>
                    <option value="sql">SQL</option>
                    <option value="java">Java</option>
                  </select>
                </div>
                <textarea
                  value={codeText}
                  onChange={(event) => setCodeText(event.target.value)}
                  rows={6}
                  className="w-full resize-none rounded-2xl border border-border px-3 py-3 font-mono text-xs leading-5 outline-none focus:border-primary"
                  placeholder="在此粘贴需要排查的代码片段（可留空，仅描述问题也可）"
                />
                <textarea
                  value={codeQuestion}
                  onChange={(event) => setCodeQuestion(event.target.value)}
                  rows={2}
                  className="w-full resize-none rounded-2xl border border-border px-3 py-2.5 text-xs leading-5 outline-none focus:border-primary"
                  placeholder="描述你遇到的问题，例如：运行时报 NameError，不知道缺了什么。"
                />
                <div className="flex justify-end">
                  <Button onClick={runCodeDebug} loading={codeLoading}>
                    <Code2 size={15} />分析代码
                  </Button>
                </div>

                {codeResult && (
                  <div className="space-y-3 rounded-2xl bg-muted/50 p-4">
                    <ResultBlock title="检测到的潜在问题" items={codeResult.detectedIssues} icon={<AlertTriangle size={13} className="mt-0.5 shrink-0 text-danger" />} empty="未发现明显结构问题" />
                    <ResultBlock title="排查思路与建议" items={codeResult.hints} icon={<Code2 size={13} className="mt-0.5 shrink-0 text-primary" />} />
                    <ResultBlock title="安全与合规提示" items={codeResult.safetyNotes} icon={<ShieldAlert size={13} className="mt-0.5 shrink-0 text-amber-500" />} empty="未发现明显安全风险" />
                    <p className="rounded-xl bg-primary-soft/60 px-3 py-2 text-[11px] leading-5 text-primary">{codeResult.nextStep}</p>
                    <p className="text-[10px] text-subtext">{codeResult.source}</p>
                  </div>
                )}
              </div>
            )}
          </section>
        </main>

        <aside className="space-y-4">
          <section className="app-card overflow-hidden">
            <div className="border-b border-border bg-gradient-to-r from-primary-soft to-violet-50 px-4 py-3">
              <div className="flex items-center gap-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-primary text-white shadow-glow-sm">
                  <span className="text-lg leading-none">{themeProfile.companionEmoji}</span>
                </div>
                <div>
                  <h2 className="text-sm font-extrabold text-ink">{themeProfile.companionName}学习陪伴</h2>
                  <p className="text-[10px] text-subtext">基于当前任务提供方法引导，不代做成果</p>
                </div>
              </div>
            </div>
            <div className="max-h-72 space-y-3 overflow-y-auto p-4">
              {chatMessages.map((message, index) => (
                <div
                  key={`${message.role}-${index}`}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[88%] rounded-2xl px-3 py-2 text-xs leading-5 ${
                      message.role === 'user'
                        ? 'rounded-br-md bg-primary text-white'
                        : 'rounded-bl-md border border-border bg-white text-ink'
                    }`}
                  >
                    {message.text}
                  </div>
                </div>
              ))}
              {chatLoading && (
                <div className="flex items-center gap-2 text-xs text-subtext">
                  <Loader2 className="animate-spin" size={13} />
                  {themeProfile.companionName}正在结合任务包思考...
                </div>
              )}
            </div>
            <div className="border-t border-border p-3">
              <div className="flex gap-2">
                <input
                  value={chatInput}
                  onChange={(event) => setChatInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') void askCompanion();
                  }}
                  placeholder="例如：今天先做什么？"
                  className="min-w-0 flex-1 rounded-xl border border-border bg-white px-3 py-2 text-xs outline-none focus:border-primary"
                />
                <Button size="icon-sm" onClick={askCompanion} disabled={chatLoading || !chatInput.trim()}>
                  <Send size={14} />
                </Button>
              </div>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {['今天先做什么？', '成果应该怎么改？'].map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => setChatInput(prompt)}
                    className="rounded-full bg-muted px-2 py-1 text-[10px] text-subtext hover:text-primary"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          </section>

          <button
            onClick={() => navigate('/learning/activities')}
            className="w-full rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-4 text-left transition hover:-translate-y-0.5 hover:shadow-card"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="text-emerald-600" size={18} />
                <span className="text-sm font-extrabold text-ink">校园活动发现</span>
              </div>
              <ArrowRight className="text-emerald-600" size={16} />
            </div>
            <p className="mt-2 text-xs leading-5 text-subtext">
              完成主题学习与成果后，可解锁由学校团委组织的实践活动；解锁不强制参加。
            </p>
          </button>

          <div className="rounded-2xl border border-border bg-white/70 p-4">
            <div className="flex items-center gap-2 text-xs font-bold text-ink">
              <BookOpen size={15} className="text-primary" />
              任务包设计说明
            </div>
            <ul className="mt-2 space-y-1.5 text-[11px] leading-5 text-subtext">
              <li>• 基础必修保证共同学习底线</li>
              <li>• 兴趣选修支持替换与个性选择</li>
              <li>• 成果任务要求版本留存与AI初审</li>
            </ul>
          </div>
        </aside>
      </div>

      {extendOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-3xl border border-white/60 bg-white p-5 shadow-2xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CalendarClock className="text-primary" size={18} />
                <h2 className="font-extrabold text-ink">申请延长学习周期</h2>
              </div>
              <button
                onClick={() => setExtendOpen(false)}
                aria-label="关闭"
                className="rounded-full p-1.5 text-subtext transition hover:bg-muted hover:text-ink"
              >
                <X size={18} />
              </button>
            </div>
            <p className="mt-1 text-xs text-subtext">提交后将进入审核队列，由辅导员审批通过后生效。</p>
            <label className="mt-4 block space-y-1.5">
              <span className="text-xs font-bold text-ink">延长天数（1—60）</span>
              <input
                type="number"
                min={1}
                max={60}
                value={extraDays}
                onChange={(event) => setExtraDays(Number(event.target.value))}
                className="w-full rounded-xl border border-border px-3 py-2.5 text-sm outline-none focus:border-primary"
              />
            </label>
            <label className="mt-3 block space-y-1.5">
              <span className="text-xs font-bold text-ink">申请说明（可选）</span>
              <textarea
                value={extendReason}
                onChange={(event) => setExtendReason(event.target.value)}
                rows={3}
                className="w-full resize-none rounded-xl border border-border px-3 py-2.5 text-xs leading-5 outline-none focus:border-primary"
                placeholder="例如：近期考试冲突，希望延长一周完成成果任务。"
              />
            </label>
            {extensions.length > 0 && (
              <div className="mt-3 rounded-xl bg-muted/60 px-3 py-2 text-[11px] leading-5 text-subtext">
                <span className="font-bold text-ink">已批准延期记录：</span>
                {extensions.map((ext) => (
                  <span key={ext.id} className="ml-1">+{ext.extraDays}天</span>
                ))}
              </div>
            )}
            <div className="mt-5 flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setExtendOpen(false)}>取消</Button>
              <Button onClick={requestExtension}><CalendarClock size={15} />提交申请</Button>
            </div>
          </div>
        </div>
      )}

      {editingItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-3xl border border-white/60 bg-white p-5 shadow-2xl">
            <div className="flex items-center gap-2">
              <Pencil className="text-primary" size={18} />
              <h2 className="font-extrabold text-ink">微调任务</h2>
              <p className="mt-1 text-xs text-subtext">AI生成后仍由学生决定任务名称与投入时间。</p>
            </div>
            <label className="mt-4 block space-y-1.5">
              <span className="text-xs font-bold text-ink">任务名称</span>
              <input
                value={editTitle}
                onChange={(event) => setEditTitle(event.target.value)}
                className="w-full rounded-xl border border-border px-3 py-2.5 text-sm outline-none focus:border-primary"
              />
            </label>
            <label className="mt-3 block space-y-1.5">
              <span className="text-xs font-bold text-ink">预计时长（分钟）</span>
              <input
                type="number"
                min={5}
                max={240}
                value={editMinutes}
                onChange={(event) => setEditMinutes(Number(event.target.value))}
                className="w-full rounded-xl border border-border px-3 py-2.5 text-sm outline-none focus:border-primary"
              />
            </label>
            <div className="mt-5 flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setEditingItem(null)}>取消</Button>
              <Button onClick={saveEdit} loading={actionId === editingItem.id}>保存修改</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Metric({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-white/70 bg-white/75 p-3">
      <div className="flex items-center gap-1.5 text-[10px] text-subtext">{icon}{label}</div>
      <div className="mt-1 text-lg font-extrabold text-ink">{value}</div>
    </div>
  );
}

function ResultBlock({
  title,
  items,
  empty,
  icon,
}: {
  title: string;
  items?: string[];
  empty?: string;
  icon: React.ReactNode;
}) {
  return (
    <div>
      <p className="mb-2 text-xs font-bold text-ink">{title}</p>
      {items && items.length > 0 ? (
        <ul className="space-y-1.5">
          {items.map((item, idx) => (
            <li key={idx} className="flex gap-2 text-[11px] leading-5 text-subtext">
              {icon}
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-[11px] leading-5 text-subtext">{empty ?? '无'}</p>
      )}
    </div>
  );
}

function TaskCard({
  item,
  busy,
  onComplete,
  onEdit,
  onReplace,
  onOpen,
}: {
  item: LearningPlanItem;
  busy: boolean;
  onComplete: () => void;
  onEdit: () => void;
  onReplace: () => void;
  onOpen: () => void;
}) {
  const completed = item.status === 'completed';
  return (
    <article className={`rounded-2xl border p-3 transition ${completed ? 'border-safe-500/25 bg-safe-50/60' : 'border-border bg-white hover:border-primary/25'}`}>
      <div className="flex items-start gap-3">
        <button
          onClick={onComplete}
          disabled={completed || busy}
          aria-label={completed ? '任务已完成' : '标记任务完成'}
          className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-xl border transition ${
            completed ? 'border-safe-500 bg-safe-500 text-white' : 'border-border bg-white text-subtext hover:border-primary hover:text-primary'
          }`}
        >
          {busy ? <Loader2 className="animate-spin" size={14} /> : <Check size={14} />}
        </button>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className={`text-sm font-bold ${completed ? 'text-safe-600' : 'text-ink'}`}>{item.title}</h3>
            <Badge className={categoryMeta[item.category].color} size="sm">{categoryMeta[item.category].label}</Badge>
          </div>
          <p className="mt-1 text-xs leading-5 text-subtext">{item.description}</p>
          <div className="mt-2 grid gap-2 sm:grid-cols-2">
            <div className="rounded-xl bg-muted/60 px-2.5 py-2 text-[10px] leading-4 text-subtext">
              <span className="font-bold text-ink">资源：</span>{item.resourceHint}
            </div>
            <div className="rounded-xl bg-muted/60 px-2.5 py-2 text-[10px] leading-4 text-subtext">
              <span className="font-bold text-ink">完成标准：</span>{item.acceptanceCriteria}
            </div>
          </div>
          <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
            <span className="inline-flex items-center gap-1 text-[10px] text-subtext">
              <Clock3 size={11} />第{item.dueDay}天 · 约{item.estimatedMinutes}分钟
            </span>
            <div className="flex gap-1.5">
              {!completed && item.category === 'elective' && (
                <Button size="xs" variant="ghost" onClick={onReplace}>
                  <RefreshCw size={12} />换一个
                </Button>
              )}
              {!completed && (
                <Button size="xs" variant="ghost" onClick={onEdit}>
                  <Pencil size={12} />微调
                </Button>
              )}
              <Button size="xs" variant={completed ? 'outline' : 'secondary'} onClick={onOpen}>
                {item.category === 'outcome' ? <FileUp size={12} /> : <MessageCircleMore size={12} />}
                {completed ? '查看记录' : '进入任务'}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}

