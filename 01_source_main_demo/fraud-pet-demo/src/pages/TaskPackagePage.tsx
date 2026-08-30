import { useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  Brain,
  Calendar,
  CheckCircle2,
  Circle,
  Play,
  RefreshCw,
  Sparkles,
  Trophy,
  Zap,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Progress } from '../components/ui/Progress';
import { useToast } from '../components/ui/Toast';
import type { AbilityProfile, TaskPackageItem } from '../types';

type PlanType = '7day' | '14day';

/** 任务类型图标映射 */
const TASK_ICONS: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  assessment: Brain,
  scenario: Play,
  retrain: RefreshCw,
  knowledge: Calendar,
};

/** 任务类型标签映射 */
const TASK_LABELS: Record<string, string> = {
  assessment: '专项测评',
  scenario: '情景训练',
  retrain: '错题复训',
  knowledge: '知识学习',
};

export default function TaskPackagePage() {
  const navigate = useNavigate();
  const { error: showError } = useToast();
  const activeTaskPackage = useAppStore((state) => state.activeTaskPackage);
  const abilityProfile = useAppStore((state) => state.abilityProfile);
  const currentUser = useAppStore((state) => state.currentUser);
  const generateTaskPackage = useAppStore((state) => state.generateTaskPackage);
  const loadCurrentTaskPackage = useAppStore((state) => state.loadCurrentTaskPackage);
  const loadAbilityProfile = useAppStore((state) => state.loadAbilityProfile);
  const isLoading = useAppStore((state) => state.isLoading);
  const error = useAppStore((state) => state.error);
  const clearError = useAppStore((state) => state.clearError);

  useEffect(() => {
    loadCurrentTaskPackage();
    loadAbilityProfile();
  }, [loadCurrentTaskPackage, loadAbilityProfile]);

  // 将全局错误以 toast 形式展示给用户，展示后立即清除，防止重复弹窗
  const lastErrorRef = useRef<string | null>(null);
  useEffect(() => {
    if (error && lastErrorRef.current !== error) {
      showError(error);
      lastErrorRef.current = error;
      clearError();
    } else if (!error) {
      lastErrorRef.current = null;
    }
  }, [error, showError, clearError]);

  const handleGenerate = useCallback(async (planType: PlanType) => {
    // 测评前置检查：未完成测评时不调用 API，直接引导去测评
    if (!currentUser?.hasCompletedAssessment && !abilityProfile) {
      showError('请先完成测评，生成能力画像后再创建任务包');
      navigate('/assessment');
      return;
    }
    await generateTaskPackage(planType);
  }, [generateTaskPackage, currentUser, abilityProfile, showError, navigate]);

  const handleActivateItem = useCallback((item: TaskPackageItem) => {
    if (item.isCompleted) return;
    // Navigate based on task type — user completes the task on the target page
    if (item.taskType === 'scenario') {
      const scenarioType = item.fraudType || 'brush_orders';
      navigate(`/training/scenario/${scenarioType}?taskId=${item.id}`);
    } else if (item.taskType === 'assessment') {
      navigate('/assessment?fromTask=' + item.id);
    } else if (item.taskType === 'knowledge') {
      navigate('/knowledge?fromTask=' + item.id);
    } else if (item.taskType === 'retrain') {
      navigate('/training?fromTask=' + item.id);
    }
  }, [navigate]);

  // 判断是否已完成测评
  const hasCompletedAssessment = Boolean(currentUser?.hasCompletedAssessment || abilityProfile);

  // No package — show selection
  if (!activeTaskPackage) {
    // 未完成测评 → 显示引导卡片
    if (!hasCompletedAssessment) {
      return (
        <div className="space-y-5 animate-slide-up">
          <div className="text-center pt-2">
            <div className="w-14 h-14 mx-auto mb-2 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-glow-sm">
              <Sparkles size={28} className="text-white" />
            </div>
            <h1 className="text-lg font-extrabold text-ink">AI 任务包</h1>
          </div>

          {/* 测评引导卡片 */}
          <div className="app-card p-4 bg-gradient-to-br from-amber-50/80 to-orange-50/60 border-amber-200/50 text-center">
            <div className="w-12 h-12 mx-auto mb-2 rounded-2xl bg-amber-500/10 flex items-center justify-center">
              <Brain size={24} className="text-amber-600" />
            </div>
            <h2 className="text-sm font-bold text-amber-800 mb-1">还未完成能力测评</h2>
            <div className="flex flex-col items-center gap-2">
              <div className="flex items-center gap-2 text-[10px] text-amber-600/60">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                预计 5-8 分钟
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                综合能力分析
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                个性化训练方案
              </div>
              <Button
                variant="default"
                size="sm"
                onClick={() => navigate('/assessment')}
                className="gap-1 bg-amber-500 hover:bg-amber-600 border-amber-500"
              >
                开始测评 <ArrowRight size={12} />
              </Button>
            </div>
          </div>

          {/* 下方简述两种方案供用户了解 */}
          <div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 opacity-60 pointer-events-none">
              <PlanCard
                title="7 日速训"
                description="高强度专项突破，聚焦你最薄弱的2-3个维度"
                days={7}
                features={['每日1-2项任务', '错题24h复训', '第7天综合测评']}
                recommended={true}
                onSelect={() => {}}
                loading={false}
              />
              <PlanCard
                title="14 日精训"
                description="系统全面提升，覆盖全部维度，节奏舒缓"
                days={14}
                features={['每日1项任务', '错题3d/7d复训', '第14天综合测评']}
                onSelect={() => {}}
                loading={false}
              />
            </div>
          </div>
        </div>
      );
    }

    // 已完成测评 → 显示方案选择
    return (
      <div className="space-y-5 animate-slide-up">
        <div className="text-center pt-2">
          <div className="w-14 h-14 mx-auto mb-2 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-glow-sm">
            <Sparkles size={28} className="text-white" />
          </div>
          <h1 className="text-lg font-extrabold text-ink">AI 任务包</h1>
        </div>

        {/* 能力画像参考 */}
        {abilityProfile && (
          <div className="app-card p-3">
            <div className="flex items-center gap-2 mb-2">
              <Brain size={14} className="text-primary" aria-hidden />
              <span className="text-xs font-bold text-ink">当前能力画像</span>
              <Badge variant="info" className="text-[10px]">{abilityProfile.level}</Badge>
            </div>
            <div className="space-y-1.5">
              {abilityProfile.dimensions.map((dim) => {
                const isWeak = abilityProfile.weakDimensions.includes(dim.dimension);
                return (
                  <div key={dim.dimension} className="flex items-center gap-2 text-[11px]">
                    <span className={`w-12 font-semibold ${isWeak ? 'text-amber-600' : 'text-ink'}`}>
                      {dim.dimension}
                    </span>
                    <div className="flex-1 h-1 rounded-full bg-slate-100 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${isWeak ? 'bg-amber-400' : 'bg-primary'}`}
                        style={{ width: `${dim.percentage}%` }}
                      />
                    </div>
                    <span className="w-7 text-right text-subtext">{dim.score}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 方案选择 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <PlanCard
            title="7 日速训"
            description="高强度专项突破，聚焦你最薄弱的2-3个维度"
            days={7}
            features={['每日1-2项任务', '错题24h复训', '第7天综合测评']}
            recommended={true}
            onSelect={() => handleGenerate('7day')}
            loading={isLoading}
          />
          <PlanCard
            title="14 日精训"
            description="系统全面提升，覆盖全部维度，节奏舒缓"
            days={14}
            features={['每日1项任务', '错题3d/7d复训', '第14天综合测评']}
            onSelect={() => handleGenerate('14day')}
            loading={isLoading}
          />
        </div>
      </div>
    );
  }

  // Active package — show calendar view
  const progress = activeTaskPackage.progress;
  const allCompleted = activeTaskPackage.completedDays >= activeTaskPackage.totalDays;

  return (
    <div className="space-y-4 animate-slide-up">
      {/* 头部 */}
      <div className="app-card p-3 bg-gradient-to-r from-violet-50/80 to-white/80 border-violet-200/60">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
              <Sparkles size={16} className="text-white" />
            </div>
            <div>
              <h1 className="text-base font-extrabold text-ink">
                {activeTaskPackage.planType === '7day' ? '7 日速训' : '14 日精训'}
              </h1>
              <p className="text-[10px] text-subtext">
                创建于 {new Date(activeTaskPackage.createdAt).toLocaleDateString('zh-CN')}
              </p>
            </div>
          </div>
          <Badge variant={allCompleted ? 'success' : 'info'} className="text-[10px]">
            {allCompleted ? '已完成' : '进行中'}
          </Badge>
        </div>
        <div className="flex items-center gap-3">
          <Progress value={progress} height={6} className="flex-1" />
          <span className="text-xs font-bold text-violet-600 whitespace-nowrap">
            {activeTaskPackage.completedDays}/{activeTaskPackage.totalDays} 天
          </span>
        </div>
        {allCompleted && (
          <div className="mt-2 flex items-center gap-1.5 text-[10px] text-emerald-600">
            <Trophy size={12} aria-hidden />
            <span>恭喜完成全部训练！可以重新测评查看能力变化。</span>
          </div>
        )}
      </div>

      {/* 个性化激励文案 */}
      {abilityProfile && !allCompleted && (
        <IncentiveCard profile={abilityProfile} progress={progress} />
      )}

      {/* 任务日历 */}
      <div className="space-y-2">
        {activeTaskPackage.items.map((item) => (
          <TaskCard
            key={item.id}
            item={item}
            onActivate={() => handleActivateItem(item)}
          />
        ))}
      </div>

      {/* 底部操作 */}
      <div className="flex gap-2 justify-center">
        <Button variant="outline" size="sm" onClick={() => navigate('/assessment')} className="text-xs">
          重新测评
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => handleGenerate(activeTaskPackage.planType as PlanType)}
          loading={isLoading}
          className="text-xs"
        >
          重新生成
        </Button>
      </div>
    </div>
  );
}

/** 方案卡片 */
function PlanCard({
  title,
  description,
  days,
  features,
  recommended = false,
  onSelect,
  loading,
}: {
  title: string;
  description: string;
  days: number;
  features: string[];
  recommended?: boolean;
  onSelect: () => void;
  loading: boolean;
}) {
  return (
    <div className={`app-card p-4 relative ${recommended ? 'border-violet-300/60 bg-gradient-to-br from-violet-50/60 to-white/80' : ''}`}>
      {recommended && (
        <div className="absolute -top-2 right-3">
          <Badge variant="info" size="sm">
            <Zap size={10} aria-hidden /> 推荐
          </Badge>
        </div>
      )}
      <div className="flex items-center gap-2 mb-1.5">
        <Calendar size={16} className="text-violet-600" aria-hidden />
        <h3 className="text-sm font-bold text-ink">{title}</h3>
        <Badge variant="outline" size="sm">{days} 天</Badge>
      </div>
      <p className="text-[11px] text-subtext mb-2">{description}</p>
      <ul className="space-y-1 mb-3">
        {features.map((f, i) => (
          <li key={i} className="flex items-start gap-1.5 text-[11px] text-ink/80">
            <CheckCircle2 size={11} className="text-violet-500 mt-0.5 flex-shrink-0" aria-hidden />
            {f}
          </li>
        ))}
      </ul>
      <Button
        variant={recommended ? 'default' : 'outline'}
        size="sm"
        fullWidth
        onClick={onSelect}
        loading={loading}
        className="gap-1 text-xs"
      >
        开始 {days} 日计划 <ArrowRight size={12} />
      </Button>
    </div>
  );
}

/** 任务卡片 */
function TaskCard({ item, onActivate }: { item: TaskPackageItem; onActivate: () => void }) {
  const Icon = TASK_ICONS[item.taskType] ?? Circle;

  return (
    <button
      onClick={onActivate}
      disabled={item.isCompleted}
      className={`app-card app-card-hover p-2.5 text-left w-full transition-all ${
        item.isCompleted
          ? 'opacity-60 border-emerald-200/60 bg-emerald-50/30'
          : 'hover:shadow-glow-sm'
      }`}
    >
      <div className="flex items-center gap-2.5">
        {/* 状态图标 */}
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
          item.isCompleted
            ? 'bg-emerald-500/10'
            : item.taskType === 'retrain'
              ? 'bg-amber-500/10'
              : 'bg-violet-500/10'
        }`}>
          {item.isCompleted ? (
            <CheckCircle2 size={16} className="text-emerald-600" aria-hidden />
          ) : (
            <Icon size={16} className={item.taskType === 'retrain' ? 'text-amber-600' : 'text-violet-600'} aria-hidden />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-0.5">
            <span className="text-[10px] font-bold text-subtext">Day {item.day}</span>
            <Badge
              variant={item.isCompleted ? 'success' : 'outline'}
              size="sm"
              className="text-[10px]"
            >
              {TASK_LABELS[item.taskType] ?? item.taskType}
            </Badge>
            {item.fraudType && (
              <Badge variant="warning" size="sm" className="text-[10px]">{item.fraudType}</Badge>
            )}
          </div>
          <h4 className="text-xs font-bold text-ink">{item.title}</h4>
          {item.description && (
            <p className="text-[10px] text-subtext line-clamp-1">{item.description}</p>
          )}
          {item.isCompleted && item.score != null && (
            <div className="flex items-center gap-1 mt-0.5 text-[10px]">
              <Trophy size={10} className="text-emerald-500" aria-hidden />
              <span className="font-semibold text-emerald-600">{item.score} 分</span>
            </div>
          )}
        </div>

        {/* 状态/操作 */}
        <div className="flex-shrink-0 self-center">
          {item.isCompleted ? (
            <CheckCircle2 size={18} className="text-emerald-500" aria-hidden />
          ) : (
            <div className="w-6 h-6 rounded-full bg-violet-500/10 flex items-center justify-center">
              <ArrowRight size={12} className="text-violet-500" aria-hidden />
            </div>
          )}
        </div>
      </div>
    </button>
  );
}

/** 个性化激励卡片 — 根据能力画像生成鼓励语 */
function IncentiveCard({ profile, progress }: { profile: AbilityProfile; progress: number }) {
  const { weakDimensions, level, overallScore, dimensions } = profile;
  const lowestDim = dimensions.reduce((min, d) => d.score < min.score ? d : min, dimensions[0]);

  const messages: Record<string, string> = {
    '辨识力': '识别风险信号、异常话术的能力需要加强，每多识破一个骗局就多一份安全！',
    '判断力': '理性判断是综合能力的第一道防线，训练中学会多问一个"为什么"。',
    '应变力': '正确应对可疑情况需要练习，每一次模拟都在帮你建立肌肉记忆。',
    '实证力': '核验与保留证据是事后维权的关键，别忘了截图和留痕的威力。',
    '协作力': '知道何时求助、向谁求助同样重要，辅导员与家长永远在你身后。',
  };

  const levelMessages: Record<string, string> = {
    '综合卓越': '你已经是综合能力达人了，精益求精，挑战满分！',
    '综合优秀': '进步显著，你的综合能力正在快速提升！',
    '综合良好': '你已经迈出了关键一步，继续保持这个节奏！',
    '综合入门': '万事开头难，每完成一项任务都是质的飞跃！',
    '反诈守护者': '你已经是综合能力达人了，精益求精，挑战满分！',
    '成长期': '进步显著，你的综合能力正在快速提升！',
    '学习期': '你已经迈出了关键一步，继续保持这个节奏！',
    '幼崽期': '万事开头难，每完成一项任务都是质的飞跃！',
  };

  const incentiveText = progress > 0
    ? `已完成 ${progress}%，继续加油！${messages[lowestDim.dimension] || ''}`
    : `新任务包已就绪！${levelMessages[level] || '开始你的训练之旅吧！'} 本期重点提升「${lowestDim.dimension}」（当前${lowestDim.score}分）。`;

  return (
    <div className="app-card p-3 bg-gradient-to-r from-amber-50/80 to-orange-50/60 border-amber-200/50">
      <div className="flex items-start gap-2.5">
        <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center shrink-0">
          <Zap size={16} className="text-amber-600" aria-hidden />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-0.5">
            <span className="text-xs font-bold text-amber-700">AI 激励</span>
            <Badge variant="warning" size="sm" className="text-[10px]">{level}</Badge>
            <span className="text-[10px] text-amber-600/60">综合 {overallScore} 分</span>
          </div>
          <p className="text-xs text-amber-800/80 leading-snug line-clamp-2">{incentiveText}</p>
          {weakDimensions.length > 0 && (
            <div className="flex gap-1 mt-1.5 flex-wrap">
              {weakDimensions.map((dim) => (
                <span key={dim} className="text-[9px] bg-amber-100 text-amber-600 px-1.5 py-0.5 rounded-full font-medium">
                  {dim}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
