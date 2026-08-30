import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  CheckCircle2,
  FileArchive,
  FileCheck2,
  FileUp,
  History,
  Image,
  Loader2,
  MessageSquareText,
  Send,
  Sparkles,
} from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/useAppStore';
import type { ArtifactReview, LearningDashboard } from '../types/learning';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useToast } from '../components/ui/Toast';

export default function ArtifactStudioPage() {
  const navigate = useNavigate();
  const ownerId = useAppStore((state) => state.currentUser?.ownerId) ?? '';
  const { success, error: showError } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dashboard, setDashboard] = useState<LearningDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [title, setTitle] = useState('大学生兼职诈骗防范海报');
  const [artifactType, setArtifactType] = useState('海报');
  const [description, setDescription] = useState('面向大学生群体，突出刷单诈骗风险信号和正确求助方式。');
  const [fileName, setFileName] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [contentSummary, setContentSummary] = useState(
    '作品面向大学生兼职求职场景，重点展示“先垫付、承诺高额返利、要求脱离正规平台”三类风险信号，并给出停止转账、保存证据和拨打96110核验的行动建议。',
  );
  const [revisionNote, setRevisionNote] = useState('');
  const [reviewResult, setReviewResult] = useState<ArtifactReview | null>(null);
  const [reviewLoading, setReviewLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.getLearningDashboard(ownerId);
      setDashboard(result);
      useAppStore.getState().setActiveLearningTheme(result.goal?.theme ?? result.plan?.title ?? null);
      if (!selectedId && result.artifacts[0]) setSelectedId(result.artifacts[0].id);
    } catch (err) {
      showError(err instanceof Error ? err.message : '成果工作台加载失败');
    } finally {
      setLoading(false);
    }
  }, [ownerId, selectedId, showError]);

  useEffect(() => {
    void load();
  }, [load]);

  const selectedArtifact = useMemo(
    () => dashboard?.artifacts.find((artifact) => artifact.id === selectedId) ?? null,
    [dashboard?.artifacts, selectedId],
  );

  const createArtifact = async () => {
    if (!dashboard?.plan) {
      showError('请先生成学习任务包');
      return;
    }
    setBusy(true);
    try {
      const result = await api.createLearningArtifact({
        ownerId,
        planId: dashboard.plan.id,
        title,
        artifactType,
        description,
        visibility: 'private',
      });
      setSelectedId(result.artifact.id);
      success('成果档案已创建，请提交第一个版本');
      await load();
    } catch (err) {
      showError(err instanceof Error ? err.message : '成果创建失败');
    } finally {
      setBusy(false);
    }
  };

  const submitVersion = async () => {
    if (!selectedArtifact) {
      showError('请先创建或选择成果');
      return;
    }
    if (contentSummary.trim().length < 8) {
      showError('请补充成果内容说明，便于AI进行初审');
      return;
    }
    setBusy(true);
    try {
      let uploadedFileName = fileName;
      if (selectedFile) {
        const upload = await api.uploadLearningArtifactFile(selectedArtifact.id, ownerId, selectedFile);
        uploadedFileName = upload.fileName;
      }
      const result = await api.addLearningArtifactVersion(selectedArtifact.id, {
        ownerId,
        fileName: uploadedFileName,
        contentSummary,
        revisionNote,
      });
      success(result.message);
      setRevisionNote('');
      setSelectedFile(null);
      setFileName('');
      await load();
    } catch (err) {
      showError(err instanceof Error ? err.message : '成果版本提交失败');
    } finally {
      setBusy(false);
    }
  };

  const runAiReview = async () => {
    if (!selectedArtifact) return;
    if (contentSummary.trim().length < 8) {
      showError('请先补充成果内容说明，便于AI进行初审');
      return;
    }
    setReviewLoading(true);
    try {
      const result = await api.reviewArtifact(selectedArtifact.id, {
        ownerId,
        contentSummary,
        revisionNote,
        fileName,
      });
      setReviewResult(result.review);
      success(result.message);
    } catch (err) {
      showError(err instanceof Error ? err.message : 'AI初审失败');
    } finally {
      setReviewLoading(false);
    }
  };

  const publish = async (visibility: 'public' | 'private') => {
    if (!selectedArtifact) return;
    setBusy(true);
    try {
      const result = await api.publishLearningArtifact(selectedArtifact.id, ownerId, visibility);
      success(result.message);
      await load();
    } catch (err) {
      showError(err instanceof Error ? err.message : '成果发布失败');
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[420px] items-center justify-center text-subtext">
        <Loader2 className="mr-2 animate-spin" size={20} />正在载入成果档案...
      </div>
    );
  }

  if (!dashboard?.plan) {
    return (
      <div className="app-card mx-auto max-w-xl p-8 text-center">
        <FileArchive className="mx-auto text-primary" size={40} />
        <h1 className="mt-3 text-xl font-extrabold text-ink">成果需要关联学习任务包</h1>
        <Button className="mt-5" onClick={() => navigate('/learning/goal')}>
          去发布目标 <ArrowRight size={16} />
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-5 animate-slide-up">
      <section className="rounded-3xl border border-amber-200/70 bg-gradient-to-br from-amber-50 via-white to-violet-50 p-5 shadow-card">
        <Badge variant="warning">AI学习集市 · 成果闭环</Badge>
        <h1 className="mt-3 text-2xl font-extrabold text-ink">成果工坊</h1>
      </section>

      <div className="grid gap-5 xl:grid-cols-[0.72fr_1.28fr]">
        <aside className="space-y-4">
          <section className="app-card p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-extrabold text-ink">我的成果</h2>
              <Badge variant="outline" size="sm">{dashboard.artifacts.length}项</Badge>
            </div>
            <div className="space-y-2">
              {dashboard.artifacts.length === 0 && (
                <div className="rounded-2xl border border-dashed border-border p-4 text-center text-xs text-subtext">
                  暂无成果，填写下方信息创建第一项。
                </div>
              )}
              {dashboard.artifacts.map((artifact) => (
                <button
                  key={artifact.id}
                  onClick={() => setSelectedId(artifact.id)}
                  className={`w-full rounded-2xl border p-3 text-left transition ${
                    selectedId === artifact.id
                      ? 'border-primary bg-primary-soft/60 shadow-glow-sm'
                      : 'border-border bg-white hover:border-primary/30'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-bold text-ink">{artifact.title}</p>
                    <Badge variant={artifact.status === 'published' ? 'success' : 'secondary'} size="sm">
                      {artifact.status === 'published' ? '已发布' : '草稿'}
                    </Badge>
                  </div>
                  <div className="mt-2 flex items-center justify-between text-[10px] text-subtext">
                    <span>{artifact.artifactType}</span>
                    <span>V{artifact.latestVersion}</span>
                  </div>
                </button>
              ))}
            </div>
          </section>

          <section className="app-card p-4">
            <div className="flex items-center gap-2">
              <FileUp className="text-primary" size={17} />
              <h2 className="text-sm font-extrabold text-ink">新建成果档案</h2>
            </div>
            <div className="mt-3 space-y-3">
              <input
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                className="w-full rounded-xl border border-border px-3 py-2.5 text-xs outline-none focus:border-primary"
                placeholder="成果标题"
              />
              <select
                value={artifactType}
                onChange={(event) => setArtifactType(event.target.value)}
                className="w-full rounded-xl border border-border bg-white px-3 py-2.5 text-xs outline-none focus:border-primary"
              >
                <option>海报</option>
                <option>文档</option>
                <option>PPT</option>
                <option>视频</option>
                <option>案例报告</option>
                <option>思维导图</option>
                <option>其他</option>
              </select>
              <textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                rows={3}
                className="w-full resize-none rounded-xl border border-border px-3 py-2.5 text-xs leading-5 outline-none focus:border-primary"
                placeholder="成果面向谁、解决什么问题？"
              />
              <Button fullWidth onClick={createArtifact} loading={busy}>创建成果档案</Button>
            </div>
          </section>
        </aside>

        <main className="space-y-4">
          {!selectedArtifact ? (
            <div className="app-card flex min-h-[420px] flex-col items-center justify-center p-8 text-center">
              <Image className="text-primary" size={42} />
              <h2 className="mt-3 text-lg font-extrabold text-ink">创建成果后开始版本迭代</h2>
            </div>
          ) : (
            <>
              <section className="app-card p-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="info">{selectedArtifact.artifactType}</Badge>
                      <Badge variant={selectedArtifact.status === 'published' ? 'success' : 'secondary'}>
                        {selectedArtifact.status === 'published' ? '已发布' : '迭代中'}
                      </Badge>
                    </div>
                    <h2 className="mt-2 text-lg font-extrabold text-ink">{selectedArtifact.title}</h2>
                    <p className="mt-1 text-xs leading-5 text-subtext">{selectedArtifact.description}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={selectedArtifact.latestVersion < 1 || busy}
                      onClick={() => publish('private')}
                    >
                      仅归档
                    </Button>
                    <Button
                      size="sm"
                      disabled={selectedArtifact.latestVersion < 1 || busy}
                      onClick={() => publish('public')}
                    >
                      <Send size={14} />发布至集市
                    </Button>
                  </div>
                </div>
              </section>

              <section className="app-card p-5">
                <div className="flex items-center gap-2">
                  <FileUp className="text-primary" size={18} />
                  <h2 className="text-sm font-extrabold text-ink">
                    提交{selectedArtifact.latestVersion === 0 ? '首个' : '新'}版本
                  </h2>
                  <Badge variant="outline" size="sm">下一版 V{selectedArtifact.latestVersion + 1}</Badge>
                </div>

                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  <div className="space-y-3">
                    <input
                      ref={fileInputRef}
                      type="file"
                      className="hidden"
                      accept=".pdf,.ppt,.pptx,.doc,.docx,.png,.jpg,.jpeg,.mp4,.zip"
                      onChange={(event) => {
                        const nextFile = event.target.files?.[0] ?? null;
                        setSelectedFile(nextFile);
                        setFileName(nextFile?.name ?? '');
                      }}
                    />
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="flex min-h-28 w-full flex-col items-center justify-center rounded-2xl border border-dashed border-primary/35 bg-primary-soft/35 p-4 text-center transition hover:bg-primary-soft/60"
                    >
                      <FileUp className="text-primary" size={24} />
                      <p className="mt-2 text-xs font-bold text-ink">{fileName || '选择成果文件'}</p>
                    </button>
                    <textarea
                      value={revisionNote}
                      onChange={(event) => setRevisionNote(event.target.value)}
                      rows={3}
                      className="w-full resize-none rounded-xl border border-border px-3 py-2.5 text-xs leading-5 outline-none focus:border-primary"
                      placeholder={selectedArtifact.latestVersion ? '本次根据哪些建议进行了修改？' : '首版创作说明（可选）'}
                    />
                  </div>
                  <div>
                    <label className="text-xs font-bold text-ink">成果内容说明</label>
                    <textarea
                      value={contentSummary}
                      onChange={(event) => setContentSummary(event.target.value)}
                      rows={8}
                      className="mt-1.5 w-full resize-none rounded-2xl border border-border px-3 py-3 text-xs leading-5 outline-none focus:border-primary"
                      placeholder="描述目标受众、内容结构、核心观点和行动建议，AI会据此初审。"
                    />
                  </div>
                </div>
                <div className="mt-4 flex flex-wrap justify-end gap-2">
                  <Button variant="outline" onClick={runAiReview} loading={reviewLoading}>
                    <FileCheck2 size={15} />AI初审草稿（不提交）
                  </Button>
                  <Button onClick={submitVersion} loading={busy}>
                    <Sparkles size={15} />提交并进行AI初审
                  </Button>
                </div>

                {reviewResult && (
                  <div className="mt-3 rounded-2xl border border-primary/20 bg-primary-soft/40 p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <FileCheck2 className="text-primary" size={17} />
                        <h2 className="text-sm font-extrabold text-ink">AI初审结果</h2>
                      </div>
                      <span className="text-xs font-bold text-primary">
                        {reviewResult.score ?? '--'} 分 · {reviewResult.level}
                      </span>
                    </div>
                    <ReviewList title="做得好的地方" items={reviewResult.strengths} tone="success" />
                    <ReviewList title="可优化点" items={reviewResult.issues} tone="warning" />
                    <ReviewList title="下一版修改建议" items={reviewResult.suggestions} tone="warning" />
                    <p className="mt-2 text-[10px] text-subtext">{reviewResult.source}</p>
                  </div>
                )}
              </section>

              {selectedArtifact.latestVersion > 0 && (
                <section className="grid gap-4 lg:grid-cols-[0.82fr_1.18fr]">
                  <div className="app-card p-4">
                    <div className="flex items-center gap-2">
                      <FileCheck2 className="text-safe-600" size={18} />
                      <h2 className="text-sm font-extrabold text-ink">AI初审</h2>
                    </div>
                    <div className="mt-3 flex items-end gap-2">
                      <span className="text-3xl font-extrabold text-primary">{selectedArtifact.aiReview.score ?? '--'}</span>
                      <span className="pb-1 text-xs text-subtext">/ 100 · {selectedArtifact.aiReview.level}</span>
                    </div>
                    <ReviewList
                      title="做得好的地方"
                      items={selectedArtifact.aiReview.strengths}
                      tone="success"
                    />
                    <ReviewList
                      title="下一版修改建议"
                      items={selectedArtifact.aiReview.suggestions}
                      tone="warning"
                    />
                    <p className="mt-3 text-[10px] text-subtext">{selectedArtifact.aiReview.source}</p>
                  </div>

                  <div className="app-card p-4">
                    <div className="flex items-center gap-2">
                      <History className="text-primary" size={18} />
                      <h2 className="text-sm font-extrabold text-ink">版本迭代记录</h2>
                    </div>
                    <div className="mt-3 space-y-3">
                      {[...selectedArtifact.versions].reverse().map((version) => (
                        <article key={version.id} className="rounded-2xl border border-border bg-white p-3">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <div className="flex items-center gap-2">
                                <Badge variant="info" size="sm">V{version.versionNo}</Badge>
                                <span className="text-xs font-bold text-ink">{version.fileName || '文字成果说明'}</span>
                              </div>
                              <p className="mt-2 line-clamp-3 text-[11px] leading-5 text-subtext">{version.contentSummary}</p>
                            </div>
                            <span className="shrink-0 text-lg font-extrabold text-primary">{version.aiReview.score ?? '--'}</span>
                          </div>
                          {version.revisionNote && (
                            <div className="mt-2 rounded-xl bg-muted/60 px-2.5 py-2 text-[10px] leading-4 text-subtext">
                              <span className="font-bold text-ink">修改说明：</span>{version.revisionNote}
                              <p className="mt-2 max-w-sm text-sm leading-6 text-subtext">至少保留V1和修改版，展示AI建议如何转化为真实学习改进。</p>
                            </div>
                          )}
                        </article>
                      ))}
                    </div>
                  </div>
                </section>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}

function ReviewList({
  title,
  items,
  tone,
}: {
  title: string;
  items?: string[];
  tone: 'success' | 'warning';
}) {
  if (!items?.length) return null;
  return (
    <div className="mt-4">
      <p className="mb-2 text-xs font-bold text-ink">{title}</p>
      <ul className="space-y-1.5">
        {items.map((item) => (
          <li key={item} className="flex gap-2 text-[11px] leading-5 text-subtext">
            {tone === 'success' ? (
              <CheckCircle2 className="mt-0.5 shrink-0 text-safe-500" size={13} />
            ) : (
              <MessageSquareText className="mt-0.5 shrink-0 text-amber-500" size={13} />
            )}
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
