import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BookCopy,
  Bookmark,
  Eye,
  FileText,
  Heart,
  Loader2,
  MessageSquare,
  Search,
  Sparkles,
  Star,
  UsersRound,
} from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/useAppStore';
import type { LearningTemplate, MarketListing, MarketComment } from '../types/learning';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useToast } from '../components/ui/Toast';
import { useAsync } from '../hooks/useAsync';
import { AsyncBoundary } from '../components/ui/AsyncBoundary';

type MarketTab = 'all' | 'plan' | 'artifact';

interface InteractionState {
  liked: boolean;
  favorited: boolean;
  myRating: number;
  commentsOpen: boolean;
  comments: MarketComment[];
  commentText: string;
  commentsLoading: boolean;
}

const emptyInteraction = (): InteractionState => ({
  liked: false,
  favorited: false,
  myRating: 0,
  commentsOpen: false,
  comments: [],
  commentText: '',
  commentsLoading: false,
});

export default function LearningMarketPage() {
  const navigate = useNavigate();
  const ownerId = useAppStore((state) => state.currentUser?.ownerId) ?? '';
  const { success, error: showError } = useToast();
  const [tab, setTab] = useState<MarketTab>('all');
  const [query, setQuery] = useState('');
  const [reuseId, setReuseId] = useState<string | null>(null);
  const [interactions, setInteractions] = useState<Record<string, InteractionState>>({});

  const { data, loading, error, refetch } = useAsync(
    () => api.getLearningMarket(tab),
    { deps: [tab] },
  );
  const templates = data?.templates ?? [];
  const [listings, setListings] = useState<MarketListing[]>([]);
  useEffect(() => {
    setListings(data?.listings ?? []);
  }, [data]);

  const getInteraction = (id: string): InteractionState =>
    interactions[id] ?? emptyInteraction();

  const patchInteraction = (id: string, patch: Partial<InteractionState>) =>
    setInteractions((prev) => ({ ...prev, [id]: { ...emptyInteraction(), ...prev[id], ...patch } }));

  const filteredTemplates = useMemo(
    () =>
      templates.filter((item) =>
        `${item.title}${item.theme}${item.tags.join('')}`.toLowerCase().includes(query.toLowerCase()),
      ),
    [query, templates],
  );
  const filteredListings = useMemo(
    () =>
      listings.filter((item) =>
        `${item.title}${item.theme}${item.tags.join('')}`.toLowerCase().includes(query.toLowerCase()),
      ),
    [listings, query],
  );

  const reuse = async (resourceId: string) => {
    setReuseId(resourceId);
    try {
      const result = await api.reuseLearningMarketResource(resourceId, ownerId);
      success(result.message);
      navigate('/learning/workspace');
    } catch (err) {
      showError(err instanceof Error ? err.message : '任务包复用失败');
    } finally {
      setReuseId(null);
    }
  };

  const toggleLike = async (listing: MarketListing) => {
    try {
      const res = await api.marketLike(listing.id, ownerId);
      setListings((prev) =>
        prev.map((l) => (l.id === listing.id ? { ...l, likes: res.likes } : l)),
      );
      patchInteraction(listing.id, { liked: res.liked });
    } catch (err) {
      showError(err instanceof Error ? err.message : '点赞失败');
    }
  };

  const toggleFavorite = async (listing: MarketListing) => {
    try {
      const res = await api.marketFavorite(listing.id, ownerId);
      setListings((prev) =>
        prev.map((l) => (l.id === listing.id ? { ...l, favorites: res.favorites } : l)),
      );
      patchInteraction(listing.id, { favorited: res.favorited });
    } catch (err) {
      showError(err instanceof Error ? err.message : '收藏失败');
    }
  };

  const rateListing = async (listing: MarketListing, score: number) => {
    try {
      const res = await api.marketRate(listing.id, ownerId, score);
      setListings((prev) =>
        prev.map((l) =>
          l.id === listing.id ? { ...l, ratingAvg: res.ratingAvg, ratingCount: res.ratingCount } : l,
        ),
      );
      patchInteraction(listing.id, { myRating: score });
      success('评分已提交');
    } catch (err) {
      showError(err instanceof Error ? err.message : '评分失败');
    }
  };

  const toggleComments = async (listing: MarketListing) => {
    const it = getInteraction(listing.id);
    if (it.commentsOpen) {
      patchInteraction(listing.id, { commentsOpen: false });
      return;
    }
    patchInteraction(listing.id, { commentsOpen: true, commentsLoading: true });
    try {
      const res = await api.getMarketComments(listing.id);
      patchInteraction(listing.id, { comments: res.comments, commentsLoading: false });
    } catch (err) {
      patchInteraction(listing.id, { commentsLoading: false });
      showError(err instanceof Error ? err.message : '评论加载失败');
    }
  };

  const submitComment = async (listing: MarketListing) => {
    const it = getInteraction(listing.id);
    const content = it.commentText.trim();
    if (!content) {
      showError('评论内容不能为空');
      return;
    }
    try {
      const created = await api.addMarketComment(listing.id, ownerId, content);
      patchInteraction(listing.id, {
        comments: [created, ...getInteraction(listing.id).comments],
        commentText: '',
      });
      success('评论已发布');
    } catch (err) {
      showError(err instanceof Error ? err.message : '评论发布失败');
    }
  };

  return (
    <div className="space-y-5 animate-slide-up">
      <section className="rounded-3xl border border-cyan-200/70 bg-gradient-to-br from-cyan-50 via-white to-violet-50 p-6 shadow-card">
        <div>
          <Badge className="border-cyan-200/70 bg-white/80 text-cyan-700">AI学习集市 · 资源广场</Badge>
          <h1 className="mt-3 text-2xl font-extrabold text-ink sm:text-3xl">让任务包和学习成果持续流转</h1>
          <div className="mt-4 flex max-w-xl items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
            <Search className="shrink-0 text-subtext" size={17} />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="min-w-0 flex-1 bg-transparent text-sm text-ink outline-none placeholder:text-subtext/60"
              placeholder="搜索主题、任务包或成果"
            />
          </div>
        </div>
      </section>

      <div className="flex flex-wrap gap-2">
        {([
          ['all', '全部资源'],
          ['plan', '任务包'],
          ['artifact', '学习成果'],
        ] as Array<[MarketTab, string]>).map(([value, label]) => (
          <button
            key={value}
            onClick={() => setTab(value)}
            className={`rounded-full px-4 py-2 text-xs font-bold transition ${
              tab === value ? 'bg-primary text-white shadow-glow-sm' : 'border border-border bg-white text-subtext hover:text-primary'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <AsyncBoundary
        loading={loading}
        error={error}
        data={data}
        onRetry={refetch}
        loadingFallback={
          <div className="flex min-h-72 items-center justify-center text-subtext">
            <Loader2 className="mr-2 animate-spin" size={20} />正在整理优质学习资源...
          </div>
        }
      >
        {() => (
        <>
          {filteredTemplates.length > 0 && (
            <section>
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-extrabold text-ink">标准化任务包</h2>
                  <p className="text-xs text-subtext">模板可一键复用，复制后自由微调，不影响原始版本。</p>
                </div>
                <Badge variant="info"><Sparkles size={12} />AI精选</Badge>
              </div>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {filteredTemplates.map((template) => (
                  <TemplateCard
                    key={template.id}
                    template={template}
                    loading={reuseId === template.id}
                    onReuse={() => reuse(template.id)}
                  />
                ))}
              </div>
            </section>
          )}

          <section>
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-extrabold text-ink">学生共创资源</h2>
                <p className="text-xs text-subtext">任务包保留复用来源，成果展示版本迭代和学习过程。</p>
              </div>
              <Badge variant="outline">{filteredListings.length}项</Badge>
            </div>
            {filteredListings.length === 0 ? (
              <div className="app-card p-8 text-center">
                <UsersRound className="mx-auto text-primary" size={36} />
                <h3 className="mt-3 font-extrabold text-ink">等待你的第一项共创资源</h3>
                <p className="mt-1 text-sm text-subtext">在学习工作台分享任务包，或在成果工坊发布学习成果。</p>
                <div className="mt-4 flex justify-center gap-2">
                  <Button variant="outline" onClick={() => navigate('/learning/workspace')}>分享任务包</Button>
                  <Button onClick={() => navigate('/learning/artifacts')}>发布成果</Button>
                </div>
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {filteredListings.map((listing) => (
                  <ListingCard
                    key={listing.id}
                    listing={listing}
                    interaction={getInteraction(listing.id)}
                    onReuse={() => reuse(listing.id)}
                    onLike={() => toggleLike(listing)}
                    onFavorite={() => toggleFavorite(listing)}
                    onRate={(score) => rateListing(listing, score)}
                    onToggleComments={() => toggleComments(listing)}
                    onCommentTextChange={(text) => patchInteraction(listing.id, { commentText: text })}
                    onSubmitComment={() => submitComment(listing)}
                  />
                ))}
              </div>
            )}
          </section>
        </>
        )}
      </AsyncBoundary>
    </div>
  );
}

function TemplateCard({
  template,
  loading,
  onReuse,
}: {
  template: LearningTemplate;
  loading: boolean;
  onReuse: () => void;
}) {
  return (
    <article className="app-card group overflow-hidden p-4 transition hover:-translate-y-1 hover:shadow-glow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-soft to-violet-100 text-primary">
          <BookCopy size={21} />
        </div>
        <div className="flex gap-1.5">
          {template.featured && <Badge variant="info" size="sm">反诈示范</Badge>}
          <Badge variant="outline" size="sm">{template.difficulty}</Badge>
        </div>
      </div>
      <h3 className="mt-3 text-base font-extrabold text-ink">{template.title}</h3>
      <p className="mt-1 line-clamp-3 text-xs leading-5 text-subtext">{template.summary}</p>
      <div className="mt-3 flex flex-wrap gap-1.5">
        {template.tags.map((tag) => <Badge key={tag} variant="secondary" size="sm">{tag}</Badge>)}
      </div>
      <div className="mt-4 grid grid-cols-3 gap-2 text-center">
        <MiniMetric label="周期" value={`${template.periodDays}天`} />
        <MiniMetric label="每日" value={`${template.dailyMinutes}分`} />
        <MiniMetric label="已复用" value={String(template.reuseCount)} />
      </div>
      <Button fullWidth className="mt-4" onClick={onReuse} loading={loading}>
        <BookCopy size={15} />一键复用并修改
      </Button>
    </article>
  );
}

function ListingCard({
  listing,
  interaction,
  onReuse,
  onLike,
  onFavorite,
  onRate,
  onToggleComments,
  onCommentTextChange,
  onSubmitComment,
}: {
  listing: MarketListing;
  interaction: InteractionState;
  onReuse: () => void;
  onLike: () => void;
  onFavorite: () => void;
  onRate: (score: number) => void;
  onToggleComments: () => void;
  onCommentTextChange: (text: string) => void;
  onSubmitComment: () => void;
}) {
  const isPlan = listing.resourceType === 'plan';
  return (
    <article className="app-card p-4">
      <div className="flex items-start justify-between gap-3">
        <div className={`flex h-10 w-10 items-center justify-center rounded-2xl ${isPlan ? 'bg-primary-soft text-primary' : 'bg-amber-50 text-amber-600'}`}>
          {isPlan ? <BookCopy size={19} /> : <FileText size={19} />}
        </div>
        <Badge variant={isPlan ? 'info' : 'warning'} size="sm">{isPlan ? '任务包' : '学习成果'}</Badge>
      </div>
      <h3 className="mt-3 text-sm font-extrabold text-ink">{listing.title}</h3>
      <p className="mt-1 line-clamp-3 text-xs leading-5 text-subtext">{listing.summary}</p>
      <div className="mt-3 flex flex-wrap gap-1.5">
        {listing.tags.map((tag) => <Badge key={tag} variant="secondary" size="sm">{tag}</Badge>)}
      </div>

      {/* 评分概览 */}
      <div className="mt-3 flex items-center gap-1 text-[11px] text-amber-500">
        <Star size={12} className={listing.ratingAvg ? 'fill-amber-400 text-amber-400' : ''} />
        <span>{listing.ratingAvg ? listing.ratingAvg.toFixed(1) : '暂无评分'}</span>
        {listing.ratingCount ? <span className="text-subtext">· {listing.ratingCount} 人评</span> : null}
      </div>

      {/* 互动操作栏 */}
      <div className="mt-3 flex items-center gap-3 text-[11px] text-subtext">
        <button
          type="button"
          onClick={onLike}
          aria-pressed={interaction.liked}
          className={`inline-flex items-center gap-1 transition-colors ${interaction.liked ? 'text-rose-500' : 'hover:text-rose-500'}`}
        >
          <Heart size={13} className={interaction.liked ? 'fill-rose-500' : ''} />{listing.likes}
        </button>
        <button
          type="button"
          onClick={onFavorite}
          aria-pressed={interaction.favorited}
          className={`inline-flex items-center gap-1 transition-colors ${interaction.favorited ? 'text-primary' : 'hover:text-primary'}`}
        >
          <Bookmark size={13} className={interaction.favorited ? 'fill-primary' : ''} />{listing.favorites}
        </button>
        <span className="inline-flex items-center gap-1"><Eye size={13} />{listing.reuseCount}</span>
        <button
          type="button"
          onClick={onToggleComments}
          aria-expanded={interaction.commentsOpen}
          className="ml-auto inline-flex items-center gap-1 hover:text-primary"
        >
          <MessageSquare size={13} />{interaction.comments.length || '评论'}
        </button>
      </div>

      {/* 我的评分 */}
      <div className="mt-2 flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onRate(s)}
            aria-label={`评 ${s} 分`}
            className="transition-transform hover:scale-110"
          >
            <Star
              size={15}
              className={s <= interaction.myRating ? 'fill-amber-400 text-amber-400' : 'text-slate-300'}
            />
          </button>
        ))}
      </div>

      {/* 评论区 */}
      {interaction.commentsOpen && (
        <div className="mt-3 rounded-xl border border-border bg-muted/40 p-3 space-y-2">
          {interaction.commentsLoading ? (
            <div className="flex items-center gap-2 text-[11px] text-subtext"><Loader2 size={13} className="animate-spin" />加载中...</div>
          ) : interaction.comments.length === 0 ? (
            <p className="text-[11px] text-subtext">还没有评论，来抢沙发～</p>
          ) : (
            interaction.comments.map((c) => (
              <div key={c.id} className="text-[11px] leading-5">
                <span className="font-semibold text-ink">{c.ownerId.slice(-6)}</span>
                <span className="ml-2 text-ink/90">{c.content}</span>
                <span className="ml-2 text-subtext">{new Date(c.createdAt).toLocaleString('zh-CN', { hour12: false })}</span>
              </div>
            ))
          )}
          <div className="flex items-center gap-2 pt-1">
            <input
              value={interaction.commentText}
              onChange={(e) => onCommentTextChange(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') onSubmitComment(); }}
              placeholder="说点什么..."
              className="min-w-0 flex-1 rounded-lg border border-border bg-white px-2.5 py-1.5 text-[12px] outline-none focus:border-primary"
            />
            <Button size="sm" variant="outline" onClick={onSubmitComment}>发送</Button>
          </div>
        </div>
      )}

      {isPlan ? (
        <Button fullWidth className="mt-4" variant="outline" onClick={onReuse}>
          <BookCopy size={14} />复用任务包
        </Button>
      ) : (
        <Button fullWidth className="mt-4" variant="outline">
          <Eye size={14} />查看成果迭代
        </Button>
      )}
    </article>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-muted/60 px-2 py-2">
      <div className="text-xs font-extrabold text-ink">{value}</div>
      <div className="mt-0.5 text-[9px] text-subtext">{label}</div>
    </div>
  );
}
