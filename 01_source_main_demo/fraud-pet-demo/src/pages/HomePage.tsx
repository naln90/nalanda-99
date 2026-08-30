import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  BookOpen,
  Brain,
  CalendarCheck,
  ChevronRight,
  FileUp,
  Sparkles,
  TrendingUp,
  Zap,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { api } from '../api/client';
import type { KnowledgeItem } from '../types';
import { resolvePetAvatar } from '../lib/pet-utils';
import { resolveThemeProfile, getHomeGreeting, getDailyTip } from '../lib/themeProfile';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import RadarChart from '../components/effects/RadarChart';
import RetrainSection from '../components/RetrainSection';

export default function HomePage() {
  const navigate = useNavigate();
  const currentUser = useAppStore((state) => state.currentUser);
  const nickname = useAppStore((state) => state.nickname);
  const pet = useAppStore((state) => state.pet);
  const dashboard = useAppStore((state) => state.dashboard);
  const abilityProfile = useAppStore((state) => state.abilityProfile);
  const activeLearningTheme = useAppStore((state) => state.activeLearningTheme);
  const loadDashboard = useAppStore((state) => state.loadDashboard);
  const loadAbilityProfile = useAppStore((state) => state.loadAbilityProfile);

  // 首页是通用入口：未激活任何学习主题时回退到中性（不默认喊“反诈”），
  // 与“可配置主题平台”的定位一致；激活后随当前主题自适应。
  const themeProfile = useMemo(
    () => resolveThemeProfile(activeLearningTheme ?? ''),
    [activeLearningTheme],
  );
  const dailyTip = useMemo(() => getDailyTip(themeProfile), [themeProfile]);

  useEffect(() => {
    loadDashboard();
    if (currentUser?.hasCompletedAssessment) {
      loadAbilityProfile();
    }
  }, [loadDashboard, loadAbilityProfile, currentUser?.hasCompletedAssessment]);

  const hasAssessment = currentUser?.hasCompletedAssessment;

  return (
    <div className="space-y-3">
      {/* ========== 欢迎头部 ========== */}
      <div className="animate-bento-in">
        <h1 className="text-2xl font-bold text-ink">
          {getGreeting()}，{nickname ?? '同学'}
        </h1>
      </div>

      {/* ========== 宠物 + 每日提示 ========== */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {pet && (
          <button
            onClick={() => navigate('/pet')}
            className="bento-card bento-card-interactive bento-card-blue md:col-span-2 p-3 text-left animate-bento-in"
          >
            <div className="flex items-center gap-3">
              <div className="icon-box bg-gradient-to-br from-primary/20 to-indigo-100 border border-primary/20">
                <span className="text-2xl" role="img" aria-label={`${pet.type} ${pet.stage}`}>
                  {resolvePetAvatar(pet)}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-base font-bold text-ink">{pet.petName}</span>
                  <Badge variant="info" size="sm">{pet.stage}</Badge>
                </div>
                <div className="flex items-center gap-3 text-xs text-subtext mt-1">
                  <span className="font-medium text-ink">Lv.{pet.level}</span>
                  <div className="flex-1 min-w-[80px]">
                    <div className="h-2 rounded-full bg-primary/10 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-primary to-primary-deep transition-all duration-700 min-w-[4px]"
                        style={{ width: `${Math.max(2, ((pet.growthValue - pet.currentLevelMin) / (pet.nextLevelValue - pet.currentLevelMin)) * 100)}%` }}
                      />
                    </div>
                  </div>
                  <span className="text-xs tabular-nums">{pet.growthValue}/{pet.nextLevelValue}</span>
                </div>
              </div>
              <ChevronRight size={16} className="text-subtext/50 flex-shrink-0" />
            </div>
          </button>
        )}

        <div className={`bento-card bento-card-amber p-3 animate-bento-in ${pet ? '' : 'md:col-span-3'}`}>
          <div className="flex items-start gap-2">
            <div className="icon-box-xs bg-amber-500/10">
              <Sparkles size={14} className="text-amber-600" aria-hidden />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5 mb-0.5">
                <span className="text-xs font-bold text-ink">{dailyTip.label}</span>
                <span className="status-dot status-dot-warning" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ========== 快速开始 ========== */}
      <div className="animate-bento-in">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-bold text-ink">快速开始</h2>
          {dashboard && dashboard.consecutiveDays > 0 && (
            <Badge variant="warning" size="sm" className="gap-1">
              <Zap size={10} /> 连续 {dashboard.consecutiveDays} 天
            </Badge>
          )}
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <button
            onClick={() => navigate('/training')}
            className="bento-card bento-card-interactive bento-card-blue p-4 flex items-center gap-3 text-left group"
            aria-label="进入今日训练"
          >
            <div className="icon-box icon-box-blue flex-shrink-0 transition-transform group-hover:scale-110">
              <Brain size={20} className="text-white" aria-hidden />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-bold text-ink">今日训练</h3>
              {dashboard && dashboard.totalTrainingCount > 0 && (
                <div className="flex items-center gap-1 mt-1.5 text-xs text-primary/70">
                  <TrendingUp size={12} aria-hidden />
                  <span>累计 {dashboard.totalTrainingCount} 次</span>
                </div>
              )}
            </div>
          </button>

          <button
            onClick={() => navigate('/learning/workspace')}
            className="bento-card bento-card-interactive bento-card-violet p-4 flex items-center gap-3 text-left group"
            aria-label="查看AI任务包"
          >
            <div className="icon-box icon-box-violet flex-shrink-0 transition-transform group-hover:scale-110">
              <CalendarCheck size={20} className="text-white" aria-hidden />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-bold text-ink">AI 学习任务包</h3>
            </div>
          </button>

          <button
            onClick={() => navigate('/learning/artifacts')}
            className="bento-card bento-card-interactive bento-card-cyan p-4 flex items-center gap-3 text-left group"
            aria-label="进入我的成果工坊"
          >
            <div className="icon-box bg-cyan-500/10 flex-shrink-0 transition-transform group-hover:scale-110">
              <FileUp size={20} className="text-cyan-600" aria-hidden />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-bold text-ink">我的成果</h3>
              <p className="text-xs text-subtext mt-0.5">创作、沉淀与展示学习成果</p>
            </div>
          </button>

          <button
            onClick={() => navigate('/knowledge')}
            className="bento-card bento-card-interactive bento-card-amber p-4 flex items-center gap-3 text-left group"
            aria-label="进入综合知识库"
          >
            <div className="icon-box bg-amber-500/10 flex-shrink-0 transition-transform group-hover:scale-110">
              <BookOpen size={20} className="text-amber-600" aria-hidden />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-bold text-ink">综合知识库</h3>
            </div>
          </button>
        </div>
      </div>

      {/* ========== 综合能力画像（基于已参与主题的综合评估） ========== */}
      {hasAssessment && abilityProfile && (
        <div className="bento-card p-5 animate-bento-in space-y-5">
          {/* 头部 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="icon-box icon-box-blue">
                <Brain size={18} className="text-white" aria-hidden />
              </div>
              <div>
                <h2 className="text-base font-bold text-ink">综合能力画像</h2>
                <p className="text-xs text-subtext mt-0.5">基于你已参与主题的综合评估</p>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={() => navigate('/assessment')} className="gap-1 h-8 text-sm">
              重新测评 <ArrowRight size={14} />
            </Button>
          </div>

          {/* 雷达图 + 进度条 */}
          <div className="flex flex-col md:flex-row items-center gap-6">
            <div className="flex-shrink-0">
              <RadarChart
                dimensions={abilityProfile.dimensions.map((d) => ({
                  label: d.dimension,
                  value: d.percentage,
                }))}
                size={160}
                labelSize={11}
              />
            </div>

            <div className="flex-1 min-w-0 w-full space-y-3">
              {abilityProfile.dimensions.map((dim) => {
                const isWeak = abilityProfile.weakDimensions.includes(dim.dimension);
                const isStrong = abilityProfile.strongDimensions.includes(dim.dimension);
                return (
                  <div key={dim.dimension} className="flex items-center gap-3">
                    <span className={`text-xs font-semibold w-12 text-right flex-shrink-0 ${
                      isWeak ? 'text-amber-600' : 'text-ink'
                    }`}>
                      {dim.dimension}
                    </span>
                    <div className="flex-1 progress-track h-2.5">
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
                    <span className={`text-xs font-bold w-12 flex-shrink-0 text-right ${
                      isWeak ? 'text-amber-600' : isStrong ? 'text-emerald-600' : 'text-primary'
                    }`}>
                      {dim.score}/{dim.maxScore}
                    </span>
                  </div>
                );
              })}

              <div className="divider-dashed my-2" />

              <div className="flex items-center gap-3">
                <span className="text-xs font-semibold text-ink w-12 text-right">综合</span>
                <div className="flex-1 progress-track h-2.5">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-primary via-violet-500 to-purple-500 transition-all duration-700"
                    style={{ width: `${abilityProfile.overallScore}%` }}
                  />
                </div>
                <Badge variant={
                  abilityProfile.level === '综合卓越' ? 'success' :
                  abilityProfile.level === '综合优秀' ? 'info' : 'warning'
                } size="sm" className="ml-1">
                  {abilityProfile.level}
                </Badge>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========== 未测评引导 ========== */}
      {!hasAssessment && (
        <div className="bento-card bento-card-blue p-4 text-center animate-bento-in">
          <div className="icon-box icon-box-blue mx-auto mb-2">
            <Brain size={20} className="text-white" />
          </div>
          <h3 className="text-base font-bold text-ink mb-1">先测测你的综合能力</h3>
          <Button size="sm" onClick={() => navigate('/assessment')} className="gap-1">
            开始测评 <ArrowRight size={14} />
          </Button>
        </div>
      )}

      {/* ========== 知识库入口 + 复训提醒（首页聚焦能力画像与知识库，宠物/成长榜见侧栏） ========== */}
      {hasAssessment && (
        <div className="space-y-3 animate-bento-in">
          <KnowledgePreview onClick={() => navigate('/knowledge')} />
          <RetrainSection />
        </div>
      )}

      {!hasAssessment && <RetrainSection />}
    </div>
  );
}

function getGreeting() {
  const h = new Date().getHours();
  if (h < 6) return '夜深了';
  if (h < 12) return '早上好';
  if (h < 14) return '中午好';
  if (h < 18) return '下午好';
  return '晚上好';
}

/** 首页知识库预览卡片：展示多主题知识，点击跳转完整知识库 */
function KnowledgePreview({ onClick }: { onClick: () => void }) {
  const [previews, setPreviews] = useState<KnowledgeItem[]>([]);

  useEffect(() => {
    api.getKnowledgeItems()
      .then((res) => {
        // 每个主题取一条代表性条目，最多展示 4 个主题
        const seen = new Set<string>();
        const picks: KnowledgeItem[] = [];
        for (const item of res.items) {
          if (!seen.has(item.theme)) {
            seen.add(item.theme);
            picks.push(item);
          }
          if (picks.length >= 4) break;
        }
        setPreviews(picks);
      })
      .catch(() => setPreviews([]));
  }, []);

  const themeEmoji: Record<string, string> = {
    网络安全: '🔐',
    心理健康: '🧠',
    消防安全: '🧯',
    交通安全: '🚦',
    求职就业: '💼',
    金融素养: '💰',
    学术诚信: '📜',
    个人信息保护: '🔏',
    校园安全: '🏫',
    应急避险: '⛑️',
  };

  return (
    <button
      onClick={onClick}
      aria-label="综合知识库"
      className="bento-card bento-card-interactive bento-card-cyan p-3 text-left h-full flex flex-col justify-between"
    >
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="icon-box-sm bg-cyan-500/10">
            <BookOpen size={14} className="text-cyan-600" aria-hidden />
          </div>
          <ChevronRight size={14} className="text-subtext" />
        </div>
        <h3 className="text-xs font-bold text-ink mb-1">综合知识库</h3>
      </div>
      <div className="mt-2 space-y-1">
        {previews.slice(0, 2).map((item) => (
          <div key={item.id} className="flex items-center gap-1 text-[10px] text-ink truncate">
            <span>{themeEmoji[item.theme] ?? '📄'}</span>
            <span className="truncate">{item.title}</span>
          </div>
        ))}
      </div>
    </button>
  );
}
