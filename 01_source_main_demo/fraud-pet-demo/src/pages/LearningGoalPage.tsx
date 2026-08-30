import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  BookOpenCheck,
  BrainCircuit,
  Check,
  Clock3,
  FileOutput,
  Lightbulb,
  ListChecks,
  Sparkles,
  Target,
  X,
} from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/useAppStore';
import type { GoalValidation, LearningTemplate } from '../types/learning';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { useToast } from '../components/ui/Toast';

const electiveOptions = ['情境挑战', '案例研判', 'AI对练', '创意表达', '实操练习'];

export default function LearningGoalPage() {
  const navigate = useNavigate();
  const ownerId = useAppStore((state) => state.currentUser?.ownerId) ?? '';
  const { success, error: showError } = useToast();
  const [templates, setTemplates] = useState<LearningTemplate[]>([]);
  const [theme, setTheme] = useState('AI素养与智能工具应用');
  const [learningType, setLearningType] = useState('自主学习');
  const [periodDays, setPeriodDays] = useState(14);
  const [dailyMinutes, setDailyMinutes] = useState(20);
  const [difficulty, setDifficulty] = useState('进阶');
  const [expectedOutcome, setExpectedOutcome] = useState('完成一份AI工具学习应用指南');
  const [majorDirection, setMajorDirection] = useState('通识能力');
  const [electiveTracks, setElectiveTracks] = useState<string[]>(['情境挑战', '案例研判', '创意表达']);
  const [customTags, setCustomTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [validation, setValidation] = useState<GoalValidation | null>(null);
  const [loading, setLoading] = useState(false);
  const [detailTemplate, setDetailTemplate] = useState<LearningTemplate | null>(null);

  useEffect(() => {
    api
      .getLearningTemplates()
      .then((result) => setTemplates(result.templates))
      .catch((err) => showError(err instanceof Error ? err.message : '模板加载失败，可手动填写'));
  }, [showError]);

  const normalizedPreview = useMemo(
    () =>
      `在 ${periodDays} 天内围绕“${theme || '学习主题'}”开展${difficulty}学习，每天约 ${dailyMinutes} 分钟，最终${expectedOutcome || '形成一项学习成果'}。`,
    [dailyMinutes, difficulty, expectedOutcome, periodDays, theme],
  );

  const toggleElective = (track: string) => {
    setElectiveTracks((current) =>
      current.includes(track) ? current.filter((item) => item !== track) : [...current, track].slice(-3),
    );
    setValidation(null);
  };

  const addTag = () => {
    const t = tagInput.trim();
    if (!t) return;
    if (customTags.includes(t)) {
      setTagInput('');
      return;
    }
    if (customTags.length >= 8) {
      showError('最多添加 8 个自定义标签');
      return;
    }
    setCustomTags((prev) => [...prev, t]);
    setTagInput('');
  };
  const removeTag = (t: string) => setCustomTags((prev) => prev.filter((x) => x !== t));

  const applyTemplate = (template: LearningTemplate) => {
    setTheme(template.theme);
    setPeriodDays(template.periodDays);
    setDailyMinutes(template.dailyMinutes);
    setDifficulty(template.difficulty);
    setExpectedOutcome(template.expectedOutcome);
    setElectiveTracks(template.electiveTracks);
    setCustomTags([]);
    setTagInput('');
    setValidation(null);
    success(`已载入“${template.title}”，仍可继续修改`);
  };

  const validate = async () => {
    if (!theme.trim() || !expectedOutcome.trim()) {
      showError('请先填写学习主题和预期成果');
      return null;
    }
    setLoading(true);
    try {
      const result = await api.validateLearningGoal({
        theme,
        periodDays,
        dailyMinutes,
        difficulty,
        expectedOutcome,
      });
      setValidation(result);
      return result;
    } catch (err) {
      showError(err instanceof Error ? err.message : '目标校验失败');
      return null;
    } finally {
      setLoading(false);
    }
  };

  const generate = async () => {
    if (!theme.trim() || !expectedOutcome.trim()) {
      showError('请先填写学习主题和预期成果');
      return;
    }
    setLoading(true);
    try {
      const check = validation ?? (await validate());
      if (!check) return;
      if (electiveTracks.length === 0) {
        showError('请至少选择一个兴趣学习方向');
        return;
      }
      const result = await api.createLearningGoal({
        ownerId,
        theme,
        learningType,
        periodDays,
        dailyMinutes,
        difficulty,
        expectedOutcome,
        majorDirection,
        electiveTracks,
        tags: customTags,
      });
      success(result.message);
      navigate('/learning/workspace');
    } catch (err) {
      showError(err instanceof Error ? err.message : '任务包生成失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-slide-up">
      <section className="rounded-3xl border border-violet-200/70 bg-gradient-to-br from-violet-50 via-white to-cyan-50 p-6 shadow-card">
        <div className="max-w-3xl">
          <Badge className="mb-3 border-violet-200/70 bg-white/80 text-violet-700">AI学习集市 · 第一步</Badge>
          <h1 className="text-2xl font-extrabold tracking-tight text-ink sm:text-3xl">把“我想学”变成可执行任务包</h1>
        </div>
      </section>

      <div className="grid gap-5 xl:grid-cols-[1.45fr_0.8fr]">
        <section className="app-card space-y-5 p-5">
          <div className="flex items-center gap-2">
            <Target className="text-primary" size={20} />
            <div>
              <h2 className="font-extrabold text-ink">发布学习目标</h2>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="space-y-1.5 sm:col-span-2">
              <span className="text-xs font-bold text-ink">学习主题</span>
              <input
                value={theme}
                onChange={(event) => {
                  setTheme(event.target.value);
                  setValidation(null);
                }}
                className="w-full rounded-xl border border-border bg-white px-3 py-2.5 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/15"
                placeholder="例如：AI素养与智能工具应用 / 心理健康 / Python编程入门"
              />
            </label>

            <label className="space-y-1.5">
              <span className="text-xs font-bold text-ink">学习类型</span>
              <select
                value={learningType}
                onChange={(event) => setLearningType(event.target.value)}
                className="w-full rounded-xl border border-border bg-white px-3 py-2.5 text-sm outline-none focus:border-primary"
              >
                <option>自主学习</option>
                <option>项目学习</option>
              </select>
            </label>

            <label className="space-y-1.5">
              <span className="text-xs font-bold text-ink">适用方向</span>
              <select
                value={majorDirection}
                onChange={(event) => setMajorDirection(event.target.value)}
                className="w-full rounded-xl border border-border bg-white px-3 py-2.5 text-sm outline-none focus:border-primary"
              >
                <option>通识能力</option>
                <option>数字安全</option>
                <option>专业课程</option>
                <option>创新项目</option>
              </select>
            </label>

            <label className="space-y-1.5">
              <span className="text-xs font-bold text-ink">学习周期</span>
              <div className="relative">
                <Clock3 className="absolute left-3 top-3 text-subtext" size={15} />
                <input
                  type="number"
                  min={3}
                  max={180}
                  value={periodDays}
                  onChange={(event) => {
                    setPeriodDays(Number(event.target.value));
                    setValidation(null);
                  }}
                  className="w-full rounded-xl border border-border bg-white py-2.5 pl-9 pr-10 text-sm outline-none focus:border-primary"
                />
              </div>
            </label>

            <label className="space-y-1.5">
              <span className="text-xs font-bold text-ink">每日可用时长</span>
              <div className="relative">
                <input
                  type="number"
                  min={10}
                  max={240}
                  value={dailyMinutes}
                  onChange={(event) => {
                    setDailyMinutes(Number(event.target.value));
                    setValidation(null);
                  }}
                  className="w-full rounded-xl border border-border bg-white px-3 py-2.5 pr-14 text-sm outline-none focus:border-primary"
                />
              </div>
            </label>

            <label className="space-y-1.5">
              <span className="text-xs font-bold text-ink">难度</span>
              <select
                value={difficulty}
                onChange={(event) => {
                  setDifficulty(event.target.value);
                  setValidation(null);
                }}
                className="w-full rounded-xl border border-border bg-white px-3 py-2.5 text-sm outline-none focus:border-primary"
              >
                <option>入门</option>
                <option>进阶</option>
                <option>挑战</option>
              </select>
            </label>

            <label className="space-y-1.5 sm:col-span-2">
              <span className="text-xs font-bold text-ink">预期成果</span>
              <div className="relative">
                <FileOutput className="absolute left-3 top-3 text-subtext" size={15} />
                <input
                  value={expectedOutcome}
                  onChange={(event) => {
                    setExpectedOutcome(event.target.value);
                    setValidation(null);
                  }}
                  className="w-full rounded-xl border border-border bg-white py-2.5 pl-9 pr-3 text-sm outline-none focus:border-primary"
                  placeholder="例如：完成一份主题学习成果或作品"
                />
              </div>
            </label>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs font-bold text-ink">兴趣选修方向</span>
              <span className="text-[11px] text-subtext">自主选择1—3项，不要求全部参加</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {electiveOptions.map((track) => {
                const selected = electiveTracks.includes(track);
                return (
                  <button
                    key={track}
                    type="button"
                    onClick={() => toggleElective(track)}
                    className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-2 text-xs font-semibold transition ${
                      selected
                        ? 'border-primary bg-primary text-white shadow-glow-sm'
                        : 'border-border bg-white text-subtext hover:border-primary/40 hover:text-primary'
                    }`}
                  >
                    {selected && <Check size={13} />}
                    {track}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs font-bold text-ink">自定义标签</span>
              <span className="text-[11px] text-subtext">为学习目标添加归档标签（最多 8 个）</span>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {customTags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 rounded-full border border-primary/30 bg-primary-soft/60 px-2.5 py-1 text-xs font-semibold text-primary"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => removeTag(tag)}
                    aria-label={`移除标签 ${tag}`}
                    className="text-primary/70 hover:text-danger"
                  >
                    ×
                  </button>
                </span>
              ))}
              <input
                value={tagInput}
                onChange={(event) => setTagInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    event.preventDefault();
                    addTag();
                  }
                }}
                placeholder="输入后回车添加"
                className="min-w-[120px] flex-1 rounded-full border border-border bg-white px-3 py-1.5 text-xs outline-none focus:border-primary"
              />
            </div>
          </div>

          <div className="rounded-2xl border border-primary/15 bg-primary-soft/50 p-4">
            <div className="mb-1 flex items-center gap-2 text-xs font-bold text-primary">
              <BrainCircuit size={15} />
              AI目标理解预览
            </div>
            <p className="text-sm leading-6 text-ink">{validation?.normalizedGoal ?? normalizedPreview}</p>
          </div>

          {validation && (
            <div className={`rounded-2xl border p-4 ${validation.isExecutable ? 'border-safe-500/25 bg-safe-50' : 'border-warning-500/25 bg-warning-50'}`}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-extrabold text-ink">目标可执行度 {validation.score} 分</p>
                  <p className="mt-1 text-xs text-subtext">{validation.source}</p>
                </div>
                <Badge variant={validation.isExecutable ? 'success' : 'warning'}>
                  {validation.isExecutable ? '可直接生成' : '建议优化'}
                </Badge>
              </div>
              <ul className="mt-3 space-y-1.5">
                {validation.suggestions.map((suggestion) => (
                  <li key={suggestion} className="flex gap-2 text-xs leading-5 text-ink">
                    <Lightbulb className="mt-0.5 shrink-0 text-amber-500" size={13} />
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex flex-col gap-2 sm:flex-row sm:justify-end">
            <Button variant="outline" onClick={validate} loading={loading}>
              <BrainCircuit size={16} />
              AI校验目标
            </Button>
            <Button variant="gradient" onClick={generate} loading={loading}>
              <Sparkles size={16} />
              生成个性化任务包
              <ArrowRight size={16} />
            </Button>
          </div>
        </section>

        <aside className="space-y-4">
          <div className="app-card p-4">
            <div className="mb-3 flex items-center gap-2">
              <BookOpenCheck className="text-primary" size={18} />
              <h2 className="text-sm font-extrabold text-ink">高频任务包模板</h2>
            </div>
            <div className="space-y-3">
              {templates.map((template) => (
                <button
                  key={template.id}
                  onClick={() => setDetailTemplate(template)}
                  className="w-full rounded-2xl border border-border bg-white p-3 text-left transition hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-card"
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-bold text-ink">{template.title}</p>
                    {template.featured && <Badge variant="info" size="sm">推荐</Badge>}
                  </div>
                  <p className="mt-1 line-clamp-2 text-[11px] leading-5 text-subtext">{template.summary}</p>
                  <div className="mt-2 flex items-center justify-between text-[10px] text-subtext">
                    <span>{template.periodDays}天 · {template.dailyMinutes}分钟/天</span>
                    <span className="inline-flex items-center gap-1 text-primary"><ListChecks size={11} />查看任务包配置</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-cyan-200 bg-gradient-to-br from-cyan-50 to-white p-4">
            <p className="text-xs font-extrabold text-cyan-800">平台定位</p>
            <p className="mt-2 text-xs leading-5 text-cyan-900/75">
              大学生 AI 主题学习与成果展示平台；宠物成长与活动解锁属于学习激励层。
            </p>
          </div>
        </aside>
      </div>

      {detailTemplate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4 backdrop-blur-sm">
          <div className="max-h-[88vh] w-full max-w-2xl overflow-y-auto rounded-3xl border border-white/60 bg-white p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-3">
              <div>
                <Badge variant="info">任务包配置</Badge>
                <h2 className="mt-2 text-lg font-extrabold text-ink">{detailTemplate.title}</h2>
                <p className="mt-1 text-xs text-subtext">
                  {detailTemplate.periodDays}天 · 每天{detailTemplate.dailyMinutes}分钟 · {detailTemplate.difficulty}难度
                </p>
              </div>
              <button
                onClick={() => setDetailTemplate(null)}
                aria-label="关闭"
                className="rounded-full p-1.5 text-subtext transition hover:bg-muted hover:text-ink"
              >
                <X size={18} />
              </button>
            </div>

            <p className="mt-3 text-sm leading-6 text-ink">{detailTemplate.summary}</p>

            {detailTemplate.outline?.length ? (
              <Section icon={<ListChecks size={15} className="text-primary" />} title="学习大纲">
                <ol className="list-decimal space-y-1 pl-5 text-xs leading-5 text-subtext">
                  {detailTemplate.outline.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ol>
              </Section>
            ) : null}

            {detailTemplate.keyDifficulties?.length ? (
              <Section icon={<Lightbulb size={15} className="text-amber-500" />} title="学习重难点">
                <ul className="space-y-1.5">
                  {detailTemplate.keyDifficulties.map((item, idx) => (
                    <li key={idx} className="flex gap-2 text-xs leading-5 text-subtext">
                      <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" />
                      {item}
                    </li>
                  ))}
                </ul>
              </Section>
            ) : null}

            {detailTemplate.referenceMaterials?.length ? (
              <Section icon={<BookOpenCheck size={15} className="text-primary" />} title="参考资料">
                <div className="space-y-2">
                  {detailTemplate.referenceMaterials.map((ref, idx) => (
                    <div key={idx} className="rounded-xl border border-border bg-white px-3 py-2">
                      <p className="text-xs font-bold text-ink">{ref.title}</p>
                      <p className="mt-0.5 text-[11px] leading-5 text-subtext">{ref.detail}</p>
                    </div>
                  ))}
                </div>
              </Section>
            ) : null}

            {detailTemplate.assessmentCriteria?.length ? (
              <Section icon={<Check size={15} className="text-safe-500" />} title="考核标准">
                <ul className="space-y-1.5">
                  {detailTemplate.assessmentCriteria.map((item, idx) => (
                    <li key={idx} className="flex gap-2 text-xs leading-5 text-subtext">
                      <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-safe-400" />
                      {item}
                    </li>
                  ))}
                </ul>
              </Section>
            ) : null}

            <div className="mt-5 flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setDetailTemplate(null)}>关闭</Button>
              <Button
                variant="gradient"
                onClick={() => {
                  applyTemplate(detailTemplate);
                  setDetailTemplate(null);
                }}
              >
                <Sparkles size={16} />套用此模板
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Section({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mt-4">
      <div className="mb-2 flex items-center gap-2 text-xs font-bold text-ink">
        {icon}
        {title}
      </div>
      {children}
    </section>
  );
}

