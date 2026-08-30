import { useAsync } from '../hooks/useAsync';
import { AsyncBoundary } from '../components/ui/AsyncBoundary';
import { useNavigate } from 'react-router-dom';
import {
  BookCopy,
  FileText,
  Lightbulb,
  Loader2,
  Repeat,
  Sparkles,
  Star,
  Target,
} from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/useAppStore';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

export default function RecommendPage() {
  const navigate = useNavigate();
  const ownerId = useAppStore((state) => state.currentUser?.ownerId) ?? '';

  const {
    data: recData,
    loading: recLoading,
    error: recError,
    refetch: recRefetch,
  } = useAsync(() => api.recommendMarket(ownerId), { deps: [ownerId] });
  const recs = recData?.recommendations ?? [];
  const {
    data: reminder,
    loading: remLoading,
    error: remError,
    refetch: remRefetch,
  } = useAsync(() => api.studyReminders(ownerId), { deps: [ownerId] });

  return (
    <div className="space-y-5 animate-slide-up">
      <section className="rounded-3xl border border-amber-200/70 bg-gradient-to-br from-amber-50 via-white to-orange-50 p-6 shadow-card">
        <div>
          <Badge className="border-amber-200/70 bg-white/80 text-amber-700">个性化推荐与学习督促</Badge>
          <h1 className="mt-3 text-2xl font-extrabold text-ink sm:text-3xl">懂你的学习节奏</h1>
        </div>
      </section>

      {/* 个性化推荐 */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Lightbulb size={16} className="text-primary" />
            <h2 className="text-lg font-extrabold text-ink">为你推荐</h2>
          </div>
          <Badge variant="info"><Sparkles size={12} />按主题匹配</Badge>
        </div>
        <AsyncBoundary
          loading={recLoading}
          error={recError}
          data={recData}
          isEmpty={(d) => d.recommendations.length === 0}
          onRetry={recRefetch}
          loadingFallback={
            <div className="flex min-h-40 items-center justify-center text-subtext">
              <Loader2 className="mr-2 animate-spin" size={20} />正在匹配最适合你的资源...
            </div>
          }
          emptyFallback={
            <div className="app-card p-8 text-center text-subtext">
              <Sparkles className="mx-auto text-primary" size={34} />
              <h3 className="mt-3 font-extrabold text-ink">先设定学习目标，推荐更精准</h3>
              <Button className="mt-4" onClick={() => navigate('/learning/goal')}>去发布目标</Button>
            </div>
          }
        >
          {() => (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {recs.map((r) => {
              const isPlan = r.theme === 'plan';
              return (
                <article key={r.id} className="app-card p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-2xl ${isPlan ? 'bg-primary-soft text-primary' : 'bg-amber-50 text-amber-600'}`}>
                      {isPlan ? <BookCopy size={19} /> : <FileText size={19} />}
                    </div>
                    <Badge variant={r.matchScore > 0 ? 'info' : 'outline'} size="sm">匹配 {r.matchScore}</Badge>
                  </div>
                  <h3 className="mt-3 text-sm font-extrabold text-ink">{r.title}</h3>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {r.tags.map((t) => <Badge key={t} variant="secondary" size="sm">{t}</Badge>)}
                  </div>
                  <div className="mt-3 flex items-center gap-3 text-[11px] text-subtext">
                    <Stars value={r.ratingAvg} />
                    <span className="inline-flex items-center gap-1"><Star size={12} />{r.likes}</span>
                  </div>
                </article>
              );
            })}
          </div>
          )}
        </AsyncBoundary>
      </section>

      {/* 学习督促 */}
      <section>
        <div className="mb-3 flex items-center gap-1.5">
          <Target size={16} className="text-primary" />
          <h2 className="text-lg font-extrabold text-ink">学习督促清单</h2>
        </div>
        <AsyncBoundary
          loading={remLoading}
          error={remError}
          data={reminder}
          onRetry={remRefetch}
          loadingFallback={
            <div className="flex min-h-40 items-center justify-center text-subtext">
              <Loader2 className="mr-2 animate-spin" size={20} />汇总你的学习进度...
            </div>
          }
        >
          {(d) => {
            const reminder = d;
            return (
          <div className="grid gap-4 md:grid-cols-3">
            {/* 待办任务 */}
            <div className="app-card p-4">
              <h3 className="mb-2 flex items-center gap-1.5 text-sm font-extrabold text-ink">
                <BookCopy size={14} className="text-primary" />待办任务（{reminder?.pendingItems.length ?? 0}）
                <p className="text-xs text-subtext">当前没有待办任务，保持节奏！</p>
              </h3>
              {(reminder?.pendingItems.length ?? 0) === 0 ? null
 : (
                <ul className="space-y-2">
                  {reminder!.pendingItems.map((it) => (
                    <li key={it.itemId} className="rounded-xl border border-border bg-white px-3 py-2">
                      <p className="text-sm font-semibold text-ink truncate">{it.title}</p>
                      <p className="mt-0.5 text-[10px] text-subtext">第 {it.dueDay} 天 · {it.status === 'in_progress' ? '进行中' : '未开始'}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* 复训提醒 */}
            <div className="app-card p-4">
              <h3 className="mb-2 flex items-center gap-1.5 text-sm font-extrabold text-ink">
                <Repeat size={14} className="text-amber-500" />复训提醒（{reminder?.retrainTasks.length ?? 0}）
                <p className="text-xs text-subtext">暂无待复训内容。</p>
              </h3>
              {(reminder?.retrainTasks.length ?? 0) === 0 ? null
 : (
                <ul className="space-y-2">
                  {reminder!.retrainTasks.map((rt) => (
                    <li key={rt.id} className="rounded-xl border border-border bg-white px-3 py-2">
                      <p className="text-sm font-semibold text-ink truncate">{rt.fraudType}</p>
                      <p className="mt-0.5 text-[10px] text-subtext">第 {rt.attempt} 次复训 · {new Date(rt.scheduledAt).toLocaleDateString('zh-CN')}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* 薄弱维度 */}
            <div className="app-card p-4">
              <h3 className="mb-2 flex items-center gap-1.5 text-sm font-extrabold text-ink">
                <Target size={14} className="text-rose-500" />薄弱维度（{reminder?.weakDimensions.length ?? 0}）
                <p className="text-xs text-subtext">暂无可提示的薄弱维度</p>
              </h3>
              {(reminder?.weakDimensions.length ?? 0) === 0 ? null
 : (
                <div className="flex flex-wrap gap-2">
                  {reminder!.weakDimensions.map((d) => (
                    <span key={d} className="rounded-full bg-rose-50 px-3 py-1 text-[12px] font-semibold text-rose-600">{d}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
            );
          }}
        </AsyncBoundary>
      </section>
    </div>
  );
}

function Stars({ value }: { value: number | null }) {
  if (!value) {
    return <span className="inline-flex items-center gap-1 text-subtext">暂无评分</span>;
  }
  return (
    <span className="inline-flex items-center gap-1 text-amber-500">
      <Star size={12} className="fill-amber-400 text-amber-400" />
      {value.toFixed(1)}
    </span>
  );
}
