import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, Award, Crown, Info, Medal, RefreshCw, TrendingUp } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { getPetEmoji } from '../lib/pet-utils';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';
import { Skeleton } from '../components/ui/Skeleton';
import { useToast } from '../components/ui/Toast';

export default function RankingPage() {
  const navigate = useNavigate();
  const { currentUser, loadRanking, pet, ranking } = useAppStore();
  const { error: showError } = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRanking = async () => {
    setLoading(true);
    setError(null);
    try {
      await loadRanking();
    } catch (e) {
      const msg = e instanceof Error ? e.message : '排行榜加载失败';
      setError(msg);
      showError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchRanking();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const rankings = ranking?.list ?? [];
  const myRank = ranking?.myRank;

  const top3 = rankings.slice(0, 3);
  const rest = rankings.slice(3);

  return (
    <div className="space-y-5">
      {/* 标题 */}
      <div className="rounded-2xl border border-primary/15 bg-gradient-to-r from-primary-soft/40 via-white to-indigo-50 p-6 shadow-card animate-slide-up">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center">
            <Award size={24} className="text-primary" />
          </div>
          <div>
            <h2 className="text-xl font-extrabold text-ink mb-0.5">反诈守护宠成长榜</h2>
          </div>
        </div>
      </div>

      {/* 我的排名 */}
      {pet && (
        <div className="app-card p-5 border-primary/20 animate-slide-up" style={{ animationDelay: '60ms' }}>
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-4">
              <div className="bg-primary/10 text-primary font-black px-4 py-2.5 rounded-xl shadow-sm border border-primary/15">
                第 {myRank?.rank ?? '-'} 名
              </div>
              <div className="text-sm space-y-0.5">
                <p className="text-subtext">主人 ID: <span className="font-semibold text-ink">{currentUser?.ownerId}</span></p>
                <p className="text-subtext">宠物: <span className="font-semibold text-ink">{pet.type} ({pet.petId})</span></p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-black text-growth">{pet.growthValue}</p>
              {myRank?.distanceToPrevious !== undefined && myRank.distanceToPrevious > 0 && (
                <p className="text-xs text-warning flex items-center mt-1 justify-end">
                  <TrendingUp size={12} className="mr-1" /> 距上一名差 {myRank.distanceToPrevious}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 加载态 */}
      {loading && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[0, 1, 2].map((i) => (
              <div key={i} className="app-card p-5">
                <Skeleton rounded="full" className="w-14 h-14 mx-auto mb-3" />
                <Skeleton className="h-3 w-20 mx-auto mb-2" />
                <Skeleton className="h-6 w-16 mx-auto mb-1" />
                <Skeleton className="h-3 w-24 mx-auto" />
              </div>
            ))}
          </div>
          <div className="app-card p-4 space-y-3">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        </div>
      )}

      {/* 错误态 */}
      {!loading && error && (
        <div className="app-card">
          <EmptyState
            icon={<AlertCircle size={28} />}
            title="排行榜加载失败"
            description={error}
            action={
              <Button onClick={fetchRanking} variant="default" size="sm">
                <RefreshCw size={14} className="mr-1.5" /> 重新加载
              </Button>
            }
          />
        </div>
      )}

      {/* 空状态 */}
      {!loading && !error && rankings.length === 0 && (
        <div className="app-card">
          <EmptyState
            icon={<Award size={28} />}
            title="暂无排行数据"
            action={<Button onClick={() => navigate('/training')} variant="default" size="sm">去训练</Button>}
          />
        </div>
      )}

      {/* 前三名展示 */}
      {!loading && !error && top3.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-slide-up" style={{ animationDelay: '120ms' }}>
          {top3.map((r, idx) => {
            const isMe = r.ownerId === currentUser?.ownerId;
            const config = [
              { ring: 'from-amber-300 to-yellow-500', label: '冠军', icon: Crown, iconColor: 'text-amber-500', emoji: '🏆' },
              { ring: 'from-slate-300 to-slate-400', label: '亚军', icon: Medal, iconColor: 'text-slate-500', emoji: '🥈' },
              { ring: 'from-orange-300 to-amber-600', label: '季军', icon: Medal, iconColor: 'text-orange-500', emoji: '🥉' },
            ][idx];
            const Icon = config.icon;
            return (
              <div key={r.rank} className={`relative app-card p-5 text-center ${isMe ? 'border-primary ring-2 ring-primary/20' : ''}`}>
                <div className="absolute top-3 right-3 text-2xl">{config.emoji}</div>
                <div className={`w-14 h-14 mx-auto rounded-2xl bg-gradient-to-br ${config.ring} flex items-center justify-center mb-3 shadow-glow-sm`}>
                  <Icon size={26} className="text-white" />
                </div>
                <p className="text-xs text-subtext mb-1">第 {r.rank} 名 · {config.label}</p>
                <div className="text-3xl mb-1">{getPetEmoji(r.petType)}</div>
                <p className="font-bold text-ink text-sm">{r.ownerId}{isMe && <span className="ml-1 text-xs text-primary">(我)</span>}</p>
                <p className="text-xs text-subtext mt-0.5">Lv.{r.level} · {r.petType}</p>
                <p className="text-xl font-black text-growth mt-2">{r.growthValue}</p>
              </div>
            );
          })}
        </div>
      )}

      {/* 总榜 */}
      {!loading && !error && rest.length > 0 && (
        <div className="app-card overflow-hidden animate-slide-up" style={{ animationDelay: '180ms' }}>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/80 text-subtext text-xs border-b border-slate-100">
                  <th className="p-4 font-medium pl-6">排名</th>
                  <th className="p-4 font-medium">主人 ID (脱敏)</th>
                  <th className="p-4 font-medium">宠物 ID</th>
                  <th className="p-4 font-medium">宠物类型</th>
                  <th className="p-4 font-medium">等级</th>
                  <th className="p-4 font-medium pr-6">成长值</th>
                </tr>
              </thead>
              <tbody>
                {rest.map((r) => {
                  const isMe = r.ownerId === currentUser?.ownerId;
                  return (
                    <tr key={r.rank} className={`border-b border-slate-50 hover:bg-slate-50/60 transition ${isMe ? 'bg-primary-soft/40' : ''}`}>
                      <td className="p-4 pl-6">
                        <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-slate-100 text-subtext font-bold text-sm">{r.rank}</span>
                      </td>
                      <td className="p-4 font-semibold text-ink">{r.ownerId}{isMe && <span className="ml-1 text-xs text-primary">(我)</span>}</td>
                      <td className="p-4 text-subtext">{r.petId}</td>
                      <td className="p-4 text-ink"><span className="inline-flex items-center gap-1.5">{getPetEmoji(r.petType)} {r.petType}</span></td>
                      <td className="p-4"><span className="chip bg-slate-100 text-ink">Lv.{r.level}</span></td>
                      <td className="p-4 pr-6 font-black text-growth">{r.growthValue}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 隐私提示 */}
      {!loading && !error && rankings.length > 0 && (
        <div className="rounded-xl p-4 bg-slate-50/80 border border-slate-100 flex items-start gap-3">
          <Info size={16} className="text-subtext flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-semibold text-ink mb-0.5">隐私保护说明</p>
          </div>
        </div>
      )}
    </div>
  );
}
