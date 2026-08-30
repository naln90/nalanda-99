import { useCallback, useEffect, useState } from 'react';
import {
  AlertTriangle,
  Check,
  CheckCircle2,
  Flag,
  Globe2,
  LayoutList,
  Loader2,
  Lock,
  Plus,
  Trash2,
  UserPlus,
  Users,
  UsersRound,
  XCircle,
} from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/useAppStore';
import type { ArtifactSummary, Milestone, ProjectIssue, Team, TeamMember } from '../types/learning';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useToast } from '../components/ui/Toast';

type TabKey = 'teams' | 'friends' | 'privacy';

const VISIBILITY_META: Record<string, { label: string; icon: typeof Globe2; cls: string }> = {
  public: { label: '公开', icon: Globe2, cls: 'text-emerald-600 bg-emerald-50' },
  friends: { label: '仅好友', icon: UsersRound, cls: 'text-primary bg-primary-soft' },
  private: { label: '私密', icon: Lock, cls: 'text-subtext bg-muted' },
};

const MILESTONE_STATUS: Record<string, { label: string; variant: 'info' | 'success' | 'danger' | 'outline' }> = {
  pending: { label: '待验收', variant: 'info' },
  verified: { label: '已验收', variant: 'success' },
  rejected: { label: '已驳回', variant: 'danger' },
};

const ISSUE_STATUS: Record<string, { label: string }> = {
  open: { label: '待处理' },
  in_progress: { label: '处理中' },
  resolved: { label: '已解决' },
  closed: { label: '已关闭' },
};

const TABS: Array<[TabKey, string, typeof Users]> = [
  ['teams', '协作小组', LayoutList],
  ['friends', '好友管理', UserPlus],
  ['privacy', '成果隐私广场', Lock],
];

export default function SocialCollaborationPage() {
  const [tab, setTab] = useState<TabKey>('teams');

  return (
    <div className="space-y-5 animate-slide-up">
      <section className="rounded-3xl border border-violet-200/70 bg-gradient-to-br from-violet-50 via-white to-indigo-50 p-6 shadow-card">
        <div>
          <Badge className="border-violet-200/70 bg-white/80 text-violet-700">协作与社交</Badge>
          <h1 className="mt-3 text-2xl font-extrabold text-ink sm:text-3xl">小组协作 · 好友结伴 · 隐私可控</h1>
        </div>
      </section>

      <div className="flex flex-wrap gap-2">
        {TABS.map(([value, label, Icon]) => (
          <button
            key={value}
            onClick={() => setTab(value)}
            className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-bold transition ${
              tab === value ? 'bg-primary text-white shadow-glow-sm' : 'border border-border bg-white text-subtext hover:text-primary'
            }`}
          >
            <Icon size={14} />{label}
          </button>
        ))}
      </div>

      {tab === 'teams' && <TeamPanel />}
      {tab === 'friends' && <FriendsPanel />}
      {tab === 'privacy' && <PrivacyPanel />}
    </div>
  );
}

/* ===================== 协作小组面板 ===================== */
function TeamPanel() {
  const ownerId = useAppStore((state) => state.currentUser?.ownerId) ?? '';
  const { success, error: showError } = useToast();

  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loadingTeams, setLoadingTeams] = useState(true);

  const [createName, setCreateName] = useState('');
  const [createDesc, setCreateDesc] = useState('');
  const [creating, setCreating] = useState(false);

  const [members, setMembers] = useState<TeamMember[]>([]);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [issues, setIssues] = useState<ProjectIssue[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);

  const [memberInput, setMemberInput] = useState('');
  const [memberRole, setMemberRole] = useState('成员');
  const [milestoneTitle, setMilestoneTitle] = useState('');
  const [milestoneDue, setMilestoneDue] = useState(7);
  const [issueTitle, setIssueTitle] = useState('');
  const [issueDesc, setIssueDesc] = useState('');

  const loadTeams = useCallback(async () => {
    setLoadingTeams(true);
    try {
      const res = await api.listTeams(ownerId);
      setTeams(res.teams);
      setSelectedId((prev) => (prev && res.teams.some((t) => t.id === prev) ? prev : (res.teams[0]?.id ?? null)));
    } catch (err) {
      showError(err instanceof Error ? err.message : '团队列表加载失败');
    } finally {
      setLoadingTeams(false);
    }
  }, [ownerId, showError]);

  const loadDetail = useCallback(async (teamId: string) => {
    setDetailLoading(true);
    try {
      const [m, ms, is] = await Promise.all([
        api.listTeamMembers(teamId),
        api.listMilestones(teamId),
        api.listIssues(teamId),
      ]);
      setMembers(m.members);
      setMilestones(ms.milestones);
      setIssues(is.issues);
    } catch (err) {
      showError(err instanceof Error ? err.message : '团队详情加载失败');
    } finally {
      setDetailLoading(false);
    }
  }, [showError]);

  useEffect(() => {
    void loadTeams();
  }, [loadTeams]);

  useEffect(() => {
    if (selectedId) {
      void loadDetail(selectedId);
    } else {
      setMembers([]);
      setMilestones([]);
      setIssues([]);
    }
  }, [selectedId, loadDetail]);

  const selectedTeam = teams.find((t) => t.id === selectedId) ?? null;
  const isOwner = selectedTeam?.ownerId === ownerId;

  const createTeam = async () => {
    const name = createName.trim();
    if (name.length < 2) {
      showError('团队名称至少 2 个字符');
      return;
    }
    setCreating(true);
    try {
      await api.createTeam(ownerId, name, createDesc.trim());
      setCreateName('');
      setCreateDesc('');
      success('团队已创建');
      await loadTeams();
    } catch (err) {
      showError(err instanceof Error ? err.message : '创建团队失败');
    } finally {
      setCreating(false);
    }
  };

  const addMember = async () => {
    if (!selectedId) return;
    const id = memberInput.trim();
    if (!id) {
      showError('请输入成员账号 ID');
      return;
    }
    try {
      await api.addTeamMember(selectedId, ownerId, id, memberRole);
      setMemberInput('');
      success('成员已添加');
      await loadDetail(selectedId);
    } catch (err) {
      showError(err instanceof Error ? err.message : '添加成员失败');
    }
  };

  const removeMember = async (memberOwnerId: string) => {
    if (!selectedId) return;
    try {
      await api.removeTeamMember(selectedId, memberOwnerId, ownerId);
      success('已移除成员');
      await loadDetail(selectedId);
    } catch (err) {
      showError(err instanceof Error ? err.message : '移除成员失败');
    }
  };

  const addMilestone = async () => {
    if (!selectedId) return;
    const title = milestoneTitle.trim();
    if (title.length < 2) {
      showError('节点名称至少 2 个字符');
      return;
    }
    try {
      await api.addMilestone(selectedId, ownerId, title, milestoneDue);
      setMilestoneTitle('');
      setMilestoneDue(7);
      success('节点已添加');
      await loadDetail(selectedId);
    } catch (err) {
      showError(err instanceof Error ? err.message : '添加节点失败');
    }
  };

  const verifyMilestone = async (milestoneId: number, status: 'verified' | 'rejected') => {
    if (!selectedId) return;
    try {
      await api.verifyMilestone(selectedId, milestoneId, ownerId, status);
      success(status === 'verified' ? '节点已验收' : '节点已驳回');
      await loadDetail(selectedId);
    } catch (err) {
      showError(err instanceof Error ? err.message : '验收操作失败');
    }
  };

  const addIssue = async () => {
    if (!selectedId) return;
    const title = issueTitle.trim();
    if (title.length < 2) {
      showError('问题标题至少 2 个字符');
      return;
    }
    try {
      await api.addIssue(selectedId, ownerId, title, issueDesc.trim());
      setIssueTitle('');
      setIssueDesc('');
      success('问题已记录');
      await loadDetail(selectedId);
    } catch (err) {
      showError(err instanceof Error ? err.message : '记录问题失败');
    }
  };

  const updateIssue = async (issueId: number, status: string) => {
    if (!selectedId) return;
    try {
      await api.updateIssue(selectedId, issueId, ownerId, status);
      success('问题状态已更新');
      await loadDetail(selectedId);
    } catch (err) {
      showError(err instanceof Error ? err.message : '更新问题失败');
    }
  };

  return (
    <div className="grid gap-5 lg:grid-cols-[320px_1fr]">
      <div className="space-y-4">
        <div className="app-card p-4 space-y-3">
          <h2 className="text-sm font-extrabold text-ink">创建学习小组</h2>
          <input
            value={createName}
            onChange={(e) => setCreateName(e.target.value)}
            placeholder="小组名称（如：期末复习攻坚组）"
            className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm outline-none focus:border-primary"
          />
          <input
            value={createDesc}
            onChange={(e) => setCreateDesc(e.target.value)}
            placeholder="小组简介（选填）"
            className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm outline-none focus:border-primary"
          />
          <Button fullWidth loading={creating} onClick={createTeam}>
            <Plus size={15} />创建小组
          </Button>
        </div>

        <div className="app-card p-4">
          <h2 className="mb-3 text-sm font-extrabold text-ink">我的小组</h2>
          {loadingTeams ? (
            <div className="flex items-center gap-2 text-sm text-subtext"><Loader2 size={16} className="animate-spin" />加载中...</div>
          ) : teams.length === 0 ? (
            <p className="text-sm text-subtext">还没有小组，先创建一个吧。</p>
          ) : (
            <div className="space-y-2">
              {teams.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setSelectedId(t.id)}
                  className={`w-full rounded-xl border px-3 py-2.5 text-left transition ${
                    selectedId === t.id
                      ? 'border-primary bg-primary-soft/60'
                      : 'border-border bg-white hover:border-primary/40'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Users size={15} className="text-primary" />
                    <span className="text-sm font-bold text-ink truncate">{t.name}</span>
                  </div>
                  <p className="mt-0.5 text-[11px] text-subtext">{t.ownerId === ownerId ? '我创建的' : '我参与的'}</p>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="space-y-4">
        {!selectedTeam ? (
          <div className="app-card p-10 text-center text-subtext">
            <Users className="mx-auto text-primary" size={36} />
            <h3 className="mt-3 font-extrabold text-ink">选择一个小组开始协作</h3>
            <p className="mt-1 text-sm">在左侧创建或选择小组，管理成员分工、验收节点与项目问题。</p>
          </div>
        ) : detailLoading ? (
          <div className="flex min-h-72 items-center justify-center text-subtext">
            <Loader2 className="mr-2 animate-spin" size={20} />加载小组详情...
          </div>
        ) : (
          <>
            <div className="app-card p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-extrabold text-ink">成员分工（{members.length}）</h2>
                {isOwner && <Badge variant="outline" size="sm">你是负责人</Badge>}
              </div>
              <div className="space-y-2">
                {members.map((m) => (
                  <div key={m.ownerId} className="flex items-center gap-2 rounded-xl border border-border bg-white px-3 py-2">
                    <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary-soft text-[11px] font-bold text-primary">
                      {m.ownerId.slice(-2)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold text-ink truncate">{m.ownerId}</p>
                      <p className="text-[10px] text-subtext">{m.role}</p>
                    </div>
                    {isOwner && m.ownerId !== ownerId && (
                      <button
                        type="button"
                        onClick={() => removeMember(m.ownerId)}
                        className="text-subtext hover:text-danger transition-colors"
                        aria-label="移除成员"
                      >
                        <Trash2 size={15} />
                      </button>
                    )}
                  </div>
                ))}
              </div>
              {isOwner && (
                <div className="mt-3 flex items-center gap-2">
                  <input
                    value={memberInput}
                    onChange={(e) => setMemberInput(e.target.value)}
                    placeholder="成员账号 ID"
                    className="min-w-0 flex-1 rounded-lg border border-border bg-white px-2.5 py-1.5 text-xs outline-none focus:border-primary"
                  />
                  <select
                    value={memberRole}
                    onChange={(e) => setMemberRole(e.target.value)}
                    className="rounded-lg border border-border bg-white px-2 py-1.5 text-xs outline-none focus:border-primary"
                  >
                    <option value="成员">成员</option>
                    <option value="副组长">副组长</option>
                  </select>
                  <Button size="sm" variant="outline" onClick={addMember}><Plus size={14} />添加</Button>
                </div>
              )}
            </div>

            <div className="app-card p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-extrabold text-ink">阶段节点验收（{milestones.length}）</h2>
                <Flag size={15} className="text-primary" />
              </div>
              <div className="space-y-2">
                {milestones.length === 0 && <p className="text-sm text-subtext">暂无节点，添加第一个里程碑吧。</p>}
                {milestones.map((m) => (
                  <div key={m.id} className="rounded-xl border border-border bg-white px-3 py-2.5">
                    <div className="flex items-center justify-between gap-2">
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-ink truncate">{m.title}</p>
                        <p className="text-[10px] text-subtext">第 {m.dueDay} 天 · {m.note || '—'}</p>
                      </div>
                      <Badge variant={MILESTONE_STATUS[m.status]?.variant ?? 'outline'} size="sm">
                        {MILESTONE_STATUS[m.status]?.label ?? m.status}
                      </Badge>
                    </div>
                    {isOwner && m.status === 'pending' && (
                      <div className="mt-2 flex gap-2">
                        <Button size="sm" onClick={() => verifyMilestone(m.id, 'verified')}>
                          <CheckCircle2 size={13} />验收
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => verifyMilestone(m.id, 'rejected')}>
                          <XCircle size={13} />驳回
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              {isOwner && (
                <div className="mt-3 flex items-center gap-2">
                  <input
                    value={milestoneTitle}
                    onChange={(e) => setMilestoneTitle(e.target.value)}
                    placeholder="节点名称（如：初稿评审）"
                    className="min-w-0 flex-1 rounded-lg border border-border bg-white px-2.5 py-1.5 text-xs outline-none focus:border-primary"
                  />
                  <input
                    type="number"
                    min={1}
                    max={180}
                    value={milestoneDue}
                    onChange={(e) => setMilestoneDue(Number(e.target.value) || 1)}
                    className="w-16 rounded-lg border border-border bg-white px-2 py-1.5 text-xs outline-none focus:border-primary"
                  />
                  <Button size="sm" variant="outline" onClick={addMilestone}><Plus size={14} />添加</Button>
                </div>
              )}
            </div>

            <div className="app-card p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-extrabold text-ink">项目问题跟踪（{issues.length}）</h2>
                <AlertTriangle size={15} className="text-amber-500" />
              </div>
              <div className="space-y-2">
                {issues.length === 0 && <p className="text-sm text-subtext">暂无记录的问题。</p>}
                {issues.map((it) => (
                  <div key={it.id} className="rounded-xl border border-border bg-white px-3 py-2.5">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-ink truncate">{it.title}</p>
                        {it.description && <p className="mt-0.5 text-[11px] leading-5 text-subtext">{it.description}</p>}
                        <p className="mt-0.5 text-[10px] text-subtext">{it.ownerId.slice(-6)} · {new Date(it.createdAt).toLocaleString('zh-CN', { hour12: false })}</p>
                      </div>
                      <select
                        value={it.status}
                        onChange={(e) => updateIssue(it.id, e.target.value)}
                        className="rounded-lg border border-border bg-white px-2 py-1 text-[11px] outline-none focus:border-primary"
                      >
                        {Object.entries(ISSUE_STATUS).map(([k, v]) => (
                          <option key={k} value={k}>{v.label}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-3 flex items-center gap-2">
                <input
                  value={issueTitle}
                  onChange={(e) => setIssueTitle(e.target.value)}
                  placeholder="问题标题"
                  className="min-w-0 flex-1 rounded-lg border border-border bg-white px-2.5 py-1.5 text-xs outline-none focus:border-primary"
                />
                <Button size="sm" variant="outline" onClick={addIssue}><Plus size={14} />记录</Button>
              </div>
              <input
                value={issueDesc}
                onChange={(e) => setIssueDesc(e.target.value)}
                placeholder="问题描述（选填）"
                className="mt-2 w-full rounded-lg border border-border bg-white px-2.5 py-1.5 text-xs outline-none focus:border-primary"
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ===================== 好友管理面板 ===================== */
function FriendsPanel() {
  const ownerId = useAppStore((state) => state.currentUser?.ownerId) ?? '';
  const { success, error: showError } = useToast();

  const [friends, setFriends] = useState<string[]>([]);
  const [pending, setPending] = useState<string[]>([]);
  const [requestsInput, setRequestsInput] = useState('');
  const [loading, setLoading] = useState(true);

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

  useEffect(() => {
    void loadFriends();
  }, [loadFriends]);

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
    <div className="grid gap-4 md:grid-cols-2">
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
          ) : pending.length === 0 ? (
            <p className="text-sm text-subtext">暂无待处理的好友申请。</p>
          ) : (
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

      <div className="app-card p-4">
        <h2 className="mb-3 flex items-center gap-1.5 text-sm font-extrabold text-ink">
          <Users size={15} className="text-primary" />我的好友（{friends.length}）
        </h2>
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-subtext"><Loader2 size={16} className="animate-spin" />加载中...</div>
        ) : friends.length === 0 ? (
          <div className="text-center py-8">
            <UsersRound className="mx-auto text-primary" size={34} />
            <p className="mt-2 text-sm text-subtext">还没有好友，发送申请结伴学习吧。</p>
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
  );
}

/* ===================== 成果隐私面板 ===================== */
function PrivacyPanel() {
  const ownerId = useAppStore((state) => state.currentUser?.ownerId) ?? '';
  const { error: showError } = useToast();

  const [artifacts, setArtifacts] = useState<ArtifactSummary[]>([]);
  const [artifactsLoading, setArtifactsLoading] = useState(false);

  const loadArtifacts = useCallback(async () => {
    setArtifactsLoading(true);
    try {
      const res = await api.listArtifacts('', ownerId);
      setArtifacts(res.artifacts);
    } catch (err) {
      showError(err instanceof Error ? err.message : '成果加载失败');
    } finally {
      setArtifactsLoading(false);
    }
  }, [ownerId, showError]);

  useEffect(() => {
    void loadArtifacts();
  }, [loadArtifacts]);

  return (
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
  );
}
