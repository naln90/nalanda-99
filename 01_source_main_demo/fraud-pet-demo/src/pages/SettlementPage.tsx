import { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { ArrowRight, Award, Loader2, PartyPopper, Sparkles, TrendingUp, XCircle } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { trainingTasks } from '../data/mockData';
import { useToast } from '../components/ui/Toast';
import { Confetti, CountUp } from '../components/effects';
import type { TrainingSubmitResponse } from '../api/client';

export default function SettlementPage() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { pet, submitTraining, completeTaskItem, trainingTasks: storeTasks } = useAppStore();
  const { error: showError } = useToast();
  const [settled, setSettled] = useState(false);
  const [noRecord, setNoRecord] = useState(false);
  const [submitFailed, setSubmitFailed] = useState(false);
  const [showConfetti, setShowConfetti] = useState(false);
  const submittedRef = useRef(false);

  const locationState = location.state as { answers?: Array<{ questionId: string; answer: string[] }>; fromTask?: string } | null;
  const answers = useMemo(() => locationState?.answers ?? [], [locationState?.answers]);
  const fromTaskId = locationState?.fromTask;

  const allTasks = storeTasks.length > 0 ? storeTasks : trainingTasks;
  const taskTitle = allTasks.find((t) => t.id === id)?.title || '训练任务';
  const taskObj = allTasks.find((t) => t.id === id);

  const [result, setResult] = useState<TrainingSubmitResponse | null>(null);

  useEffect(() => {
    if (!submittedRef.current && id && pet && answers.length > 0) {
      submittedRef.current = true;
      void submitTraining(id, answers).then(async (res) => {
        if (res) {
          setResult(res);
          // 结算成功且获得成长值时触发撒花
          if ((res.growth.finalGrowth ?? 0) > 0) setShowConfetti(true);
          // 如果来自任务包，标记任务包项完成
          if (fromTaskId) {
            await completeTaskItem(fromTaskId);
          }
        }
        setSettled(true);
      }).catch(() => {
        setSubmitFailed(true);
        showError('训练结算提交失败，请稍后重试');
        setSettled(true);
      });
    } else if (!submittedRef.current && id) {
      // 无宠物或无答案时，直接标记完成
      submittedRef.current = true;
      // 直接链接进入或刷新页面会丢失 location.state，给出友好恢复提示而非虚假「完成」
      if (!locationState) {
        setNoRecord(true);
      }
      setSettled(true);
    }
  }, [id, pet, answers, submitTraining, showError, fromTaskId, completeTaskItem]);

  if (!settled) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] animate-fade-in">
        <Loader2 size={40} className="text-primary animate-spin mb-4" />
      </div>
    );
  }

  if (noRecord) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh] animate-fade-in text-center">
        <XCircle size={40} className="text-subtext mb-3" />
        <p className="text-ink font-medium mb-1">未找到本次训练记录</p>
        <p className="text-sm text-subtext mb-4">页面刷新或直接从链接进入时，训练结果不会保留，请重新进入训练任务</p>
        <button onClick={() => navigate(`/training/session/${id}`)} className="btn-primary px-6 py-2.5">重新进入训练</button>
      </div>
    );
  }

  if (submitFailed || (!result && !pet)) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh] animate-fade-in text-center">
        <XCircle size={40} className="text-danger mb-3" />
        <p className="text-ink font-medium mb-1">训练提交失败</p>
        <p className="text-sm text-subtext mb-4">结算时出现错误，请返回训练中心重试</p>
        <button onClick={() => navigate('/training')} className="btn-primary px-6 py-2.5">返回训练中心</button>
      </div>
    );
  }

  const growth = result?.growth.finalGrowth ?? 0;
  const accuracy = result?.accuracy ?? 0;
  const score = result?.score ?? 0;
  const rewardMessage = result?.rewardMessage ?? '';
  const currentPet = result?.pet ?? pet;
  const progress = currentPet ? Math.min((currentPet.growthValue / currentPet.nextLevelValue) * 100, 100) : 0;

  return (
    <div className="max-w-2xl mx-auto mt-6">
      <Confetti active={showConfetti} count={50} duration={4500} onComplete={() => setShowConfetti(false)} />
      <div className="relative app-card p-10 text-center overflow-hidden animate-pop">
        <div className="absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r from-primary via-violet-500 to-safe" />
        <div className="absolute inset-0 bg-mesh opacity-60" />

        {/* 庆祝图标 */}
        <div className="relative w-20 h-20 mx-auto mb-5">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-emerald-50 to-emerald-100 flex items-center justify-center border-2 border-emerald-100">
            <Award size={40} className="text-growth" />
          </div>
          <div className="absolute inset-0 w-20 h-20 rounded-full bg-emerald-400/30 blur-xl animate-pulse-soft -z-10" />
          <PartyPopper size={20} className="absolute -top-1 -right-1 text-amber-400 animate-float" />
        </div>

        <h2 className="relative text-2xl font-extrabold text-ink mb-1">本次训练完成</h2>
        <p className="relative text-sm text-subtext mb-6">{taskTitle}</p>

        {/* 成长值展示 */}
        <div className="relative bg-gradient-to-br from-slate-50 to-white rounded-2xl p-5 mb-5 flex justify-between items-center border border-slate-100">
          <div className="text-left">
            <p className="text-lg font-bold text-ink">{score}分 · {Math.round(accuracy * 100)}%</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-subtext mb-1">本次获得</p>
            <p className="text-4xl font-black text-growth animate-slide-up">
              <CountUp value={growth} showPlus duration={900} />
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-subtext mb-1">成长值构成</p>
            <p className="text-xs text-subtext leading-relaxed">
              基础 {result?.growth.basePoints ?? 0}<br />
              + 正确率 {result?.growth.accuracyBonus ?? 0}<br />
              + 难度 {result?.growth.difficultyBonus ?? 0}
            </p>
          </div>
        </div>

        {/* 宠物成长条 */}
        {currentPet && (
          <div className="relative rounded-2xl p-4 mb-5 text-left bg-gradient-to-br from-primary-soft/60 to-emerald-50/60 border border-primary/10">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-ink flex items-center">
                <TrendingUp size={16} className="mr-1.5 text-primary" />
                {currentPet.type} · Lv.{currentPet.level} · {currentPet.stage}
              </span>
              <span className="text-xs text-subtext">距下一级还差 <span className="font-semibold text-growth">{currentPet.nextLevelValue - currentPet.growthValue}</span></span>
            </div>
            <div className="w-full bg-white rounded-full h-2.5 overflow-hidden">
              <div className="h-2.5 rounded-full bg-gradient-to-r from-safe to-emerald-400 transition-all duration-700" style={{ width: `${progress}%` }} />
            </div>
            <p className="text-xs text-subtext mt-1.5">当前成长值: <span className="font-semibold text-ink">{currentPet.growthValue}</span> / {currentPet.nextLevelValue}</p>
          </div>
        )}

        {/* 奖励提示 */}
        {rewardMessage && (
          <p className="relative text-sm text-subtext mb-5 flex items-center justify-center gap-1.5">
            <Sparkles size={14} className="text-amber-400" /> {rewardMessage}
          </p>
        )}

        {/* 推荐下一步 */}
        {taskObj && (
          <div className="relative rounded-xl p-4 mb-6 text-left bg-amber-50/60 border border-amber-100">
            <p className="text-xs font-bold text-warning mb-2">推荐下一步训练</p>
            {(() => {
              const nextTask = allTasks.find((t) => t.id !== id);
              return nextTask ? (
                <button
                  onClick={() => navigate(`/training/session/${nextTask.id}`)}
                  className="text-sm text-primary font-semibold hover:underline flex items-center"
                >
                  {nextTask.title} <ArrowRight size={14} className="ml-1" />
                </button>
              ) : null;
            })()}
          </div>
        )}

        {/* 操作按钮 */}
        <div className="relative flex gap-3 justify-center">
          <button onClick={() => navigate('/training')} className="btn-ghost px-6 py-2.5">继续训练</button>
          <button onClick={() => navigate('/pet')} className="btn-primary px-6 py-2.5 flex items-center">
            查看宠物状态 <ArrowRight size={16} className="ml-1" />
          </button>
        </div>
      </div>
    </div>
  );
}
