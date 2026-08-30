import { useEffect, useState, useCallback } from 'react';
import {
  Activity,
  BarChart3,
  Clock,
  Cpu,
  FileText,
  Filter,
  RefreshCw,
  Search,
  Shield,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Tabs, TabsList, TabsTrigger } from '../components/ui/Tabs';

export default function EvidenceCenterPage() {
  const evidenceOverview = useAppStore((state) => state.evidenceOverview);
  const aiLogs = useAppStore((state) => state.aiLogs);
  const loadEvidenceOverview = useAppStore((state) => state.loadEvidenceOverview);
  const loadAILogs = useAppStore((state) => state.loadAILogs);

  const [activeTab, setActiveTab] = useState('overview');
  const [filterCallType, setFilterCallType] = useState<string | null>(null);

  useEffect(() => {
    loadEvidenceOverview();
    loadAILogs(50);
  }, [loadEvidenceOverview, loadAILogs]);

  const handleRefresh = useCallback(async () => {
    loadEvidenceOverview();
    loadAILogs(50);
  }, [loadEvidenceOverview, loadAILogs]);

  return (
    <div className="space-y-5 animate-slide-up">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500/20 to-blue-500/5 flex items-center justify-center">
            <Shield size={18} className="text-blue-600" aria-hidden />
          </div>
          <div>
            <h1 className="text-lg font-extrabold text-ink">赛事证据中心</h1>
            <p className="text-xs text-subtext">AI 调用透明化记录 · Prompt 版本可追溯</p>
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={handleRefresh} className="gap-1">
          <RefreshCw size={14} aria-hidden /> 刷新
        </Button>
      </div>

      {/* 标签页 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">统计概览</TabsTrigger>
          <TabsTrigger value="logs">调用日志</TabsTrigger>
          <TabsTrigger value="prompts">Prompt版本</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* ========== 统计概览 ========== */}
      {activeTab === 'overview' && (
        <div className="space-y-4">
          {evidenceOverview ? (
            <>
              {/* 统计卡片 */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <StatCard
                  icon={Activity}
                  label="总调用次数"
                  value={evidenceOverview.totalCalls}
                  color="primary"
                />
                <StatCard
                  icon={TrendingUp}
                  label="成功率"
                  value={`${(evidenceOverview.successRate * 100).toFixed(1)}%`}
                  color="safe"
                />
                <StatCard
                  icon={Clock}
                  label="平均延迟"
                  value={`${evidenceOverview.avgLatencyMs.toFixed(0)}ms`}
                  color="warning"
                />
                <StatCard
                  icon={Cpu}
                  label="调用类型数"
                  value={Object.keys(evidenceOverview.callTypeBreakdown).length}
                  color="info"
                />
              </div>

              {/* 调用类型分布 */}
              <div className="app-card p-4">
                <div className="flex items-center gap-2 mb-3">
                  <BarChart3 size={16} className="text-primary" aria-hidden />
                  <span className="text-sm font-bold text-ink">调用类型分布</span>
                </div>
                <div className="space-y-2">
                  {Object.entries(evidenceOverview.callTypeBreakdown)
                    .sort(([, a], [, b]) => b - a)
                    .map(([type, count]) => {
                      const maxCount = Math.max(...Object.values(evidenceOverview.callTypeBreakdown));
                      const percentage = maxCount > 0 ? (count / maxCount) * 100 : 0;
                      return (
                        <div key={type} className="flex items-center gap-3">
                          <span className="text-xs font-semibold text-ink w-20 truncate">{type}</span>
                          <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-primary to-primary-deep transition-all"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                          <span className="text-xs font-bold text-primary w-10 text-right">{count}</span>
                        </div>
                      );
                    })}
                </div>
              </div>

              {/* 数据日期范围 */}
              <div className="app-card p-3 flex items-center gap-3 text-xs text-subtext">
                <Clock size={12} aria-hidden />
                <span>数据范围：{evidenceOverview.dateRange.from} ~ {evidenceOverview.dateRange.to}</span>
              </div>
            </>
          ) : (
            <div className="app-card p-8 text-center">
              <FileText size={32} className="text-subtext/30 mx-auto mb-2" />
            </div>
          )}
        </div>
      )}

      {/* ========== 调用日志 ========== */}
      {activeTab === 'logs' && (
        <div className="space-y-3">
          {/* 筛选 */}
          {evidenceOverview && Object.keys(evidenceOverview.callTypeBreakdown).length > 0 && (
            <div className="flex items-center gap-2 flex-wrap">
              <Filter size={14} className="text-subtext" aria-hidden />
              <button
                onClick={() => setFilterCallType(null)}
                className={`px-2 py-1 rounded-md text-xs font-semibold transition-colors ${
                  filterCallType === null ? 'bg-primary text-white' : 'bg-white/60 text-subtext hover:text-ink'
                }`}
              >
                全部
              </button>
              {Object.keys(evidenceOverview.callTypeBreakdown).map((type) => (
                <button
                  key={type}
                  onClick={() => setFilterCallType(type)}
                  className={`px-2 py-1 rounded-md text-xs font-semibold transition-colors ${
                    filterCallType === type ? 'bg-primary text-white' : 'bg-white/60 text-subtext hover:text-ink'
                  }`}
                >
                  {type} ({evidenceOverview.callTypeBreakdown[type]})
                </button>
              ))}
            </div>
          )}

          {/* 日志列表 */}
          {aiLogs.length > 0 ? (
            <div className="space-y-2">
              {aiLogs
                .filter((log) => !filterCallType || log.callType === filterCallType)
                .map((log) => (
                  <div key={log.id} className="app-card p-3.5 text-left">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge variant={log.isSuccess ? 'success' : 'danger'} size="sm">
                          {log.isSuccess ? '成功' : '失败'}
                        </Badge>
                        <Badge variant="outline" size="sm">{log.callType}</Badge>
                        <Badge variant="ghost" size="sm">
                          v{log.promptVersion}
                        </Badge>
                      </div>
                      <span className="text-xs text-subtext">
                        {new Date(log.createdAt).toLocaleString('zh-CN')}
                      </span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="font-semibold text-ink">输入:</span>
                        <span className="text-subtext ml-1 line-clamp-1">{log.inputSummary}</span>
                      </div>
                      <div>
                        <span className="font-semibold text-ink">输出:</span>
                        <span className="text-subtext ml-1 line-clamp-1">{log.outputSummary}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 mt-2 text-xs text-subtext">
                      <span>模型: {log.modelUsed}</span>
                      <span>延迟: {log.latencyMs}ms</span>
                      {log.tokenCount && <span>Token: {log.tokenCount}</span>}
                    </div>
                    {log.errorMessage && (
                      <div className="mt-1.5 p-2 rounded-md bg-red-50/60 text-xs text-red-700">
                        <span className="font-semibold">错误:</span> {log.errorMessage}
                      </div>
                    )}
                  </div>
                ))}
            </div>
          ) : (
            <div className="app-card p-8 text-center">
              <Search size={32} className="text-subtext/30 mx-auto mb-2" />
            </div>
          )}
        </div>
      )}

      {/* ========== Prompt 版本 ========== */}
      {activeTab === 'prompts' && (
        <div className="space-y-3">
          {(evidenceOverview?.promptVersions?.length ?? 0) > 0 ? (
            (evidenceOverview?.promptVersions ?? []).map((version, i) => (
              <div key={i} className="app-card p-3.5 text-left">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sparkles size={14} className="text-primary" aria-hidden />
                    <span className="text-sm font-bold text-ink">{version}</span>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="app-card p-8 text-center">
              <FileText size={32} className="text-subtext/30 mx-auto mb-2" />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/** 统计卡片 */
function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ComponentType<{ size?: number; className?: string }>;
  label: string;
  value: string | number;
  color: 'primary' | 'safe' | 'warning' | 'info';
}) {
  const colorMap = {
    primary: { bg: 'bg-primary/10', text: 'text-primary' },
    safe: { bg: 'bg-emerald-500/10', text: 'text-emerald-600' },
    warning: { bg: 'bg-amber-500/10', text: 'text-amber-600' },
    info: { bg: 'bg-blue-500/10', text: 'text-blue-600' },
  }[color];

  return (
    <div className="app-card p-3.5">
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-7 h-7 rounded-lg ${colorMap.bg} flex items-center justify-center`}>
          <Icon size={14} className={colorMap.text} aria-hidden />
        </div>
        <span className="text-xs text-subtext">{label}</span>
      </div>
      <div className={`text-xl font-extrabold ${colorMap.text}`}>{value}</div>
    </div>
  );
}
