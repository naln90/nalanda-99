import { useState, useRef, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CheckCircle2, ChevronRight, FlaskConical, Loader2, Sparkles, XCircle } from 'lucide-react';
import { api, computeLevel } from '../api/client';
import { useAppStore } from '../store/useAppStore';
import type { AbilityDimension, AbilityProfile, AssessmentQuestion } from '../types';
import { useToast } from '../components/ui/Toast';

const DIMENSIONS: AbilityDimension[] = ['辨识力', '判断力', '应变力', '实证力', '协作力'];

type Phase = 'select' | 'loading' | 'quiz' | 'submitting';

const MODE_OPTIONS = [
  {
    mode: 'quick' as const,
    name: '快速测评',
    desc: '10题快速了解你的五大维度综合能力',
    icon: '⚡',
    questions: 10,
    recommended: true,
  },
  {
    mode: 'standard' as const,
    name: '标准测评',
    desc: '20题全面覆盖各类诈骗类型与风险阶段',
    icon: '🎯',
    questions: 20,
    recommended: false,
  },
];

export default function AssessmentPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const fromTaskId = searchParams.get('fromTask');
  const completeTaskItem = useAppStore((state) => state.completeTaskItem);
  const currentUser = useAppStore((state) => state.currentUser);
  const { success, error: showError } = useToast();
  const ownerId = currentUser?.ownerId || '';

  const [phase, setPhase] = useState<Phase>('select');
  const [sessionId, setSessionId] = useState<string>('');
  const [questions, setQuestions] = useState<AssessmentQuestion[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [selectedOptions, setSelectedOptions] = useState<number[]>([]);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackData, setFeedbackData] = useState<{
    isCorrect: boolean;
    explanation: string;
    correctAnswer: string | string[];
  } | null>(null);
  const [correctCount, setCorrectCount] = useState(0);
  const submittingRef = useRef(false);

  const handleSelectMode = useCallback(async (mode: 'quick' | 'standard') => {
    if (submittingRef.current) return;
    setPhase('loading');
    try {
      const result = await api.createAssessmentSession(ownerId, mode);
      // 题目不包含 correctAnswer（由服务端评定）
      const qs: AssessmentQuestion[] = result.questions.map((q: any) => ({
        id: q.id,
        questionType: q.questionType,
        fraudType: q.fraudType,
        abilityDim: q.abilityDim,
        riskStage: q.riskStage,
        stem: q.stem,
        options: q.options,
        // 客户端不感知正确答案
      }));
      setSessionId(result.sessionId);
      setQuestions(qs);
      setCurrentIdx(0);
      setCorrectCount(0);
      setSelectedOptions([]);
      setShowFeedback(false);
      setFeedbackData(null);
      setPhase('quiz');
    } catch (e) {
      showError(e instanceof Error ? e.message : '测评会话创建失败，请稍后重试');
      setPhase('select');
    }
  }, [showError, ownerId]);

  const currentQuestion = questions[currentIdx];

  const handleSelectOption = (idx: number) => {
    if (showFeedback) return;
    if (currentQuestion?.questionType === 'multiple') {
      setSelectedOptions((prev) =>
        prev.includes(idx) ? prev.filter((i) => i !== idx) : [...prev, idx].sort((a, b) => a - b)
      );
    } else {
      setSelectedOptions([idx]);
    }
  };

  const handleSubmitAnswer = async () => {
    if (selectedOptions.length === 0 || !currentQuestion || !sessionId || submittingRef.current) return;

    submittingRef.current = true;
    try {
      const isMultiple = currentQuestion.questionType === 'multiple';
      const letters = selectedOptions.map((idx) => String.fromCharCode(65 + idx));
      const answer = isMultiple ? letters : letters[0];
      const fb = await api.submitAssessmentAnswer(sessionId, currentQuestion.id, answer);

      setFeedbackData({
        isCorrect: fb.isCorrect,
        explanation: fb.explanation,
        correctAnswer: fb.correctAnswer,
      });
      if (fb.isCorrect) {
        setCorrectCount((c) => c + 1);
      }
      setShowFeedback(true);
    } catch (e) {
      showError(e instanceof Error ? e.message : '答案提交失败');
    } finally {
      submittingRef.current = false;
    }
  };

  const handleNext = async () => {
    if (!currentQuestion || !sessionId) return;

    if (currentIdx + 1 < questions.length) {
      setCurrentIdx(currentIdx + 1);
      setSelectedOptions([]);
      setShowFeedback(false);
      setFeedbackData(null);
    } else {
      // 最后一道题，完成会话
      setPhase('submitting');
      try {
        const result = await api.completeAssessmentSession(sessionId);

        // 构建 AbilityProfile
        const scores = result.abilityProfile?.scores ?? {};
        const dimensions = DIMENSIONS.map((dim) => ({
          dimension: dim,
          score: scores[dim] ?? 0,
          maxScore: 100,
          percentage: scores[dim] ?? 0,
        }));
        const overallScore = result.abilityProfile?.overallScore
          ?? Math.round(dimensions.reduce((s, d) => s + d.score, 0) / dimensions.length);
        const weakDimensions = (result.abilityProfile?.weakDimensions ?? []) as AbilityDimension[];
        const strongDimensions = DIMENSIONS.filter((d) => scores[d] >= 80);
        const abilityProfile: AbilityProfile = {
          dimensions,
          overallScore,
          weakDimensions,
          strongDimensions,
          level: computeLevel(overallScore),
        };

        // 同步写入 store（AssessmentResultPage 依赖 store.assessmentResult）
        useAppStore.setState({
          assessmentResult: {
            accuracy: result.accuracy,
            correctCount: result.correctCount,
            totalCount: result.totalCount,
            weakAreas: result.weakAreas ?? [],
            growthAwarded: result.growthAwarded,
            unlockedPetPool: result.unlockedPetPool ?? true,
            currentUser: result.currentUser ?? useAppStore.getState().currentUser!,
            abilityProfile,
          },
          abilityProfile,
        });

        if (fromTaskId) {
          await completeTaskItem(fromTaskId);
        }
        success(`测评完成！正确率 ${Math.round(result.accuracy * 100)}%，获得成长值 +${result.growthAwarded}`);
        navigate('/assessment-result');
      } catch (e) {
        showError(e instanceof Error ? e.message : '测评提交失败，请稍后重试');
        setPhase('quiz');
      }
    }
  };

  // ── Mode Selection ──
  if (phase === 'select') {
    return (
      <div className="max-w-2xl mx-auto mt-6 animate-slide-up">
        <div className="relative app-card p-8 overflow-hidden">
          <div className="absolute inset-0 bg-mesh opacity-70" />
          <div className="relative text-center mb-8">
            <div className="relative w-20 h-20 mx-auto mb-4">
              <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-primary to-primary-deep flex items-center justify-center shadow-glow">
                <FlaskConical size={34} className="text-white" />
              </div>
              <div className="absolute inset-0 w-20 h-20 rounded-3xl bg-primary/40 blur-xl animate-pulse-soft -z-10" />
            </div>
            <h2 className="text-2xl font-extrabold text-ink mb-2">首次综合能力测评</h2>
          </div>

          <div className="relative space-y-3">
            {MODE_OPTIONS.map((opt) => (
              <button
                key={opt.mode}
                onClick={() => handleSelectMode(opt.mode)}
                className={`w-full flex items-center justify-between px-6 py-5 rounded-2xl border-2 transition-all text-left group ${
                  opt.recommended
                    ? 'border-primary bg-primary-soft/50 hover:bg-primary-soft'
                    : 'border-slate-200 hover:border-primary/40 hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center gap-4">
                  <span className="text-2xl">{opt.icon}</span>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-ink text-lg">{opt.name}</span>
                      {opt.recommended && (
                        <span className="chip bg-gradient-to-r from-primary to-primary-deep text-white text-xs">推荐</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono text-subtext bg-slate-100 px-2 py-1 rounded-lg">{opt.questions}题</span>
                  <ChevronRight size={20} className="text-slate-400 group-hover:text-primary group-hover:translate-x-1 transition-all" />
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // ── Loading / Submitting ──
  if (phase === 'loading' || phase === 'submitting') {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] animate-fade-in">
        <Loader2 size={40} className="text-primary animate-spin mb-4" />
        <p className="text-subtext">
          {phase === 'loading' ? '正在生成个性化测评题目...' : '正在计算综合能力画像...'}
        </p>
      </div>
    );
  }

  if (!currentQuestion) return null;

  const progress = ((currentIdx + 1) / questions.length) * 100;

  return (
    <div className="max-w-3xl mx-auto animate-slide-up">
      {/* 进度条 */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-bold text-ink">
            第 {currentIdx + 1} / {questions.length} 题
          </span>
          <div className="flex items-center gap-2">
            <span className="text-xs text-subtext flex items-center gap-1">
              <Sparkles size={12} className="text-primary" /> {currentQuestion.fraudType}
            </span>
            {currentQuestion.abilityDim && (
              <span className="text-xs chip bg-slate-100 text-subtext">{currentQuestion.abilityDim}</span>
            )}
          </div>
        </div>
        <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
          <div
            className="h-2.5 rounded-full bg-gradient-to-r from-primary to-primary-deep transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="app-card p-8">
        {/* 题干 */}
        <div className="mb-6 pb-4 border-b border-slate-100">
          <div className="flex flex-wrap gap-2 mb-3">
            <span className="chip bg-primary-soft text-primary text-xs">
              {currentQuestion.questionType === 'single' ? '单选题' : '多选题'}
            </span>
            {currentQuestion.riskStage && (
              <span className="chip bg-amber-50 text-amber-700 text-xs">{currentQuestion.riskStage}</span>
            )}
          </div>
          <h3 className="text-lg font-medium text-ink leading-relaxed">{currentQuestion.stem}</h3>
        </div>

        {/* 选项 */}
        <div className="space-y-3 mb-6">
          {currentQuestion.options.map((opt, idx) => {
            const isSelected = selectedOptions.includes(idx);
            let style = 'border-slate-200 hover:border-primary/40 text-slate-700 hover:bg-slate-50';
            if (showFeedback && feedbackData) {
              const optionLetter = String.fromCharCode(65 + idx);
              // 服务端反馈返回了 correctAnswer，用它判断哪个选项是正确答案
              const isThisCorrect = Array.isArray(feedbackData.correctAnswer)
                ? feedbackData.correctAnswer.includes(optionLetter)
                : feedbackData.correctAnswer === optionLetter;
              if (isThisCorrect) {
                style = 'border-safe bg-emerald-50 text-safe font-medium';
              } else if (isSelected) {
                style = 'border-danger bg-rose-50 text-danger';
              } else {
                style = 'border-slate-200 text-subtext';
              }
            } else if (isSelected) {
              style = 'border-primary bg-primary-soft text-primary font-medium shadow-glow-sm';
            }
            return (
              <button
                key={idx}
                onClick={() => handleSelectOption(idx)}
                disabled={showFeedback}
                className={`w-full text-left px-5 py-3.5 rounded-xl border-2 transition-all flex items-center justify-between ${style}`}
              >
                <span>{opt}</span>
                {showFeedback && feedbackData && (() => {
                  const optLetter = String.fromCharCode(65 + idx);
                  const isThisCorrect = Array.isArray(feedbackData.correctAnswer)
                    ? feedbackData.correctAnswer.includes(optLetter)
                    : feedbackData.correctAnswer === optLetter;
                  if (isThisCorrect) {
                    return <CheckCircle2 size={20} className="text-safe flex-shrink-0" />;
                  }
                  if (isSelected) {
                    return <XCircle size={20} className="text-danger flex-shrink-0" />;
                  }
                  return null;
                })()}
              </button>
            );
          })}
        </div>

        {/* 服务端反馈 */}
        {showFeedback && feedbackData && (
          <div
            className={`rounded-xl p-4 mb-6 animate-fade-in ${
              feedbackData.isCorrect
                ? 'bg-emerald-50 border border-emerald-200'
                : 'bg-amber-50 border border-amber-200'
            }`}
          >
            <div className="flex items-start gap-3">
              {feedbackData.isCorrect ? (
                <CheckCircle2 size={20} className="text-safe flex-shrink-0 mt-0.5" />
              ) : (
                <XCircle size={20} className="text-warning flex-shrink-0 mt-0.5" />
              )}
              <div>
                <p className={`font-bold mb-1 ${feedbackData.isCorrect ? 'text-safe' : 'text-warning'}`}>
                  {feedbackData.isCorrect ? '回答正确！' : '回答有误'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-subtext">
            已答对 {correctCount}/{currentIdx + 1} 题
          </span>
          <div>
            {!showFeedback ? (
              <button
                disabled={selectedOptions.length === 0}
                onClick={handleSubmitAnswer}
                className="btn-primary px-8 py-2.5"
              >
                确认答案
              </button>
            ) : (
              <button onClick={handleNext} className="btn-primary px-8 py-2.5 flex items-center">
                {currentIdx + 1 < questions.length ? '下一题' : '查看测评结果'}
                <ChevronRight size={18} className="ml-1" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
