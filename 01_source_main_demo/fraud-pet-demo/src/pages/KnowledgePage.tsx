import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  BookOpen,
  Image as ImageIcon,
  Lightbulb,
  Loader2,
  Quote,
  RefreshCw,
  ScanSearch,
  ShieldCheck,
  Sparkles,
  Upload,
  X,
} from 'lucide-react';
import { api } from '../api/client';
import type { KnowledgeItem } from '../types';
import { useAppStore } from '../store/useAppStore';
import { useToast } from '../components/ui/Toast';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';

const THEME_EMOJI: Record<string, string> = {
  全部: '📚',
  网络安全: '🔐',
  心理健康: '🧠',
  消防安全: '🧯',
  交通安全: '🚦',
  求职就业: '💼',
  金融素养: '💰',
  学术诚信: '📜',
  个人信息保护: '🔏',
  校园安全: '🏫',
  应急避险: '⛑️',
};

const CATEGORY_EMOJI: Record<string, string> = {
  AI换脸: '🎭',
  冒充客服: '🎧',
  刷单返利: '🧾',
  虚假投资: '📈',
  游戏交易: '🎮',
  冒充老师: '👨‍🏫',
  账户安全: '🔐',
  冒充公检法: '🚔',
  校园贷: '💸',
  注销校园贷: '🗑️',
  培训贷: '🎓',
  杀猪盘: '💘',
  冒充熟人: '👥',
  演唱会门票: '🎫',
  航班退改签: '✈️',
  求职交费: '💼',
  二手交易: '🛍️',
  冒充快递理赔: '📦',
  学术诈骗: '📝',
  免费领取: '🎁',
  百万保障诈骗: '🛡️',
  贷款征信诈骗: '🏦',
  虚假购物服务: '🛒',
  色情诱导诈骗: '⚠️',
  NFC盗刷: '📱',
  寄送现金黄金: '🪙',
  帮信与两卡: '💳',
  虚拟货币诈骗: '₿',
  冒充领导: '👔',
  积分清零诈骗: '⭐',
  快递引流诈骗: '📬',
  九大反诈利器: '🛠️',
  二十个防诈关键词: '🔑',
  刷流水诈骗: '🌊',
  购物卡洗钱: '🎟️',
  反诈总则: '📖',
};

export default function KnowledgePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const fromTaskId = searchParams.get('fromTask');
  const trainingTasks = useAppStore((state) => state.trainingTasks);
  const completeTaskItem = useAppStore((state) => state.completeTaskItem);
  const { error: showError, success: showSuccess } = useToast();
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [activeTheme, setActiveTheme] = useState<string>('全部');
  const [activeCategory, setActiveCategory] = useState<string>('全部');
  const [keyword, setKeyword] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detailItem, setDetailItem] = useState<KnowledgeItem | null>(null);

  // 图片上传识别状态
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [, setUploadedFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<{
    extractedText?: string;
    fraudType?: string;
    riskLevel?: string;
    confidence?: number;
    matchedKeywords?: string[];
    suggestedKeywords?: string[];
    suggestedCategories?: string[];
    isSafe?: boolean;
    analysisNote?: string;
    error?: string;
  } | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const fetchKnowledge = async () => {
    setLoading(true);
    setError(null);
    try {
      const [catsRes, itemsRes] = await Promise.all([
        api.getKnowledgeCategories(),
        api.getKnowledgeItems(),
      ]);
      setCategories(catsRes.categories);
      setItems(itemsRes.items);
    } catch (e) {
      const msg = e instanceof Error ? e.message : '知识库加载失败';
      setError(msg);
      showError(msg);
    } finally {
      setLoading(false);
    }
  };

  // ── 图片上传识别 ──
  const resetImageAnalysis = () => {
    setUploadedImage(null);
    setUploadedFile(null);
    setAnalysisResult(null);
  };

  const analyzeImage = useCallback(async (file: File) => {
    setAnalyzing(true);
    try {
      const result = await api.analyzeImage(file);
      if (result.success) {
        setAnalysisResult({
          extractedText: result.extractedText,
          fraudType: result.fraudType,
          riskLevel: result.riskLevel,
          confidence: result.confidence,
          matchedKeywords: result.matchedKeywords,
          suggestedKeywords: result.suggestedKeywords,
          suggestedCategories: result.suggestedCategories,
          isSafe: result.isSafe,
          analysisNote: result.analysisNote,
        });
        // 自动填充推荐分类和关键词
        if (result.suggestedCategories && result.suggestedCategories.length > 0) {
          const first = result.suggestedCategories[0];
          if (categories.includes(first)) {
            setActiveCategory(first);
          }
        }
        if (result.suggestedKeywords && result.suggestedKeywords.length > 0) {
          setKeyword(result.suggestedKeywords.join(' '));
        }
        showSuccess('图片识别完成');
      } else {
        setAnalysisResult({ error: result.error ?? '识别失败' });
        showError(result.error ?? '图片识别失败');
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : '图片识别失败';
      setAnalysisResult({ error: msg });
      showError(msg);
    } finally {
      setAnalyzing(false);
    }
  }, [categories, showError, showSuccess]);

  const handleFileSelected = useCallback((file: File) => {
    if (!file.type.startsWith('image/')) {
      showError('请上传图片文件（PNG、JPG、GIF、WEBP）');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      showError('图片大小不能超过 10MB');
      return;
    }
    setUploadedFile(file);
    setAnalysisResult(null);
    const reader = new FileReader();
    reader.onload = (e) => setUploadedImage(e.target?.result as string);
    reader.readAsDataURL(file);
    void analyzeImage(file);
  }, [analyzeImage, showError]);

  const onFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileSelected(file);
    e.target.value = '';
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFileSelected(file);
  };

  // 监听 Ctrl+V / Cmd+V 粘贴图片
  useEffect(() => {
    const onPaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;
      for (const item of items) {
        if (item.type.startsWith('image/')) {
          const file = item.getAsFile();
          if (file) handleFileSelected(file);
          break;
        }
      }
    };
    window.addEventListener('paste', onPaste);
    return () => window.removeEventListener('paste', onPaste);
  }, [handleFileSelected]);

  useEffect(() => {
    void fetchKnowledge();
    // 来自任务包，标记知识学习任务完成
    if (fromTaskId) {
      completeTaskItem(fromTaskId).then((ok) => {
        if (ok) showSuccess('知识学习任务已完成 ✓');
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 切换主题时重置分类选择，避免主题与分类冲突导致空结果
  useEffect(() => {
    setActiveCategory('全部');
  }, [activeTheme]);

  // 兼容旧后端：若条目未返回 theme，默认归入中性主题
  const normalizedItems = useMemo(
    () =>
      items.map((it) => ({
        ...it,
        theme: it.theme || '网络安全',
      })),
    [items],
  );

  // 从已加载条目中派生主题 → 分类映射（无需依赖新 API /themes）
  const themes = useMemo(() => {
    const map: Record<string, string[]> = {};
    for (const it of normalizedItems) {
      map[it.theme] ??= [];
      if (!map[it.theme].includes(it.category)) {
        map[it.theme].push(it.category);
      }
    }
    return map;
  }, [normalizedItems]);

  const filtered = normalizedItems.filter((it) => {
    if (activeTheme !== '全部' && it.theme !== activeTheme) return false;
    if (activeCategory !== '全部' && it.category !== activeCategory) return false;
    if (keyword && !it.title.includes(keyword) && !it.category.includes(keyword) && !it.theme.includes(keyword) && !it.typicalPhrase.includes(keyword)) return false;
    return true;
  });

  const availableCategories = activeTheme === '全部' ? categories : (themes[activeTheme] ?? []);
  const allCats = ['全部', ...availableCategories];
  const allThemes = ['全部', ...Object.keys(themes)];

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh] animate-fade-in">
        <Loader2 size={36} className="text-primary animate-spin mb-4" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="app-card">
        <EmptyState
          icon={<AlertCircle size={28} />}
          title="知识库加载失败"
          description={error}
          action={
            <Button onClick={fetchKnowledge} variant="default" size="sm">
              <RefreshCw size={14} className="mr-1.5" /> 重新加载
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* 标题 */}
      <div className="rounded-2xl border border-violet-200/70 bg-gradient-to-r from-violet-50 via-white to-cyan-50 p-6 shadow-card animate-slide-up">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-violet-100 flex items-center justify-center">
            <BookOpen size={24} className="text-violet-700" />
          </div>
          <div>
            <h2 className="text-xl font-extrabold text-ink mb-0.5">综合知识库</h2>
          </div>
        </div>
      </div>

      {/* 搜索 + 分类筛选 */}
      <div
        className={`app-card p-5 space-y-4 animate-slide-up ${isDragging ? 'ring-2 ring-primary ring-offset-2' : ''}`}
        style={{ animationDelay: '60ms' }}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        <div className="relative">
          <ScanSearch size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-subtext" />
          <input
            type="text"
            placeholder="搜索知识主题、分类、标题或典型话术，也可粘贴/拖拽/点击上传聊天截图..."
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            className="field pl-10 pr-24"
          />
          <div className="absolute right-1.5 top-1/2 -translate-y-1/2 flex items-center gap-1">
            {keyword && (
              <button
                type="button"
                onClick={() => {
                  setKeyword('');
                  setActiveCategory('全部');
                  resetImageAnalysis();
                }}
                className="p-1.5 rounded-md text-subtext hover:bg-slate-100 hover:text-ink transition-colors"
                title="清空"
              >
                <X size={14} />
              </button>
            )}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-primary-soft text-primary text-xs font-medium hover:bg-primary/15 transition-colors"
              title="上传聊天截图识别"
            >
              <ImageIcon size={14} /> 识图
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/gif,image/webp,image/bmp"
              className="hidden"
              onChange={onFileInputChange}
            />
          </div>
        </div>

        {/* 拖拽提示 */}
        {isDragging && (
          <div className="rounded-xl border-2 border-dashed border-primary bg-primary-soft/40 p-6 text-center text-primary text-sm font-medium animate-fade-in">
            <Upload size={24} className="mx-auto mb-2" />
            松开即可上传聊天截图进行识别
          </div>
        )}

        {/* 图片识别结果 */}
        {(uploadedImage || analyzing || analysisResult) && (
          <div className="rounded-xl border border-slate-100 bg-slate-50/80 overflow-hidden animate-fade-in">
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-100 bg-white/60">
              <div className="flex items-center gap-2 text-sm font-medium text-ink">
                <ScanSearch size={15} className="text-primary" />
                <span>图片识别结果</span>
                {analyzing && <Loader2 size={14} className="animate-spin text-subtext" />}
              </div>
              <button
                onClick={resetImageAnalysis}
                className="p-1 rounded-md text-subtext hover:bg-slate-100 hover:text-ink transition-colors"
                title="清除识别结果"
              >
                <X size={14} />
              </button>
            </div>
            <div className="p-4 space-y-4">
              {uploadedImage && (
                <div className="flex items-start gap-4">
                  <div className="relative group flex-shrink-0">
                    <img
                      src={uploadedImage}
                      alt="上传的聊天截图"
                      className="w-28 h-28 object-cover rounded-xl border border-slate-200"
                    />
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 rounded-xl transition-colors" />
                  </div>
                  <div className="flex-1 min-w-0">
                    {analysisResult?.error ? (
                      <div className="rounded-lg p-3 bg-rose-50 text-danger text-sm">
                        {analysisResult.error}
                      </div>
                    ) : analysisResult?.extractedText ? (
                      <div className="space-y-3">
                        <div>
                          <p className="text-sm text-ink leading-relaxed bg-white rounded-lg p-3 border border-slate-100">
                            {analysisResult.extractedText}
                          </p>
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                          {analysisResult.fraudType && analysisResult.fraudType !== '正常文本' && analysisResult.fraudType !== '未知' && (
                            <span className={`chip border text-xs ${
                              analysisResult.riskLevel === '高风险' ? 'bg-rose-50 text-danger border-rose-100' :
                              analysisResult.riskLevel === '中风险' ? 'bg-amber-50 text-warning border-amber-100' :
                              'bg-primary-soft text-primary border-primary/15'
                            }`}>
                              {analysisResult.riskLevel} · {analysisResult.fraudType}
                            </span>
                          )}
                          {analysisResult.fraudType === '正常文本' && (
                            <span className="chip border text-xs bg-emerald-50 text-emerald-600 border-emerald-100">
                              暂未识别出明显风险特征
                            </span>
                          )}
                          {typeof analysisResult.confidence === 'number' && analysisResult.confidence > 0 && (
                            <span className="text-xs text-subtext">
                              置信度 {Math.round(analysisResult.confidence * 100)}%
                            </span>
                          )}
                        </div>
                      </div>
) : null
}
                  </div>
                </div>
              )}

              {/* 推荐搜索 */}
              {!analyzing && analysisResult && (
                <div className="space-y-3">
                  {(analysisResult.suggestedKeywords && analysisResult.suggestedKeywords.length > 0) && (
                    <div>
                      <div className="flex flex-wrap gap-2">
                        {analysisResult.suggestedKeywords.map((kw) => (
                          <button
                            key={kw}
                            onClick={() => setKeyword(kw)}
                            className="px-2.5 py-1 rounded-full text-xs bg-white border border-slate-200 text-ink hover:border-primary hover:text-primary transition-colors"
                          >
                            {kw}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                  {(analysisResult.suggestedCategories && analysisResult.suggestedCategories.length > 0) && (
                    <div>
                      <div className="flex flex-wrap gap-2">
                        {analysisResult.suggestedCategories.map((cat) => (
                          <button
                            key={cat}
                            onClick={() => {
                              if (categories.includes(cat) || cat === '全部') {
                                setActiveCategory(cat);
                              } else {
                                setKeyword(cat);
                              }
                            }}
                            className={`px-2.5 py-1 rounded-full text-xs border transition-colors ${
                              activeCategory === cat
                                ? 'bg-gradient-to-r from-primary to-primary-deep text-white border-transparent'
                                : 'bg-white border-slate-200 text-ink hover:border-primary hover:text-primary'
                            }`}
                          >
                            {CATEGORY_EMOJI[cat] ? `${CATEGORY_EMOJI[cat]} ` : ''}{cat}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                  {analysisResult.analysisNote && (
                    <p className="text-[11px] text-subtext leading-relaxed">{analysisResult.analysisNote}</p>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* 主题筛选 */}
        <div className="space-y-1.5">
          <div className="flex flex-wrap gap-2">
            {allThemes.map((theme) => (
              <button
                key={theme}
                onClick={() => setActiveTheme(theme)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  activeTheme === theme
                    ? 'bg-gradient-to-r from-primary to-primary-deep text-white shadow-glow-sm'
                    : 'bg-slate-50 text-subtext hover:bg-slate-100 hover:text-ink'
                }`}
              >
                {THEME_EMOJI[theme] ? `${THEME_EMOJI[theme]} ` : ''}{theme}
              </button>
            ))}
          </div>
        </div>

        {/* 分类筛选 */}
        <div className="space-y-1.5">
          <div className="flex flex-wrap gap-2">
            {allCats.map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  activeCategory === cat
                    ? 'bg-gradient-to-r from-primary to-primary-deep text-white shadow-glow-sm'
                    : 'bg-slate-50 text-subtext hover:bg-slate-100 hover:text-ink'
                }`}
              >
                {cat !== '全部' && CATEGORY_EMOJI[cat] ? `${CATEGORY_EMOJI[cat]} ` : ''}{cat}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 知识卡片列表 */}
      <div>
        <p className="text-sm text-subtext mb-3">共 <span className="font-bold text-ink">{filtered.length}</span> 条知识</p>
        {filtered.length === 0 ? (
          <div className="app-card p-12 text-center text-subtext animate-fade-in">
            <BookOpen size={36} className="mx-auto mb-3 text-slate-300" />
            <p>暂无符合条件的知识条目</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {filtered.map((item, idx) => (
              <KnowledgeCard
                key={item.id}
                item={item}
                delay={idx * 50}
                onOpenDetail={() => setDetailItem(item)}
                onTrain={() => {
                  if (item.relatedTaskId) navigate(`/training/session/${item.relatedTaskId}`);
                }}
                relatedTitle={item.relatedTaskId ? trainingTasks.find((t) => t.id === item.relatedTaskId)?.title : undefined}
              />
            ))}
          </div>
        )}
      </div>

      {/* 合规提示 */}
      <div className="rounded-xl p-4 bg-slate-50/80 border border-slate-100 flex items-start gap-3">
        <ShieldCheck size={16} className="text-safe flex-shrink-0 mt-0.5" />
        <p className="text-xs text-subtext leading-relaxed">
          知识库内容均标注来源，仅供校园主题学习、风险提示与自我教育参考，不替代公安机关、金融机构、学校管理部门或专业医疗机构的判断。如遇紧急情况，请及时拨打 <span className="font-bold text-ink">110</span>、反诈专线 <span className="font-bold text-ink">96110</span> 或联系学校相关部门。
        </p>
      </div>

      {/* 知识详情弹窗 */}
      {detailItem && (
        <KnowledgeDetailModal
          item={detailItem}
          onClose={() => setDetailItem(null)}
          onTrain={
            detailItem.relatedTaskId
              ? () => {
                  setDetailItem(null);
                  navigate(`/training/session/${detailItem.relatedTaskId}`);
                }
              : undefined
          }
          relatedTitle={
            detailItem.relatedTaskId
              ? trainingTasks.find((t) => t.id === detailItem.relatedTaskId)?.title
              : undefined
          }
        />
      )}
    </div>
  );
}

function KnowledgeCard({
  item,
  delay,
  onTrain,
  onOpenDetail,
  relatedTitle,
}: {
  item: KnowledgeItem;
  delay: number;
  onTrain: () => void;
  onOpenDetail: () => void;
  relatedTitle?: string;
}) {
  const emoji = CATEGORY_EMOJI[item.category] || '🛡️';
  const riskCls =
    item.riskLevel === '高风险' ? 'bg-rose-50 text-danger border-rose-100' :
    item.riskLevel === '中风险' ? 'bg-amber-50 text-warning border-amber-100' :
    'bg-primary-soft text-primary border-primary/15';

  return (
    <div
      className="app-card app-card-hover p-5 animate-slide-up cursor-pointer select-none"
      style={{ animationDelay: `${delay}ms` }}
      onDoubleClick={onOpenDetail}
      title="双击查看完整详情"
    >
      {/* 头部 */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center text-2xl border border-slate-100">
            {emoji}
          </div>
          <div>
            <h3 className="font-bold text-ink leading-tight">{item.title}</h3>
            <div className="flex flex-wrap items-center gap-1.5 mt-1">
              <span className="text-[11px] px-1.5 py-0.5 rounded-md bg-slate-100 text-subtext">{item.theme}</span>
              <span className="text-[11px] text-subtext">{item.category}</span>
            </div>
          </div>
        </div>
        <span className={`chip border whitespace-nowrap ${riskCls}`}>{item.riskLevel}</span>
      </div>

      {/* 典型话术 */}
      <div className="rounded-xl p-3 bg-slate-50/80 border border-slate-100 mb-3">
        <p className="text-[11px] text-subtext mb-1 flex items-center gap-1 font-medium"><Quote size={11} /> 典型话术</p>
        <p className="text-sm text-ink leading-relaxed italic">「{item.typicalPhrase}」</p>
      </div>

      {/* 识别要点 */}
      <div className="flex items-start gap-2 mb-2.5">
        <AlertTriangle size={15} className="text-warning flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          {item.id === 'know-20-keywords' ? (
            <KeywordGrid content={item.recognitionPoints} />
          ) : (
            <p className="text-sm text-ink leading-relaxed">{item.recognitionPoints}</p>
          )}
        </div>
      </div>

      {/* 应对建议 */}
      <div className="flex items-start gap-2 mb-4">
        <Lightbulb size={15} className="text-safe flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm text-ink leading-relaxed">{item.suggestions}</p>
        </div>
      </div>

      {/* 来源 */}
      {item.source && (
        <div className="mt-3 pt-3 border-t border-slate-100">
          <p className="text-[11px] text-subtext leading-relaxed flex items-start gap-1">
            <BookOpen size={11} className="flex-shrink-0 mt-0.5" />
            <span className="line-clamp-2">来源：{item.source}</span>
          </p>
        </div>
      )}

      {/* 关联训练 */}
      {relatedTitle && (
        <button
          onClick={onTrain}
          className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl bg-primary-soft/60 border border-primary/15 text-primary text-sm font-medium hover:bg-primary-soft transition-colors group"
        >
          <span className="flex items-center gap-1.5"><Sparkles size={14} /> 关联训练：{relatedTitle}</span>
          <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
        </button>
      )}
    </div>
  );
}

function KeywordGrid({ content }: { content: string }) {
  const separator = content.indexOf('：') !== -1 ? '：' : ':';
  const parts = content.split(separator);
  const intro = parts[0] + separator;
  const rest = parts.slice(1).join(separator);
  const tokens = rest.trim().split(/\s+/);
  const items = tokens
    .map((token) => {
      const match = token.match(/^(\d+)([^=]+)=(.*)$/);
      if (!match) return null;
      return {
        num: Number(match[1]),
        keyword: match[2].trim(),
        meaning: match[3].trim().replace(/[。，；;,.]$/, ''),
      };
    })
    .filter((it): it is { num: number; keyword: string; meaning: string } => it !== null);

  if (items.length === 0) {
    return <p className="text-sm text-ink leading-relaxed">{content}</p>;
  }

  return (
    <div>
      <p className="text-sm text-ink leading-relaxed mb-2">{intro}</p>
      <div className="grid grid-cols-2 gap-x-2 gap-y-1">
        {items.map((it) => (
          <div
            key={it.num}
            className="flex items-center gap-1 text-xs leading-snug"
          >
            <span className="w-4 h-4 rounded-full bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center flex-shrink-0">
              {it.num}
            </span>
            <span className="font-semibold text-ink">{it.keyword}</span>
            <span className="text-subtext">{it.meaning}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/** 知识详情弹窗 — 双击卡片后展示完整内容 */
function KnowledgeDetailModal({
  item,
  onClose,
  onTrain,
  relatedTitle,
}: {
  item: KnowledgeItem;
  onClose: () => void;
  onTrain?: () => void;
  relatedTitle?: string;
}) {
  const emoji = CATEGORY_EMOJI[item.category] || '🛡️';
  const riskCls =
    item.riskLevel === '高风险' ? 'bg-rose-50 text-danger border-rose-200' :
    item.riskLevel === '中风险' ? 'bg-amber-50 text-warning border-amber-200' :
    'bg-primary-soft text-primary border-primary/20';

  // Esc 关闭
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    // 弹出时禁止背景滚动
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in"
      onClick={onClose}
    >
      {/* 遮罩 */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

      {/* 弹窗主体 */}
      <div
        className="relative w-full max-w-2xl max-h-[85vh] overflow-y-auto bg-white rounded-2xl shadow-2xl animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="sticky top-0 bg-white/95 backdrop-blur border-b border-slate-100 px-6 py-4 flex items-start justify-between gap-3 z-10">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center text-2xl border border-slate-100 flex-shrink-0">
              {emoji}
            </div>
            <div className="min-w-0">
              <h3 className="font-extrabold text-ink leading-tight text-lg">{item.title}</h3>
              <p className="text-xs text-subtext mt-1 flex items-center gap-2 flex-wrap">
                <span className="px-1.5 py-0.5 rounded-md bg-slate-100">{item.theme}</span>
                <span>{item.category}</span>
                <span className={`chip border ${riskCls}`}>{item.riskLevel}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-subtext flex-shrink-0 transition-colors"
            aria-label="关闭"
          >
            <X size={16} />
          </button>
        </div>

        {/* 内容区 */}
        <div className="px-6 py-5 space-y-5">
          {/* 典型话术 */}
          <div className="rounded-xl p-4 bg-slate-50/80 border border-slate-100">
            <p className="text-xs text-subtext mb-2 flex items-center gap-1 font-medium">
              <Quote size={12} /> 典型话术
            </p>
            <p className="text-sm text-ink leading-relaxed italic">「{item.typicalPhrase}」</p>
          </div>

          {/* 识别要点 */}
          <div>
            <p className="text-xs text-subtext mb-2 flex items-center gap-1 font-medium">
              <AlertTriangle size={12} className="text-warning" /> 识别要点
            </p>
            {item.id === 'know-20-keywords' ? (
              <KeywordGrid content={item.recognitionPoints} />
            ) : (
              <p className="text-sm text-ink leading-relaxed whitespace-pre-line">{item.recognitionPoints}</p>
            )}
          </div>

          {/* 应对建议 */}
          <div>
            <p className="text-xs text-subtext mb-2 flex items-center gap-1 font-medium">
              <Lightbulb size={12} className="text-safe" /> 应对建议
            </p>
            <p className="text-sm text-ink leading-relaxed whitespace-pre-line">{item.suggestions}</p>
          </div>

          {/* 来源 */}
          {item.source && (
            <div className="rounded-xl p-4 bg-slate-50/80 border border-slate-100">
              <p className="text-xs text-subtext mb-1.5 flex items-center gap-1 font-medium">
                <BookOpen size={12} /> 内容来源
              </p>
              <p className="text-sm text-ink leading-relaxed">{item.source}</p>
              {item.sourceUrl && (
                <a
                  href={item.sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 mt-2 text-xs text-primary hover:underline"
                  onClick={(e) => e.stopPropagation()}
                >
                  查看原始来源 <ArrowRight size={11} />
                </a>
              )}
            </div>
          )}

          {/* 关联训练 */}
          {relatedTitle && onTrain && (
            <button
              onClick={onTrain}
              className="w-full flex items-center justify-between px-4 py-3 rounded-xl bg-primary-soft/60 border border-primary/15 text-primary text-sm font-medium hover:bg-primary-soft transition-colors group"
            >
              <span className="flex items-center gap-1.5">
                <Sparkles size={14} /> 关联训练：{relatedTitle}
              </span>
              <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
            </button>
          )}
        </div>

        {/* 底部 */}
        <div className="sticky bottom-0 bg-white/95 backdrop-blur border-t border-slate-100 px-6 py-3 flex items-center justify-between">
          <p className="text-xs text-subtext flex items-center gap-1">
            <ShieldCheck size={12} className="text-safe" /> 按 Esc 或点击空白处关闭
          </p>
          <button
            onClick={onClose}
            className="btn-primary px-5 py-2 text-sm"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  );
}
