/**
 * 辅导员看板 — 匿名学生画像与班级汇总
 * 展示班级整体反诈能力概览，支持数据驱动班会策划
 */
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { DIMENSION_ICONS, getDimensionColor } from '../lib/constants';
import { DIMENSION_KEY_MAP } from '../api/client';

const FRAUD_COLORS: string[] = [
  '#ef4444', '#f97316', '#eab308', '#22c55e', '#14b8a6', '#3b82f6', '#8b5cf6', '#ec4899',
];

export default function CounselorDashboardPage() {
  const dashboard = useAppStore((s) => s.counselorDashboard);
  const loadDashboard = useAppStore((s) => s.loadCounselorDashboard);
  const isLoading = useAppStore((s) => s.isLoading);
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  if (isLoading || !dashboard) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        {isLoading ? '加载看板中...' : '暂无数据'}
      </div>
    );
  }

  const { overview, avgScores, weakDistribution, fraudDistribution, trainingTrend, studentProfiles } = dashboard;
  const maxTrend = Math.max(...trainingTrend.map(t => t.count), 1);

  // 兼容后端尚未热更新的历史维度名（识诈力等）→ 当前中性维度名
  const normAvgScores = Object.fromEntries(
    Object.entries(avgScores ?? {}).map(([dim, score]) => [DIMENSION_KEY_MAP[dim] ?? dim, score]),
  );
  const normWeak = (weakDistribution ?? []).map((item: any) => ({
    ...item,
    dimension: DIMENSION_KEY_MAP[item.dimension] ?? item.dimension,
  }));

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold text-gray-800">辅导员看板</h1>
        <span className="text-sm text-gray-400">学生数据已匿名处理</span>
      </div>

      {/* 概览卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <StatCard icon="👥" label="学生总数" value={overview.totalStudents.toString()} />
        <StatCard icon="📊" label="测评率" value={`${overview.assessedRate}%`} />
        <StatCard icon="🐾" label="宠物领养率" value={`${overview.petRate}%`} />
        <StatCard icon="🏋️" label="训练总次数" value={overview.totalTraining.toString()} />
        <StatCard
          icon="🎯"
          label="平均正确率"
          value={`${overview.avgAccuracy}%`}
          highlight={overview.avgAccuracy >= 80}
        />
      </div>

      {/* 能力均值 + 薄弱分布 */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* 综合能力均值 */}
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <h2 className="font-bold text-gray-800 mb-4">综合能力均值</h2>
          <div className="space-y-3">
            {Object.entries(normAvgScores).map(([dim, score]) => (
              <div key={dim} className="flex items-center gap-3">
                <span className="text-sm w-16 font-medium text-gray-600">{DIMENSION_ICONS[dim] || '📌'} {dim}</span>
                <div className="flex-1 h-6 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${score}%`,
                      backgroundColor: getDimensionColor(dim),
                    }}
                  />
                </div>
                <span className="text-sm font-bold w-10 text-right" style={{ color: getDimensionColor(dim) }}>
                  {score}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* 薄弱维度分布 */}
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <h2 className="font-bold text-gray-800 mb-4">薄弱维度分布</h2>
          <div className="space-y-3">
            {normWeak.map((item) => (
              <div key={item.dimension} className="flex items-center gap-3">
                <span className="text-sm w-16 font-medium text-gray-600">{DIMENSION_ICONS[item.dimension] || '📌'} {item.dimension}</span>
                <div className="flex-1 h-6 bg-amber-50 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-amber-400 rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min((item.count / (weakDistribution[0]?.count || 1)) * 100, 100)}%`,
                    }}
                  />
                </div>
                <span className="text-sm font-bold text-amber-600 w-10 text-right">
                  {item.count}人
                </span>
              </div>
            ))}
            {weakDistribution.length === 0 && (
              <p className="text-sm text-gray-400 text-center py-4">暂无薄弱维度数据</p>
            )}
          </div>
        </div>
      </div>

      {/* 诈骗类型分布 */}
      <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
        <h2 className="font-bold text-gray-800 mb-4">诈骗类型训练分布</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {fraudDistribution.map((item, idx) => {
            const maxCount = fraudDistribution[0]?.count || 1;
            const pct = Math.round((item.count / maxCount) * 100);
            return (
              <div key={item.type} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full shrink-0"
                  style={{ backgroundColor: FRAUD_COLORS[idx % FRAUD_COLORS.length] }}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-500 truncate">{item.type}</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${pct}%`,
                          backgroundColor: FRAUD_COLORS[idx % FRAUD_COLORS.length],
                        }}
                      />
                    </div>
                    <span className="text-xs font-medium text-gray-600">{item.count}</span>
                  </div>
                </div>
              </div>
            );
          })}
          {fraudDistribution.length === 0 && (
            <p className="text-sm text-gray-400 py-4 col-span-full text-center">暂无训练数据</p>
          )}
        </div>
      </div>

      {/* 训练趋势 + 学生画像 */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* 7天训练趋势 */}
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <h2 className="font-bold text-gray-800 mb-4">近7天训练趋势</h2>
          <div className="flex items-end gap-2 h-32">
            {trainingTrend.map((t) => (
              <div key={t.date} className="flex-1 flex flex-col items-center gap-1">
                <span className="text-xs font-medium text-gray-600">{t.count}</span>
                <div
                  className="w-full bg-blue-400 rounded-t-md transition-all duration-300"
                  style={{ height: `${(t.count / maxTrend) * 100}%`, minHeight: t.count > 0 ? 4 : 0 }}
                />
                <span className="text-[10px] text-gray-400">{t.date}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 学生画像简要列表 */}
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <h2 className="font-bold text-gray-800 mb-4">学生匿名画像（Top 10）</h2>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {studentProfiles.slice(0, 10).map((s) => (
              <div key={s.ownerId} className="flex items-center gap-3 py-1.5 border-b border-gray-50 last:border-0">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
                  {s.overallScore}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{s.ownerId}</p>
                  <div className="flex gap-1 flex-wrap">
                    {s.weakDimensions.slice(0, 2).map((d) => (
                      <span
                        key={d}
                        className="text-[10px] px-1.5 py-0.5 rounded-full"
                        style={{ backgroundColor: getDimensionColor(d) + '20', color: getDimensionColor(d) }}
                      >
                        {d}
                      </span>
                    ))}
                    {s.weakDimensions.length > 2 && (
                      <span className="text-[10px] text-gray-400">+{s.weakDimensions.length - 2}</span>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs font-medium text-blue-600">{s.accuracy}%</p>
                  <p className="text-[10px] text-gray-400">Lv.{s.petLevel}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 班会素材入口 */}
      <button
        onClick={() => navigate('/counselor/class-meeting')}
        className="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-2xl p-4 font-bold text-lg shadow-md hover:shadow-lg transition-shadow"
      >
        📋 生成班会素材
      </button>
    </div>
  );
}

function StatCard({ icon, label, value, highlight }: {
  icon: string;
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className={`rounded-xl p-4 border shadow-sm ${highlight ? 'bg-green-50 border-green-200' : 'bg-white border-gray-100'}`}>
      <p className="text-2xl mb-1">{icon}</p>
      <p className="text-2xl font-bold text-gray-800">{value}</p>
      <p className="text-xs text-gray-400">{label}</p>
    </div>
  );
}
