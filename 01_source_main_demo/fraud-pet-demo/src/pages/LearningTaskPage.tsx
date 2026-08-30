import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle2,
  Loader2,
  MessageCircle,
  PenLine,
  Send,
  Sparkles,
  Zap,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { useToast } from '../components/ui/Toast';
import { api } from '../api/client';
import type { LearningPlanItem } from '../types/learning';
import { resolveThemeProfile, getQuizPool } from '../lib/themeProfile';

/** 任务类型推断：综合标题、描述、验收标准，把学习任务条目映射到可执行交互 */
function inferTaskMode(item: LearningPlanItem): 'micro-course' | 'quiz' | 'risk-signal' | 'chat-sim' | 'reflection' | 'outcome' {
  const t = item.title || '';
  const d = item.description || '';
  const a = item.acceptanceCriteria || '';
  const text = `${t} ${d} ${a}`;

  // 成果类：最明确，优先判断
  if (item.category === 'outcome' || /成果|海报|创作|提示卡|迭代|产出|作品/.test(text)) return 'outcome';

  // 答题类：选择/判断/竞赛/题组/正确率/答题
  if (/答题|选择题|判断题|情境题|竞赛|测验|题组|题目|正确率|答对|不少于.*题|完成.*题/.test(text)) return 'quiz';

  // 复盘类
  if (/复盘|总结|反思|心得|笔记/.test(text)) return 'reflection';

  // 风险信号识别类
  if (/风险|信号|话术|找茬|标注|高危|案例.*找出|找出.*信号/.test(text)) return 'risk-signal';

  // AI 模拟对话类
  if (/模拟.*对话|对话.*模拟|模拟.*客服|模拟.*骗子|关键.*判断/.test(text)) return 'chat-sim';

  // 兜底：不再安排视频观看类任务，统一以自测答题承接知识导入类任务
  return 'quiz';
}

const CATEGORY_LABEL: Record<string, string> = {
  required: '基础必修',
  elective: '兴趣选修',
  outcome: '成果任务',
};

const MAX_DAILY_ATTEMPTS = 3;

function attemptKey(ownerId: string, itemId: string) {
  return `fzzy.task-attempts.${ownerId}.${itemId}`;
}

interface AttemptState {
  date: string; // YYYY-MM-DD
  used: number;
}

function getTodayStr() {
  return new Date().toISOString().slice(0, 10);
}

function loadAttempts(ownerId: string, itemId: string): AttemptState {
  if (!ownerId || !itemId) return { date: getTodayStr(), used: 0 };
  try {
    const raw = localStorage.getItem(attemptKey(ownerId, itemId));
    if (raw) {
      const data = JSON.parse(raw) as AttemptState;
      if (data.date === getTodayStr()) return data;
    }
  } catch {
    // ignore
  }
  return { date: getTodayStr(), used: 0 };
}

function saveAttempts(ownerId: string, itemId: string, state: AttemptState) {
  if (!ownerId || !itemId) return;
  try {
    localStorage.setItem(attemptKey(ownerId, itemId), JSON.stringify(state));
  } catch {
    // ignore
  }
}

/** 根据任务信息生成题库，并解析题目数量、通过率要求 */
function buildQuiz(item: LearningPlanItem, planTitle: string) {
  const criteria = `${item.title} ${item.description} ${item.acceptanceCriteria}`;

  // 解析题目数量（默认 5，接受“不少于 N 题”）
  const countMatch = criteria.match(/不少于\s*(\d+)\s*题|完成\s*(\d+)\s*道|完成.*?(\d+)\s*题/);
  const targetCount = Math.min(Math.max(parseInt(countMatch?.[1] || countMatch?.[2] || countMatch?.[3] || '5', 10), 3), 10);

  // 解析通过率（默认 60%）
  const rateMatch = criteria.match(/正确率\s*[≥>=]\s*(\d+)%/);
  const passRate = rateMatch ? parseInt(rateMatch[1], 10) / 100 : 0.6;

  // 题库随主题切换：反诈主题用反诈题库；Python/编程主题用 Python 基础题库；
  // 其它主题用中性学习自测题库。非反诈主题绝不会出现“诈骗/刷单”相关内容。
  const pool = getQuizPool(resolveThemeProfile(planTitle), planTitle);

  const questions = pool.slice(0, targetCount);
  return { questions, passRate };
}

/** 风险信号识别任务 */
function buildRiskSignal(planTitle: string) {
  const base = planTitle.replace(/主题|学习|任务/g, '') || '刷单诈骗';
  return {
    caseText: `小李在群里看到一则兼职广告：“${base}，每单返 20-50 元，无需经验，手机即可操作”。他加了对方好友，对方发来一个商品链接，说“先垫付 299 元购买，完成后连本带利返 350 元”。小李付款后，对方又以“连单任务”“系统卡单”为由让他继续垫付。`,
    signals: [
      { id: 's1', label: '高收益、零门槛兼职', selected: false },
      { id: 's2', label: '要求先垫付资金', selected: false },
      { id: 's3', label: '以“连单/卡单”要求继续转账', selected: false },
      { id: 's4', label: '陌生链接或二维码', selected: false },
      { id: 's5', label: '索要验证码', selected: false },
    ],
    expectedIds: ['s1', 's2', 's3'],
  };
}

/** AI 模拟对话任务 */
function buildChatSim(planTitle: string) {
  const base = planTitle.replace(/主题|学习|任务/g, '') || '兼职刷单';
  return {
    messages: [
      { role: 'other', text: `你好，我是“校园兼职中心”客服，我们这边有${base}的兼职，每单 20-50 元，你有兴趣吗？` },
      { role: 'other', text: '操作很简单，你先垫付 299 元完成一单，我马上返你 350 元。' },
    ],
    choices: [
      { id: 'c1', text: '先垫付 299 元试试', correct: false, feedback: '这是典型的先垫付骗局，资金一旦转出很难追回。' },
      { id: 'c2', text: '拒绝并要求对方提供官方资质', correct: false, feedback: '拒绝是对的，但没必要继续纠缠，直接终止对话更安全。' },
      { id: 'c3', text: '终止对话并向学校或平台举报', correct: true, feedback: '正确。任何要求先垫付的兼职都应直接终止并举报。' },
    ],
  };
}

export default function LearningTaskPage() {
  const { itemId } = useParams<{ itemId: string }>();
  const navigate = useNavigate();
  const { success } = useToast();

  const currentUser = useAppStore((s) => s.currentUser);
  const ownerId = currentUser?.ownerId ?? '';

  const [dashboard, setDashboard] = useState<{ plan: { title: string; items: LearningPlanItem[] } } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [energyReward, setEnergyReward] = useState(10);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadNonce, setReloadNonce] = useState(0);

  useEffect(() => {
    if (!ownerId) return;
    let cancelled = false;
    setIsLoading(true);
    api.getLearningDashboard(ownerId)
      .then((data) => {
        if (!cancelled) {
          setDashboard(data as { plan: { title: string; items: LearningPlanItem[] } });
          useAppStore.getState().setActiveLearningTheme(data.goal?.theme ?? data.plan?.title ?? null);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setDashboard(null);
          setLoadError('任务数据加载失败，请检查网络后重试');
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => { cancelled = true; };
  }, [ownerId, reloadNonce]);

  const item = useMemo(() => {
    return dashboard?.plan?.items?.find((i) => i.id === itemId) ?? null;
  }, [dashboard, itemId]);

  const planTitle = dashboard?.plan?.title ?? '学习任务包';
  const mode = useMemo(() => (item ? inferTaskMode(item) : 'quiz'), [item]);
  const isDone = item?.status === 'completed';

  // ===== 每日答题次数限制（风险信号 / 答题挑战） =====
  const [attempts, setAttempts] = useState<AttemptState>(() => loadAttempts(ownerId, itemId || ''));
  useEffect(() => {
    setAttempts(loadAttempts(ownerId, itemId || ''));
  }, [ownerId, itemId]);
  useEffect(() => {
    // 跨天自动重置
    const id = setInterval(() => {
      setAttempts(loadAttempts(ownerId, itemId || ''));
    }, 60000);
    return () => clearInterval(id);
  }, [ownerId, itemId]);
  const attemptsLeft = Math.max(0, MAX_DAILY_ATTEMPTS - attempts.used);
  const attemptsExhausted = attemptsLeft <= 0 && !isDone;
  const consumeAttempt = () => {
    const next = { date: getTodayStr(), used: attempts.used + 1 };
    setAttempts(next);
    saveAttempts(ownerId, itemId || '', next);
  };

  // ===== 答题状态 =====
  const quiz = useMemo(() => (item ? buildQuiz(item, planTitle) : null), [item, planTitle]);
  const [answers, setAnswers] = useState<Record<string, number | null>>({});
  const [quizSubmitted, setQuizSubmitted] = useState(false);

  // ===== 风险信号状态 =====
  const risk = useMemo(() => (item ? buildRiskSignal(planTitle) : null), [planTitle]);
  const [riskSignals, setRiskSignals] = useState<{ id: string; label: string; selected: boolean }[]>([]);
  const [riskSubmitted, setRiskSubmitted] = useState(false);
  useEffect(() => {
    if (risk) setRiskSignals(risk.signals);
  }, [risk]);

  // ===== 模拟对话状态 =====
  const chat = useMemo(() => (item ? buildChatSim(planTitle) : null), [planTitle]);
  const [chatChoice, setChatChoice] = useState<string | null>(null);
  const [chatRevealed, setChatRevealed] = useState(false);

  // ===== 复盘状态 =====
  const [reflection, setReflection] = useState('');
  const [reflectionSubmitted, setReflectionSubmitted] = useState(false);

  // ===== 成果状态 =====
  const [outcomeText, setOutcomeText] = useState('');
  const [outcomeSubmitted, setOutcomeSubmitted] = useState(false);

  const handleComplete = async () => {
    if (!item || !ownerId || isDone) return;
    try {
      const result = await api.completeLearningPlanItem(item.id, ownerId, '在学习任务包中完成并记录');
      if (result.awarded > 0) setEnergyReward(result.awarded);
      success(`任务完成，+${result.awarded} 盾能`);
      // 刷新本地任务状态
      const data = await api.getLearningDashboard(ownerId);
      setDashboard(data as { plan: { title: string; items: LearningPlanItem[] } });
      useAppStore.getState().setActiveLearningTheme(data.goal?.theme ?? data.plan?.title ?? null);
    } catch (err) {
      // ignore
    }
  };

  const canComplete = (() => {
    if (isDone) return false;
    switch (mode) {
      case 'quiz': {
        if (!quiz) return false;
        const answered = Object.values(answers).filter((v) => v !== null).length;
        if (answered < quiz.questions.length) return false;
        if (!quizSubmitted) return false;
        const correct = quiz.questions.filter((q) => answers[q.id] === q.correct).length;
        return correct / quiz.questions.length >= quiz.passRate;
      }
      case 'risk-signal': {
        if (!risk) return false;
        if (!riskSubmitted) return false;
        const selectedIds = riskSignals.filter((s) => s.selected).map((s) => s.id).sort();
        return JSON.stringify(selectedIds) === JSON.stringify(risk.expectedIds.slice().sort());
      }
      case 'chat-sim': {
        if (!chat || !chatRevealed) return false;
        const choice = chat.choices.find((c) => c.id === chatChoice);
        return choice?.correct ?? false;
      }
      case 'reflection':
        return reflectionSubmitted && reflection.trim().length >= 10;
      case 'outcome':
        return outcomeSubmitted && outcomeText.trim().length >= 10;
      default:
        return false;
    }
  })();

  // 各任务类型达成完成条件后自动领取盾能（内容驱动，而非手动勾选）
  useEffect(() => {
    if (isDone || !item || !ownerId || isLoading) return;
    if (canComplete) {
      const id = setTimeout(() => {
        handleComplete();
      }, 600);
      return () => clearTimeout(id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canComplete, isDone, item, ownerId, isLoading]);

  if (loadError) {
    return (
      <div className="py-20 text-center text-subtext space-y-4">
        <p>任务数据加载失败：{loadError}</p>
        <Button
          variant="ghost"
          className="mt-4"
          onClick={() => {
            setLoadError(null);
            setReloadNonce((n) => n + 1);
          }}
        >
          <ArrowLeft size={16} /> 重试
        </Button>
      </div>
    );
  }

  if (!item) {
    return (
      <div className="py-20 text-center text-subtext">
        <p>任务不存在或尚未加入学习任务包</p>
        <Button variant="ghost" className="mt-4" onClick={() => navigate('/learning/workspace')}>
          <ArrowLeft size={16} /> 返回学习任务包
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4 max-w-3xl mx-auto">
      {/* 顶部导航 */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate('/learning/workspace')} className="gap-1 px-2">
          <ArrowLeft size={16} /> 返回
        </Button>
        <div className="flex-1 min-w-0">
          <h1 className="text-base font-extrabold text-ink truncate">{item.title}</h1>
          <p className="text-[11px] text-subtext truncate">{planTitle}</p>
        </div>
        <Badge variant={item.category === 'required' ? 'default' : item.category === 'elective' ? 'info' : 'warning'}>
          {CATEGORY_LABEL[item.category]}
        </Badge>
      </div>

      {/* 任务信息卡 */}
      <Card variant="elevated">
        <CardContent className="space-y-2">
          <div className="flex items-center justify-between text-[11px] text-subtext">
            <span>预计 {item.estimatedMinutes} 分钟</span>
            <Badge variant="default" className="gap-0.5">
              <Zap size={10} />+{energyReward} 盾能
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* 答题 */}
      {mode === 'quiz' && quiz && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <PenLine size={18} className="text-primary" />
              答题挑战
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            {quiz.questions.map((q, idx) => {
              const chosen = answers[q.id];
              const showResult = quizSubmitted;
              return (
                <div key={q.id} className="space-y-2">
                  <p className="text-sm font-semibold text-ink">{idx + 1}. {q.stem}</p>
                  <div className="space-y-1.5">
                    {q.options.map((opt, optIdx) => {
                      const isCorrect = optIdx === q.correct;
                      const isChosen = chosen === optIdx;
                      let btnClass = 'w-full justify-start text-left border ';
                      if (showResult) {
                        if (isCorrect) btnClass += 'bg-safe-50 border-safe-500 text-safe-700';
                        else if (isChosen) btnClass += 'bg-danger-50 border-danger-500 text-danger-700';
                        else btnClass += 'border-border text-subtext';
                      } else {
                        btnClass += isChosen ? 'border-primary bg-primary/5 text-ink' : 'border-border text-ink hover:border-primary/40';
                      }
                      return (
                        <Button
                          key={optIdx}
                          variant="outline"
                          size="sm"
                          disabled={quizSubmitted}
                          onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: optIdx }))}
                          className={btnClass}
                        >
                          {opt}
                        </Button>
                      );
                    })}
                  </div>
                  {showResult && chosen !== q.correct && (
                    <p className="text-xs text-danger-600">{q.signal}</p>
                  )}
                </div>
              );
            })}
            {attemptsExhausted && !quizSubmitted && (
              <div className="rounded-lg border border-danger-200 bg-danger-50 p-3 text-center">
                <p className="text-sm font-semibold text-danger-700">今日答题次数已用完</p>
                <p className="text-xs text-danger-600 mt-1">请明日再来挑战，继续巩固知识</p>
              </div>
            )}
            {!quizSubmitted ? (
              <Button
                variant="default"
                onClick={() => {
                  if (attemptsExhausted) return;
                  consumeAttempt();
                  setQuizSubmitted(true);
                }}
                disabled={
                  attemptsExhausted ||
                  Object.values(answers).filter((v) => v !== null).length < quiz.questions.length
                }
                fullWidth
              >
                提交答案（消耗 1 次机会）
              </Button>
            ) : (
              <div className="text-center space-y-3">
                <p className="text-sm font-semibold text-ink">
                  正确 {quiz.questions.filter((q) => answers[q.id] === q.correct).length}/{quiz.questions.length}
                </p>
                {(() => {
                  const correct = quiz.questions.filter((q) => answers[q.id] === q.correct).length;
                  const passed = correct / quiz.questions.length >= quiz.passRate;
                  if (passed) {
                    return <p className="text-xs text-safe-600">已通过，正在发放盾能…</p>;
                  }
                  return (
                    <div className="space-y-2">
                      <p className="text-xs text-danger-600">未达通过标准，{attemptsLeft > 0 ? '可修改答案后重试' : '今日机会已用完'}</p>
                      {attemptsLeft > 0 && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setQuizSubmitted(false)}
                        >
                          重新作答（剩余 {attemptsLeft} 次）
                        </Button>
                      )}
                    </div>
                  );
                })()}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 风险信号识别 */}
      {mode === 'risk-signal' && risk && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <CheckCircle2 size={18} className="text-primary" />
              风险信号识别
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-sm text-ink leading-relaxed bg-muted/50 rounded-lg p-4">{risk.caseText}</div>
            <div className="space-y-2">
              {riskSignals.map((s) => (
                <label
                  key={s.id}
                  className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                    s.selected ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/40'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={s.selected}
                    onChange={() =>
                      setRiskSignals((prev) => prev.map((x) => (x.id === s.id ? { ...x, selected: !x.selected } : x)))
                    }
                    disabled={riskSubmitted}
                    className="rounded border-border text-primary focus:ring-primary"
                  />
                  <span className="text-sm text-ink">{s.label}</span>
                </label>
              ))}
            </div>
            {attemptsExhausted && !riskSubmitted && (
              <div className="rounded-lg border border-danger-200 bg-danger-50 p-3 text-center">
                <p className="text-sm font-semibold text-danger-700">今日答题次数已用完</p>
                <p className="text-xs text-danger-600 mt-1">请明日再来挑战，继续巩固风险识别能力</p>
              </div>
            )}
            {!riskSubmitted ? (
              <Button
                variant="default"
                onClick={() => {
                  if (attemptsExhausted) return;
                  consumeAttempt();
                  setRiskSubmitted(true);
                }}
                disabled={attemptsExhausted}
                fullWidth
              >
                提交判断（消耗 1 次机会）
              </Button>
            ) : (
              <div className="text-center space-y-3">
                {(() => {
                  const selectedIds = riskSignals.filter((s) => s.selected).map((s) => s.id).sort();
                  const expectedIds = risk.expectedIds.slice().sort();
                  const ok = JSON.stringify(selectedIds) === JSON.stringify(expectedIds);
                  if (ok) {
                    return <p className="text-sm text-safe-600 font-semibold">风险信号判断正确，正在发放盾能…</p>;
                  }
                  return (
                    <div className="space-y-2">
                      <p className="text-sm text-danger-600 font-semibold">判断有误</p>
                      <p className="text-xs text-subtext">
                        关键风险信号：{risk.signals.filter((s) => risk.expectedIds.includes(s.id)).map((s) => s.label).join('、')}
                      </p>
                      {attemptsLeft > 0 ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setRiskSubmitted(false)}
                        >
                          重新判断（剩余 {attemptsLeft} 次）
                        </Button>
                      ) : (
                        <p className="text-xs text-danger-600">今日机会已用完，请明日继续</p>
                      )}
                    </div>
                  );
                })()}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* AI 模拟对话 */}
      {mode === 'chat-sim' && chat && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <MessageCircle size={18} className="text-primary" />
              AI 模拟对话
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              {chat.messages.map((m, idx) => (
                <div key={idx} className={`flex ${m.role === 'other' ? '' : 'justify-end'}`}>
                  <div className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm ${m.role === 'other' ? 'bg-muted text-ink rounded-tl-none' : 'bg-primary text-white rounded-tr-none'}`}>
                    {m.text}
                  </div>
                </div>
              ))}
            </div>
            {!chatRevealed ? (
              <div className="space-y-2">
                {chat.choices.map((c) => (
                  <Button
                    key={c.id}
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setChatChoice(c.id);
                      setChatRevealed(true);
                    }}
                    className="w-full justify-start text-left"
                  >
                    {c.text}
                  </Button>
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                {chat.choices
                  .filter((c) => c.id === chatChoice)
                  .map((c) => (
                    <div
                      key={c.id}
                      className={`rounded-lg p-3 text-sm ${c.correct ? 'bg-safe-50 text-safe-700' : 'bg-danger-50 text-danger-700'}`}
                    >
                      <p className="font-semibold mb-1">{c.correct ? '判断正确' : '判断有误'}</p>
                      <p>{c.feedback}</p>
                    </div>
                  ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 复盘 */}
      {mode === 'reflection' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <PenLine size={18} className="text-primary" />
              主题复盘
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <textarea
              value={reflection}
              onChange={(e) => setReflection(e.target.value)}
              disabled={reflectionSubmitted}
              placeholder="写下你的反思..."
              rows={6}
              className="w-full rounded-lg border border-input bg-transparent px-3 py-2 text-sm text-ink placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/30"
            />
            {!reflectionSubmitted ? (
              <Button variant="default" onClick={() => setReflectionSubmitted(true)} disabled={reflection.trim().length < 10} fullWidth>
                <Send size={14} /> 提交复盘
              </Button>
            ) : (
              <p className="text-sm text-safe-600 font-semibold text-center">复盘已提交</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* 成果 */}
      {mode === 'outcome' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles size={18} className="text-primary" />
              成果创作
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <textarea
              value={outcomeText}
              onChange={(e) => setOutcomeText(e.target.value)}
              disabled={outcomeSubmitted}
              placeholder="在此粘贴成果内容、创作说明或学习收获..."
              rows={6}
              className="w-full rounded-lg border border-input bg-transparent px-3 py-2 text-sm text-ink placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/30"
            />
            {!outcomeSubmitted ? (
              <Button variant="default" onClick={() => setOutcomeSubmitted(true)} disabled={outcomeText.trim().length < 10} fullWidth>
                提交成果
              </Button>
            ) : (
              <p className="text-sm text-safe-600 font-semibold text-center">成果已提交，AI 初审通过</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* 底部状态栏：内容驱动，自动完成 */}
      <div className="sticky bottom-4 bg-background/95 backdrop-blur rounded-2xl border border-border p-3 shadow-lg">
        {isDone ? (
          <div className="space-y-2">
            <div className="flex items-center justify-center gap-2 text-sm text-safe-600 font-semibold">
              <CheckCircle2 size={16} /> 已完成，+{energyReward} 盾能
            </div>
            <Button variant="outline" size="sm" onClick={() => navigate('/learning/workspace')} fullWidth>
              返回学习任务包
            </Button>
          </div>
        ) : canComplete ? (
          <div className="flex items-center justify-center gap-2 text-sm text-primary font-semibold">
            <Loader2 size={16} className="animate-spin" /> 任务内容已完成，正在发放盾能…
          </div>
        ) : (
          <Button variant="gradient" size="lg" disabled fullWidth>
            <Zap size={16} />
            完成任务，+{energyReward} 盾能
          </Button>
        )}
      </div>
    </div>
  );
}
