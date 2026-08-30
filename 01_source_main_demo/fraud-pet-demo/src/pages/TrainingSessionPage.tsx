import { useEffect, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { CheckCircle2, ChevronRight, Loader2, MessageSquare, XCircle } from 'lucide-react';
import { api } from '../api/client';
import type { TrainingQuestion, TrainingTaskDetail } from '../types';
import { useToast } from '../components/ui/Toast';

export default function TrainingSessionPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { error: showError } = useToast();
  const fromTask = (location.state as { fromTask?: string } | null)?.fromTask;

  const [taskDetail, setTaskDetail] = useState<TrainingTaskDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadFailed, setLoadFailed] = useState(false);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [selectedOptions, setSelectedOptions] = useState<Set<number>>(new Set());
  const [showFeedback, setShowFeedback] = useState(false);
  const [answers, setAnswers] = useState<Array<{ questionId: string; answer: string[] }>>([]);

  useEffect(() => {
    if (!id) return;
    void api.getTrainingTask(id).then((detail) => {
      setTaskDetail(detail);
      setLoading(false);
    }).catch((e) => {
      showError(e instanceof Error ? e.message : '训练任务加载失败');
      setLoadFailed(true);
      setLoading(false);
    });
  }, [id, showError]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] animate-fade-in">
        <Loader2 size={40} className="text-primary animate-spin mb-4" />
      </div>
    );
  }

  if (!taskDetail || taskDetail.questions.length === 0 || loadFailed) {
    return (
      <div className="flex flex-col items-center justify-center h-[40vh] animate-fade-in text-center">
        <XCircle size={40} className="text-danger mb-3" />
        <p className="text-ink font-medium mb-1">训练任务加载失败</p>
        <button onClick={() => navigate('/training')} className="btn-primary px-6 py-2.5">返回训练中心</button>
      </div>
    );
  }

  const currentQuestion = taskDetail.questions[currentIdx];
  const isMultiple = currentQuestion.questionType === 'multiple';

  const getOptionLetter = (idx: number) => String.fromCharCode(65 + idx);

  const isOptionCorrect = (q: TrainingQuestion, optionIdx: number): boolean => {
    const letter = getOptionLetter(optionIdx);
    if (Array.isArray(q.correctAnswer)) {
      return q.correctAnswer.includes(letter);
    }
    return q.correctAnswer === letter;
  };

  const isAnswerCorrect = (): boolean => {
    if (selectedOptions.size === 0) return false;
    const selectedLetters = Array.from(selectedOptions).map(getOptionLetter).sort();
    const correctLetters = Array.isArray(currentQuestion.correctAnswer)
      ? [...currentQuestion.correctAnswer].sort()
      : [currentQuestion.correctAnswer];
    return JSON.stringify(selectedLetters) === JSON.stringify(correctLetters);
  };

  const handleToggleOption = (idx: number) => {
    if (showFeedback) return;
    setSelectedOptions((prev) => {
      const next = new Set(prev);
      if (isMultiple) {
        if (next.has(idx)) next.delete(idx);
        else next.add(idx);
      } else {
        next.clear();
        next.add(idx);
      }
      return next;
    });
  };

  const handleSubmitAnswer = () => {
    if (selectedOptions.size === 0) return;
    setShowFeedback(true);
  };

  const handleNext = () => {
    const selectedLetters = Array.from(selectedOptions).map(getOptionLetter);
    const newAnswers = [...answers, { questionId: currentQuestion.id, answer: selectedLetters }];
    setAnswers(newAnswers);

    if (currentIdx + 1 < taskDetail.questions.length) {
      setCurrentIdx(currentIdx + 1);
      setSelectedOptions(new Set());
      setShowFeedback(false);
    } else {
      navigate(`/training/settlement/${id}`, { state: { answers: newAnswers, fromTask } });
    }
  };

  const correct = isAnswerCorrect();
  const progress = ((currentIdx + 1) / taskDetail.questions.length) * 100;
  const task = taskDetail.task;

  return (
    <div className="space-y-5 animate-slide-up">
      {/* 进度条 */}
      <div>
        <div className="flex justify-between items-center mb-2">
          <div>
            <h2 className="text-lg font-extrabold text-ink">{task.title}</h2>
          </div>
          <span className="text-sm font-bold text-ink">第 {currentIdx + 1} / {taskDetail.questions.length} 题</span>
        </div>
        <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
          <div className="h-2.5 rounded-full bg-gradient-to-r from-primary to-primary-deep transition-all duration-500" style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="flex gap-5 flex-col lg:flex-row">
        {/* 情景对话区 */}
        <div className="lg:w-[340px] flex-shrink-0 rounded-2xl overflow-hidden flex flex-col border border-slate-200 shadow-card" style={{ minHeight: '420px' }}>
          <div className="bg-gradient-to-r from-[#1A2240] to-[#0B1228] text-white py-3 px-4 text-sm font-semibold flex items-center gap-2">
            <MessageSquare size={16} className="text-cyan-300" />
            {taskDetail.scenario.title}
          </div>
          <div
            className="flex-1 p-4 space-y-4 overflow-y-auto scrollbar-thin"
            style={{ background: 'linear-gradient(180deg,#F1F5F9 0%,#E2E8F0 100%)' }}
          >
            {taskDetail.scenario.messages.map((msg, idx) => {
              const isScam = msg.speaker === '可疑联系人';
              const isSystem = msg.speaker === '系统提示';
              const avatar = isScam ? '⚠️' : isSystem ? 'ℹ️' : '🛡️';
              const avatarBg = isScam ? 'bg-rose-100' : isSystem ? 'bg-sky-100' : 'bg-emerald-100';
              return (
                <div key={idx} className="flex gap-3 animate-fade-in" style={{ animationDelay: `${idx * 100}ms` }}>
                  <div className={`w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center text-sm shadow-sm ${avatarBg}`}>
                    {avatar}
                  </div>
                  <div>
                    <p className="text-[10px] text-subtext mb-1 ml-1">{msg.speaker}</p>
                    <div className="bg-white p-3 rounded-2xl rounded-tl-none text-sm text-ink shadow-sm border border-slate-100 max-w-[260px]">
                      {msg.content}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 答题区 */}
        <div className="flex-1 app-card p-6 flex flex-col">
          <div className="mb-5 pb-4 border-b border-slate-100">
            <span className="chip bg-primary-soft text-primary mb-2">
              {isMultiple ? '多选题' : '单选题'}
            </span>
            <h3 className="text-base font-medium text-ink leading-relaxed">{currentQuestion.stem}</h3>
          </div>

          <div className="space-y-3 mb-5 flex-1">
            {currentQuestion.options.map((opt, idx) => {
              const isSelected = selectedOptions.has(idx);
              const isThisCorrect = isOptionCorrect(currentQuestion, idx);
              let style = 'border-slate-200 hover:border-primary/40 text-slate-700 hover:bg-slate-50';
              if (showFeedback) {
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
                  onClick={() => handleToggleOption(idx)}
                  disabled={showFeedback}
                  className={`w-full text-left px-4 py-3 rounded-xl border-2 transition-all flex items-center justify-between ${style}`}
                >
                  <span>{opt}</span>
                  {showFeedback && isThisCorrect && <CheckCircle2 size={18} className="text-safe flex-shrink-0" />}
                  {showFeedback && isSelected && !isThisCorrect && <XCircle size={18} className="text-danger flex-shrink-0" />}
                </button>
              );
            })}
          </div>

          {/* 即时反馈 */}
          {showFeedback && (
            <div className={`rounded-xl p-4 mb-4 animate-fade-in ${correct ? 'bg-emerald-50 border border-emerald-200' : 'bg-amber-50 border border-amber-200'}`}>
              <div className="flex items-start gap-3">
                {correct ? <CheckCircle2 size={18} className="text-safe flex-shrink-0 mt-0.5" /> : <XCircle size={18} className="text-warning flex-shrink-0 mt-0.5" />}
                <div>
                  <p className={`font-bold mb-1 text-sm ${correct ? 'text-safe' : 'text-warning'}`}>{correct ? '回答正确！' : '回答有误，注意以下风险信号'}</p>
                </div>
              </div>
            </div>
          )}

          {/* 底部操作 */}
          <div className="flex items-center justify-between pt-4 border-t border-slate-50">
            <span className="text-xs text-subtext">预计成长值 <span className="font-bold text-growth">+{task.reward}</span></span>
            {!showFeedback ? (
              <button disabled={selectedOptions.size === 0} onClick={handleSubmitAnswer} className="btn-primary px-6 py-2">
                确认答案
              </button>
            ) : (
              <button onClick={handleNext} className="btn-primary px-6 py-2 flex items-center">
                {currentIdx + 1 < taskDetail.questions.length ? '下一题' : '完成训练'}
                <ChevronRight size={16} className="ml-1" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
