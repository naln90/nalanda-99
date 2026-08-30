import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowRight,
  Award,
  Brain,
  CheckCircle2,
  Lightbulb,
  Radar,
  Sparkles,
  Target,
  TrendingUp,
  Trophy,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { useEffect } from 'react';
import { RadarChart } from '../components/effects';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import type { AbilityDimension } from '../types';

export default function AssessmentResultPage() {
  const navigate = useNavigate();
  const currentUser = useAppStore((s) => s.currentUser);
  const assessmentResult = useAppStore((s) => s.assessmentResult);
  const isLoading = useAppStore((s) => s.isLoading);

  useEffect(() => {
    if (!assessmentResult) {
      navigate('/assessment', { replace: true });
    }
  }, [assessmentResult, navigate]);

  if (!assessmentResult) return null;

  const accuracy = assessmentResult.accuracy;
  const accuracyScore = Math.round(accuracy * 100);
  const growthAwarded = assessmentResult.growthAwarded ?? 30;

  // 使用后台返回的综合能力画像
  const abilityProfile = assessmentResult.abilityProfile;
  const hasRealProfile = Boolean(abilityProfile?.dimensions?.length);

  // 如果没有真实能力画像，基于准确率做均匀估算并标注"预估"
  const displayDimensions = abilityProfile?.dimensions ?? [
    { dimension: '辨识力' as AbilityDimension, score: accuracyScore, maxScore: 100, percentage: accuracyScore },
    { dimension: '判断力' as AbilityDimension, score: accuracyScore, maxScore: 100, percentage: accuracyScore },
    { dimension: '应变力' as AbilityDimension, score: accuracyScore, maxScore: 100, percentage: accuracyScore },
    { dimension: '实证力' as AbilityDimension, score: accuracyScore, maxScore: 100, percentage: accuracyScore },
    { dimension: '协作力' as AbilityDimension, score: accuracyScore, maxScore: 100, percentage: accuracyScore },
  ];

  const weakDimensions = abilityProfile?.weakDimensions ?? (
    displayDimensions.filter((d) => d.percentage < 60).map((d) => d.dimension)
  );
  const strongDimensions = abilityProfile?.strongDimensions ?? (
    displayDimensions.filter((d) => d.percentage >= 80).map((d) => d.dimension)
  );

  const handleGeneratePlan = () => {
    // 收敛到新主题无关学习链路：基于测评薄弱维度，前往「发布学习目标」创建任意主题任务包
    navigate('/learning/goal');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      {/* ========== 测评结果总览 ========== */}
      <div className="relative app-card p-8 overflow-hidden text-center animate-pop">
        <div className="absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r from-primary via-violet-500 to-emerald-500" />
        <div className="absolute inset-0 bg-mesh opacity-60" />
        <div className="relative">
          <div className="relative w-20 h-20 mx-auto mb-4">
            <div className="w-20 h-20 rounded-full bg-emerald-50 flex items-center justify-center border-2 border-emerald-100">
              <CheckCircle2 size={36} className="text-safe" />
            </div>
            <div className="absolute inset-0 w-20 h-20 rounded-full bg-emerald-400/30 blur-xl animate-pulse-soft -z-10" />
          </div>
          <h2 className="text-2xl font-extrabold text-ink mb-1">测评完成</h2>
          {abilityProfile && (
            <div className="flex items-center justify-center gap-2 mb-1">
              <Badge variant={weakDimensions.length > 0 ? 'warning' : 'success'} size="lg">
                {abilityProfile.level}
              </Badge>
            </div>
          )}

          <div className="flex justify-center gap-10 mb-2">
            <Stat
              icon={<Target size={16} />}
              label="正确率"
              value={`${accuracyScore}%`}
              sub={`${assessmentResult.correctCount}/${assessmentResult.totalCount} 题`}
            />
            <Stat
              icon={<TrendingUp size={16} />}
              label="获得成长值"
              value={`+${growthAwarded}`}
              valueClass="text-growth"
            />
            <Stat
              icon={<Award size={16} />}
              label="解锁状态"
              value="宠物池已开启"
              valueClass="text-primary"
            />
          </div>
        </div>
      </div>

      {/* ========== 综合能力画像雷达图 ========== */}
      <div className="app-card p-6 animate-slide-up" style={{ animationDelay: '60ms' }}>
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-extrabold text-ink flex items-center">
            <Radar size={18} className="mr-2 text-primary" aria-hidden /> 综合能力画像
          </h3>
          {hasRealProfile && abilityProfile ? (
            <Badge variant="info" size="sm">
              综合 {abilityProfile.overallScore}%
            </Badge>
          ) : (
            <Badge variant="warning" size="sm">
              预估数据
            </Badge>
          )}
        </div>

        <div className="flex flex-col lg:flex-row items-center gap-6">
          {/* 雷达图 */}
          <div className="flex-shrink-0">
            <RadarChart
              dimensions={displayDimensions.map((d) => ({
                label: d.dimension,
                value: d.percentage,
              }))}
              size={280}
              labelSize={11}
            />
          </div>

          {/* 维度详情 */}
          <div className="flex-1 w-full space-y-3">
            {displayDimensions.map((dim) => {
              const isWeak = weakDimensions.includes(dim.dimension);
              const isStrong = strongDimensions.includes(dim.dimension);
              return (
                <div key={dim.dimension}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-1.5">
                      <span className="text-sm font-bold text-ink">{dim.dimension}</span>
                      {isWeak && <Badge variant="warning" size="sm">薄弱</Badge>}
                      {isStrong && <Badge variant="success" size="sm">优势</Badge>}
                    </div>
                    <span className={`text-xs font-bold ${isWeak ? 'text-amber-600' : isStrong ? 'text-emerald-600' : 'text-primary'}`}>
                      {dim.score}/{dim.maxScore}
                    </span>
                  </div>
                  <div className="h-2.5 w-full rounded-full bg-slate-100 overflow-hidden mb-0.5">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${
                        isWeak
                          ? 'bg-gradient-to-r from-amber-400 to-orange-400'
                          : isStrong
                            ? 'bg-gradient-to-r from-emerald-400 to-green-500'
                            : 'bg-gradient-to-r from-primary to-primary-deep'
                      }`}
                      style={{ width: `${dim.percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ========== 薄弱维度提醒 ========== */}
      {weakDimensions.length > 0 && (
        <div className="app-card p-5 animate-slide-up border-amber-200/60 bg-amber-50/30" style={{ animationDelay: '80ms' }}>
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 flex items-center justify-center flex-shrink-0">
              <AlertTriangle size={18} className="text-amber-600" aria-hidden />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-bold text-amber-800 mb-1.5">需要重点提升的维度</h3>
              <div className="flex flex-wrap gap-1.5 mb-2">
                {weakDimensions.map((dim) => (
                  <Badge key={dim} variant="warning">{dim}</Badge>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========== AI 任务包入口 ========== */}
      <div className="app-card p-6 animate-slide-up bg-gradient-to-br from-violet-50/60 to-white/80 border-violet-200/60" style={{ animationDelay: '120ms' }}>
        <div className="flex flex-col sm:flex-row items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow-glow-sm">
            <Brain size={24} className="text-white" />
          </div>
          <div className="flex-1 text-center sm:text-left">
            <h3 className="font-extrabold text-ink">生成专属训练计划</h3>
          </div>
          <Button onClick={handleGeneratePlan} loading={isLoading} className="gap-1.5 flex-shrink-0">
            <Sparkles size={14} aria-hidden /> 生成 AI 任务包 <ArrowRight size={14} />
          </Button>
        </div>
      </div>

      {/* ========== 进入宠物选择池 ========== */}
      <div className="relative rounded-2xl p-6 overflow-hidden border border-primary/15 animate-slide-up" style={{ animationDelay: '200ms' }}>
        <div className="absolute inset-0 bg-gradient-to-r from-primary-soft to-emerald-50" />
        <div className="relative flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-white flex items-center justify-center shadow-glow-sm flex-shrink-0">
              <Award size={24} className="text-primary" />
            </div>
            <div className="text-center sm:text-left">
              <h3 className="font-extrabold text-ink">宠物选择池已解锁！</h3>
            </div>
          </div>
          <Button onClick={() => navigate('/pet-select')} className="gap-1.5 flex-shrink-0">
            进入宠物选择池 <ArrowRight size={16} />
          </Button>
        </div>
      </div>

      {/* ========== 提升建议 ========== */}
      {weakDimensions.length > 0 && (
        <div className="app-card p-5 animate-slide-up" style={{ animationDelay: '240ms' }}>
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb size={16} className="text-primary" aria-hidden />
            <span className="text-sm font-bold text-ink">提升建议</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <TipCard
              icon={Trophy}
              title="坚持每日训练"
            />
            <TipCard
              icon={Target}
              title="AI任务包"
            />
            <TipCard
              icon={Brain}
              title="错题复训"
            />
            <TipCard
              icon={CheckCircle2}
              title="定期测评"
            />
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({
  icon,
  label,
  value,
  valueClass = 'text-ink',
  sub,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  valueClass?: string;
  sub?: string;
}) {
  return (
    <div className="text-center">
      <p className="text-xs text-subtext mb-1 flex items-center justify-center gap-1">
        {icon} {label}
      </p>
      <p className={`text-2xl font-black ${valueClass}`}>{value}</p>
      {sub && <p className="text-xs text-subtext mt-0.5">{sub}</p>}
    </div>
  );
}

function TipCard({
  icon: Icon,
  title,
}: {
  icon: React.ComponentType<{ size?: number; className?: string }>;
  title: string;
}) {
  return (
    <div className="p-3 rounded-xl bg-slate-50/80 border border-slate-100 flex items-start gap-3">
      <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
        <Icon size={14} className="text-primary" aria-hidden />
      </div>
      <div>
        <h4 className="text-sm font-bold text-ink">{title}</h4>
      </div>
    </div>
  );
}
