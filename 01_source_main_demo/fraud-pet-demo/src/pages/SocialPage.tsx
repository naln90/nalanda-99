import { useCallback, useEffect, useState } from 'react';
import {
  Check,
  Globe2,
  Loader2,
  Lock,
  Trash2,
  UserPlus,
  Users,
  UsersRound,
} from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/useAppStore';
import type { ArtifactSummary } from '../types/learning';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useToast } from '../components/ui/Toast';

type SocialTab = 'friends' | 'privacy';

const VISIBILITY_META: Record<string, { label: string; icon: typeof Globe2; cls: string }> = {
  public: { label: '公开', icon: Globe2, cls: 'text-emerald-600 bg-emerald-50' },
  friends: { label: '仅好友', icon: UsersRound, cls: 'text-primary bg-primary-soft' },
  private: { label: '私密', icon: Lock, cls: 'text-subtext bg-muted' },
};

export default function SocialPage() {
  const ownerId = useAppStore((state) => state.currentUser?.ownerId) ?? '';
  const { success, error: showError } = useToast();

  const [tab, setTab] = useState<SocialTab>('friends');
  const [friends, setFriends] = useState<string[]>([]);
  const [pending, setPending] = useState<string[]>([]);
  const [requestsInput, setRequestsInput] = useState('');
  const [loading, setLoading] = useState(true);

  const [artifacts, setArtifacts] = useState<ArtifactSummary[]>([]);
  const [artifactsLoading, setArtifactsLoading] = useState(false);

  const loadFriends = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.listFriends(ownerId);
      setFriends(res.friends);
      setPending(res.pendingRequests);
    } catch (err) {
      showError(err instanceof Error ? err.message : '好友列表加载失败');
    } finally {
      setLoading(false);
    }
  }, [ownerId, showError]);

  const loadArtifacts = useCallback(async () => {
    setArtifactsLoading(true);
    try {
      // viewerId = 当前用户：后端按 公开/仅好友/私密 三级过滤，私密成果对他人不可见
      const res = await api.listArtifacts('', ownerId);
      setArtifacts(res.artifacts);
    } catch (err) {
      showError(err instanceof Error ? err.message : '成果加载失败');
    } finally {
      setArtifactsLoading(false);
    }
  }, [ownerId, showError]);

  useEffect(() => {
    if (tab === 'friends') void loadFriends();
    else void loadArtifacts();
  }, [tab, loadFriends, loadArtifacts]);

  const sendRequest = async () => {
    const id = requestsInput.trim();
    if (!id) {
      showError('请输入对方账号 ID');
      return;
    }
    try {
      const res = await api.friendRequest(ownerId, id);
      setRequestsInput('');
      success(res.message || '好友申请已发送');
      await loadFriends();
    } catch (err) {
      showError(err instanceof Error ? err.message : '发送申请失败');
    }
  };

  const acceptRequest = async (friendOwnerId: string) => {
    try {
      await api.friendAccept(ownerId, friendOwnerId);
      success('已添加为好友');
      await loadFriends();
    } catch (err) {
      showError(err instanceof Error ? err.message : '接受申请失败');
    }
  };

  const remove = async (friendOwnerId: string) => {
    try {
      await api.removeFriend(ownerId, friendOwnerId);
      success('已删除好友');
      await loadFriends();
    } catch (err) {
      showError(err instanceof Error ? err.message : '删除好友失败');
    }
  };

  return (
    <div className="space-y-5 animate-slide-up">
      <section className="rounded-3xl border border-rose-200/70 bg-gradient-to-br from-rose-50 via-white to-fuchsia-50 p-6 shadow-card">
        <div>
          <Badge className="border-rose-200/70 bg-white/80 text-rose-700">好友关系与成果隐私</Badge>
          <h1 className="mt-3 text-2xl font-extrabold text-ink sm:text-3xl">结伴学习 · 三级可见</h1>
        </div>
      </section>

      <div className="flex flex-wrap gap-2">
        {([
          ['friends', '好友管理'],
          ['privacy', '成果隐私广场'],
        ] as Array<[SocialTab, string]>).map(([value, label]) => (
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

      {tab === 'friends' ? (
        <div className="grid gap-4 md:grid-cols-2">
          {/* 申请与待处理 */}
          <div className="app-card p-4 space-y-3">
            <h2 className="text-sm font-extrabold text-ink">添加学习伙伴</h2>
            <div className="flex items-center gap-2">
              <input
                value={requestsInput}
                onChange={(e) => setRequestsInput(e.target.value)}
                placeholder="对方账号 ID"
                className="min-w-0 flex-1 rounded-lg border border-border bg-white px-3 py-2 text-sm outline-none focus:border-primary"
                onKeyDown={(e) => { if (e.key === 'Enter') void sendRequest(); }}
              />
              <Button size="sm" onClick={sendRequest}><UserPlus size={14} />申请</Button>
            </div>

            <div className="pt-1">
              <h3 className="mb-2 text-[12px] font-bold text-subtext">待处理申请（{pending.length}）</h3>
              {loading ? (
                <div className="flex items-center gap-2 text-sm text-subtext"><Loader2 size={16} className="animate-spin" />加载中...</div>
              ) : pending.length === 0 ? null
 : (
                <div className="space-y-2">
                  {pending.map((p) => (
                    <div key={p} className="flex items-center gap-2 rounded-xl border border-border bg-white px-3 py-2">
                      <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary-soft text-[11px] font-bold text-primary">
                        {p.slice(-2)}
                      </div>
                      <span className="min-w-0 flex-1 truncate text-sm font-semibold text-ink">{p}</span>
                      <Button size="sm" onClick={() => acceptRequest(p)}><Check size={13} />接受</Button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* 好友列表 */}
          <div className="app-card p-4">
            <h2 className="mb-3 flex items-center gap-1.5 text-sm font-extrabold text-ink">
              <Users size={15} className="text-primary" />我的好友（{friends.length}）
            </h2>
            {loading ? (
              <div className="flex items-center gap-2 text-sm text-subtext"><Loader2 size={16} className="animate-spin" />加载中...</div>
            ) : friends.length === 0 ? (
              <div className="text-center py-8">
                <UsersRound className="mx-auto text-primary" size={34} />
              </div>
            ) : (
              <div className="space-y-2">
                {friends.map((f) => (
                  <div key={f} className="flex items-center gap-2 rounded-xl border border-border bg-white px-3 py-2.5">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-primary-deep text-xs font-bold text-white">
                      {f.slice(-2)}
                    </div>
                    <span className="min-w-0 flex-1 truncate text-sm font-semibold text-ink">{f}</span>
                    <button
                      type="button"
                      onClick={() => remove(f)}
                      className="text-subtext hover:text-danger transition-colors"
                      aria-label="删除好友"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="app-card p-4">
            <h2 className="mb-1 text-sm font-extrabold text-ink">成果隐私三级过滤说明</h2>
            <p className="text-[12px] leading-5 text-subtext">
              下方为你作为查看者实际「可见」的成果列表（后端实时按作者设置的可见性过滤）：
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-600"><Globe2 size={12} />公开 · 所有人可见</span>
              <span className="inline-flex items-center gap-1 rounded-full bg-primary-soft px-2.5 py-1 text-[11px] font-semibold text-primary"><UsersRound size={12} />仅好友 · 互加好友可见</span>
              <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2.5 py-1 text-[11px] font-semibold text-subtext"><Lock size={12} />私密 · 仅自己可见（他人列表自动隐藏）</span>
            </div>
          </div>

          {artifactsLoading ? (
            <div className="flex min-h-60 items-center justify-center text-subtext">
              <Loader2 className="mr-2 animate-spin" size={20} />加载可见成果...
            </div>
          ) : artifacts.length === 0 ? (
            <div className="app-card p-10 text-center text-subtext">
              <Lock className="mx-auto text-primary" size={34} />
              <h3 className="mt-3 font-extrabold text-ink">暂无可见成果</h3>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {artifacts.map((a) => {
                const meta = VISIBILITY_META[a.visibility] ?? VISIBILITY_META.private;
                const Icon = meta.icon;
                return (
                  <article key={a.id} className="app-card p-4">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-sm font-extrabold text-ink truncate">{a.title}</h3>
                      <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold ${meta.cls}`}>
                        <Icon size={11} />{meta.label}
                      </span>
                    </div>
                    <p className="mt-1 text-[11px] text-subtext">
                      {a.artifactType} · 作者 {a.ownerId.slice(-6)} · {new Date(a.createdAt).toLocaleDateString('zh-CN')}
                    </p>
                  </article>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
