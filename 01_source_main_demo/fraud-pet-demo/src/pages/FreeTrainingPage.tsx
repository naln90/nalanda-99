import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, Filter, PlayCircle, RefreshCw, Search } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import type { TrainingTask } from '../types';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';
import { Skeleton } from '../components/ui/Skeleton';
import { useToast } from '../components/ui/Toast';

export default function FreeTrainingPage() {
  const navigate = useNavigate();
  const { loadTrainingTasks, trainingTasks } = useAppStore();
  const { error: showError } = useToast();

  const [fraudTypeFilter, setFraudTypeFilter] = useState<string>('全部');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('全部');
  const [searchKeyword, setSearchKeyword] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      await loadTrainingTasks();
    } catch (e) {
      const msg = e instanceof Error ? e.message : '训练任务加载失败';
      setError(msg);
      showError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchTasks();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fraudTypes = useMemo(
    () => ['全部', ...Array.from(new Set(trainingTasks.map((t) => t.fraudType)))],
    [trainingTasks],
  );
  const difficulties = ['全部', '低', '中等', '高'];

  const filteredTasks = useMemo(() => {
    const kw = searchKeyword.trim().toLowerCase();
    return trainingTasks.filter((task) => {
      if (fraudTypeFilter !== '全部' && task.fraudType !== fraudTypeFilter) return false;
      if (difficultyFilter !== '全部' && task.difficulty !== difficultyFilter) return false;
      if (kw && !task.title.toLowerCase().includes(kw) && !task.fraudType.toLowerCase().includes(kw)) return false;
      return true;
    });
  }, [trainingTasks, fraudTypeFilter, difficultyFilter, searchKeyword]);

  return (
    <div className="space-y-5">
      <div className="animate-slide-up">
        <h2 className="text-xl font-extrabold text-ink flex items-center">
          <Filter size={20} className="mr-2 text-primary" /> 自由训练
        </h2>
      </div>

      {/* 筛选器 */}
      <div className="app-card p-5 space-y-4 animate-slide-up" style={{ animationDelay: '60ms' }}>
        <div className="relative">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-subtext" />
          <input
            type="text"
            placeholder="搜索训练任务名称或诈骗类型..."
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            className="field pl-10"
          />
        </div>

        <div>
          <div className="flex flex-wrap gap-2">
            {fraudTypes.map((type) => (
              <FilterChip key={type} active={fraudTypeFilter === type} onClick={() => setFraudTypeFilter(type)}>{type}</FilterChip>
            ))}
          </div>
        </div>

        <div>
          <div className="flex flex-wrap gap-2">
            {difficulties.map((diff) => (
              <FilterChip key={diff} active={difficultyFilter === diff} onClick={() => setDifficultyFilter(diff)}>
                {diff === '全部' ? '全部' : diff + '难度'}
              </FilterChip>
            ))}
          </div>
        </div>
      </div>

      {/* 加载态 */}
      {loading && (
        <div>
          <div className="h-4 w-32 mb-3 skeleton rounded" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="app-card p-5">
                <div className="flex justify-between mb-3">
                  <Skeleton className="h-5 w-2/3" />
                  <Skeleton rounded="full" className="h-5 w-14" />
                </div>
                <div className="space-y-2 mb-4">
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-full" />
                </div>
                <div className="flex justify-between pt-3 border-t border-slate-50">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton rounded="full" className="h-7 w-24" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 错误态 */}
      {!loading && error && (
        <div className="app-card">
          <EmptyState
            icon={<AlertCircle size={28} />}
            title="训练任务加载失败"
            description={error}
            action={
              <Button onClick={fetchTasks} variant="default" size="sm">
                <RefreshCw size={14} className="mr-1.5" /> 重新加载
              </Button>
            }
          />
        </div>
      )}

      {/* 任务列表 */}
      {!loading && !error && (
        <div>
          <p className="text-sm text-subtext mb-3">
            共 <span className="font-bold text-ink">{filteredTasks.length}</span> 个训练任务
          </p>
          {filteredTasks.length === 0 ? (
            <div className="app-card">
              <EmptyState
                icon={<Search size={28} />}
                title="没有符合条件的训练任务"
                action={
                  <Button
                    onClick={() => {
                      setFraudTypeFilter('全部');
                      setDifficultyFilter('全部');
                      setSearchKeyword('');
                    }}
                    variant="ghost"
                    size="sm"
                  >
                    清空筛选
                  </Button>
                }
              />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredTasks.map((task, idx) => (
                <TaskCard key={task.id} task={task} onStart={() => navigate(`/training/session/${task.id}`)} delay={idx * 50} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function FilterChip({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
        active
          ? 'bg-gradient-to-r from-primary to-primary-deep text-white shadow-glow-sm'
          : 'bg-slate-50 text-subtext hover:bg-slate-100 hover:text-ink'
      }`}
    >
      {children}
    </button>
  );
}

function TaskCard({ task, onStart, delay }: { task: TrainingTask; onStart: () => void; delay: number }) {
  return (
    <div className="app-card app-card-hover p-5 flex flex-col justify-between animate-slide-up" style={{ animationDelay: `${delay}ms` }}>
      <div>
        <div className="flex justify-between items-start mb-3">
          <h3 className="font-bold text-ink leading-tight pr-2">{task.title}</h3>
          <span className={`chip border whitespace-nowrap ${
            task.riskLevel === '高风险' ? 'bg-rose-50 text-danger border-rose-100' :
            task.riskLevel === '中风险' ? 'bg-amber-50 text-warning border-amber-100' : 'bg-primary-soft text-primary border-primary/15'
          }`}>{task.riskLevel}</span>
        </div>
        <div className="space-y-1.5 mb-4">
          <p className="text-xs text-subtext flex justify-between"><span>诈骗类型</span> <span className="text-ink font-medium">{task.fraudType}</span></p>
          <p className="text-xs text-subtext flex justify-between"><span>预计用时</span> <span className="text-ink font-medium">{task.duration}</span></p>
          <p className="text-xs text-subtext flex justify-between"><span>难度</span> <span className="text-ink font-medium">{task.difficulty}</span></p>
        </div>
      </div>
      <div className="flex items-center justify-between pt-3 border-t border-slate-50">
        <span className="text-growth font-extrabold">+{task.reward} <span className="text-xs font-normal text-subtext">成长值</span></span>
        <button onClick={onStart} className="btn-primary px-3 py-1.5 text-xs flex items-center gap-1">
          <PlayCircle size={14} /> 开始训练
        </button>
      </div>
    </div>
  );
}
