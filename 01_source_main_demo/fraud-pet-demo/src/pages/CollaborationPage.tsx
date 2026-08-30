import { useCallback, useEffect, useState } from 'react';
import {
  CheckCircle2,
  Loader2,
  Plus,
  Trash2,
  Users,
  Flag,
  AlertTriangle,
  XCircle,
} from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/useAppStore';
import type { Team, TeamMember, Milestone, ProjectIssue } from '../types/learning';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useToast } from '../components/ui/Toast';

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

export default function CollaborationPage() {
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
    <div className="space-y-5 animate-slide-up">
      <section className="rounded-3xl border border-indigo-200/70 bg-gradient-to-br from-indigo-50 via-white to-violet-50 p-6 shadow-card">
        <div>
          <Badge className="border-indigo-200/70 bg-white/80 text-indigo-700">项目式协作管控</Badge>
          <h1 className="mt-3 text-2xl font-extrabold text-ink sm:text-3xl">小组分工 · 节点验收 · 问题跟踪</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-subtext">
            组建学习小组，明确成员分工；按阶段节点推进并验收成果，全程记录项目问题，让协作过程可追溯。
          </p>
        </div>
      </section>

      <div className="grid gap-5 lg:grid-cols-[320px_1fr]">
        {/* 左：团队列表 + 创建 */}
        <div className="space-y-4">
          <div className="app-card p-4 space-y-3">
            <h2 className="text-sm font-extrabold text-ink">创建学习小组</h2>
            <input
              value={createName}
              onChange={(e) => setCreateName(e.target.value)}
              placeholder="小组名称（如：反诈海报攻坚组）"
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
            ) : teams.length === 0 ? null
 : (
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

        {/* 右：小组详情 */}
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
              {/* 成员管理 */}
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

              {/* 节点验收 */}
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

              {/* 问题记录 */}
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
    </div>
  );
}
