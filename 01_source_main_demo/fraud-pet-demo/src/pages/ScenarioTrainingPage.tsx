import { useEffect, useRef, useState, useCallback } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Loader2,
  MessageSquare,
  Send,
  Shield,
  Siren,
  XCircle,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import type { ScenarioMessage, ScenarioState } from '../types';

const SCENARIO_TYPES: Record<string, string> = {
  brush_orders: '刷单返利',
  game_trade: '游戏交易',
  fake_customer_service: '虚假客服',
  fake_teacher: '冒充老师',
  fake_recruitment: '虚假招聘',
  scholarship: '奖助学金诈骗',
  ai_face_swap: 'AI换脸',
  training_loan: '求职培训贷',
  refund: '网购退款',
  investment: '虚假投资理财',
};

const STATE_LABELS: Record<string, string> = {
  S0: '对话开始',
  S1: '初步接触',
  S2: '深入诱导',
  S3: '施压/威胁',
  S4: '转账引导',
  S5: '对话结束',
};

export default function ScenarioTrainingPage() {
  const { type } = useParams();
  const [searchParams] = useSearchParams();
  const taskIdFromQuery = searchParams.get('taskId');
  const navigate = useNavigate();
  const scenarioSession = useAppStore((state) => state.scenarioSession);
  const reviewReport = useAppStore((state) => state.reviewReport);
  const isLoading = useAppStore((state) => state.isLoading);
  const startScenarioTraining = useAppStore((state) => state.startScenarioTraining);
  const replyScenarioTraining = useAppStore((state) => state.replyScenarioTraining);
  const finishScenarioTraining = useAppStore((state) => state.finishScenarioTraining);
  const completeTaskItem = useAppStore((state) => state.completeTaskItem);

  const [input, setInput] = useState('');
  const [showReview, setShowReview] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Start session on mount
  useEffect(() => {
    let cancelled = false;
    const scenarioType = type ?? 'brush_orders';
    if (!cancelled) {
      startScenarioTraining(scenarioType);
    }
    return () => { cancelled = true; };
  }, [type, startScenarioTraining]);

  // Auto scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [scenarioSession?.messages]);

  const handleSend = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading || scenarioSession?.currentState === 'S5') return;
    setInput('');
    const result = await replyScenarioTraining(trimmed);
    if (result?.isTerminal || result?.isCompleted) {
      setIsCompleted(true);
      await finishScenarioTraining();
      // 如果来自任务包，标记完成
      if (taskIdFromQuery) {
        await completeTaskItem(taskIdFromQuery);
      }
      setShowReview(true);
    }
  }, [input, isLoading, scenarioSession?.currentState, replyScenarioTraining, finishScenarioTraining, taskIdFromQuery, completeTaskItem]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  const handleFinishEarly = useCallback(async () => {
    setIsCompleted(true);
    await finishScenarioTraining();
    // 如果来自任务包，标记完成
    if (taskIdFromQuery) {
      await completeTaskItem(taskIdFromQuery);
    }
    setShowReview(true);
  }, [finishScenarioTraining, taskIdFromQuery, completeTaskItem]);

  const isFinished = isCompleted || scenarioSession?.currentState === 'S5';

  // Loading
  if (!scenarioSession && isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] animate-fade-in">
        <Loader2 size={36} className="text-primary animate-spin mb-3" />
      </div>
    );
  }

  // Review report modal
  if (showReview && reviewReport) {
    return (
      <div className="space-y-5 animate-fade-in">
        <div className="flex items-center gap-2 mb-1">
          <button
            onClick={() => { setShowReview(false); navigate('/task-package'); }}
            className="p-1 hover:bg-white/60 rounded-lg transition-colors"
            aria-label="返回"
          >
            <ArrowLeft size={18} className="text-subtext" />
          </button>
          <h1 className="text-lg font-extrabold text-ink">训练复盘</h1>
        </div>

        {/* 总分 */}
        <div className="app-card p-5 text-center bg-gradient-to-br from-primary/5 to-white/80">
          <div className="w-16 h-16 mx-auto mb-3 rounded-2xl bg-gradient-to-br from-primary to-primary-deep flex items-center justify-center shadow-glow-sm">
            <Shield size={30} className="text-white" />
          </div>
          <div className="text-3xl font-extrabold text-ink">{reviewReport.score} 分</div>
          <Badge variant={reviewReport.isSuccess ? 'success' : 'warning'} className="mt-1.5">
            {reviewReport.isSuccess ? '成功识破骗局 ✓' : '需要加强警惕'}
          </Badge>
        </div>

        {/* 行为分析 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="app-card p-4 border-emerald-200/60">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle2 size={16} className="text-emerald-600" aria-hidden />
              <span className="text-sm font-bold text-emerald-700">正确行为</span>
            </div>
            <ul className="space-y-1.5">
              {reviewReport.correctBehaviors.map((b, i) => (
                <li key={i} className="text-xs text-ink/80 flex items-start gap-1.5">
                  <span className="text-emerald-500 mt-0.5">+</span> {b}
                </li>
              ))}
            </ul>
          </div>
          <div className="app-card p-4 border-amber-200/60">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle size={16} className="text-amber-600" aria-hidden />
              <span className="text-sm font-bold text-amber-700">风险行为</span>
            </div>
            <ul className="space-y-1.5">
              {reviewReport.riskyBehaviors.map((b, i) => (
                <li key={i} className="text-xs text-ink/80 flex items-start gap-1.5">
                  <span className="text-amber-500 mt-0.5">-</span> {b}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* 证据清单 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="app-card p-4 border-emerald-200/60">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle2 size={14} className="text-emerald-600" />
              <span className="text-xs font-bold text-emerald-700">已识别证据</span>
              <span className="text-xs text-subtext">无</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {reviewReport.identifiedEvidence.map((ev, i) => (
                <Badge key={i} variant="success" size="sm">{ev}</Badge>
              ))}
              )}
            </div>
          </div>
          <div className="app-card p-4 border-amber-200/60">
            <div className="flex items-center gap-2 mb-2">
              <XCircle size={14} className="text-amber-600" />
              <span className="text-xs font-bold text-amber-700">遗漏证据</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {reviewReport.missedEvidence.map((ev, i) => (
                <Badge key={i} variant="warning" size="sm">{ev}</Badge>
              ))}
              )}
            </div>
          </div>
        </div>

        {/* 下一步建议 */}
        {reviewReport.nextSteps.length > 0 && (
          <div className="app-card p-4 border-blue-200/60 bg-blue-50/30">
            <h3 className="text-sm font-bold text-blue-700 mb-2">下一步建议</h3>
            <ul className="space-y-1.5">
              {reviewReport.nextSteps.map((step, i) => (
                <li key={i} className="text-xs text-ink/80 flex items-start gap-1.5">
                  <span className="text-blue-500 font-bold">{i + 1}.</span> {step}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* 能力变化 */}
        {reviewReport.abilityChange.length > 0 && (
          <div className="app-card p-4">
            <h3 className="text-sm font-bold text-ink mb-2">能力变化</h3>
            <div className="flex flex-wrap gap-2">
              {reviewReport.abilityChange.map((ac, i) => (
                <Badge
                  key={i}
                  variant={ac.direction === 'up' ? 'success' : ac.direction === 'down' ? 'warning' : 'default'}
                  size="sm"
                >
                  {ac.dimension} {ac.direction === 'up' ? `+${ac.delta}` : ac.delta}
                </Badge>
              ))}
            </div>
          </div>
        )}

        <div className="flex gap-2 justify-center pt-2">
          <Button variant="outline" onClick={() => { setShowReview(false); navigate('/task-package'); }}>
            返回任务包
          </Button>
          <Button onClick={() => { navigate('/assessment'); }}>
            重新测评
          </Button>
        </div>
      </div>
    );
  }

  const messages = scenarioSession?.messages ?? [];
  const scenarioName = SCENARIO_TYPES[scenarioSession?.scenarioType ?? ''] ?? '情景训练';
  const currentState = (scenarioSession?.currentState ?? 'S0') as ScenarioState;

  return (
    <div className="flex flex-col h-[calc(100vh-240px)] md:h-[calc(100vh-180px)] animate-slide-up">
      {/* 顶部导航 */}
      <div className="flex items-center justify-between mb-3 flex-shrink-0">
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/task-package')}
            className="p-1 hover:bg-white/60 rounded-lg transition-colors"
            aria-label="返回"
          >
            <ArrowLeft size={18} className="text-subtext" />
          </button>
          <div>
            <h1 className="text-base font-bold text-ink">{scenarioName}</h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* 状态指示 */}
          <Badge variant="info" size="sm">
            {STATE_LABELS[currentState] ?? currentState}
          </Badge>
          {/* 证据计数 */}
          {(scenarioSession?.identifiedEvidence?.length ?? 0) > 0 && (
            <Badge variant="success" size="sm">
              <CheckCircle2 size={10} aria-hidden />
              {scenarioSession?.identifiedEvidence.length} 证据
            </Badge>
          )}
          {!isFinished && (
            <Button variant="ghost" size="sm" onClick={handleFinishEarly}>
              结束对话
            </Button>
          )}
        </div>
      </div>

      {/* 证据列表 */}
      {(scenarioSession?.identifiedEvidence?.length ?? 0) > 0 && (
        <div className="app-card p-2.5 mb-3 flex-shrink-0 flex flex-wrap gap-1.5 items-center">
          {scenarioSession?.identifiedEvidence.map((ev, i) => (
            <Badge key={i} variant="success" size="sm">{ev}</Badge>
          ))}
        </div>
      )}

      {/* 消息区域 */}
      <div className="flex-1 overflow-y-auto space-y-3 mb-3 pr-1">
        {messages.length === 0 && (
          <div className="text-center text-subtext py-8">
            <MessageSquare size={32} className="mx-auto mb-2 opacity-30" />
            <p className="text-sm">对话即将开始...</p>
          </div>
        )}
        {messages.map((msg) => (
          <ChatBubble key={msg.id} message={msg} />
        ))}

        {/* Finished message */}
        {isFinished && (
          <div className="app-card border-amber-200/60 bg-amber-50/60 p-4 text-center">
            <Siren size={24} className="text-amber-500 mx-auto mb-2" />
            <Button size="sm" onClick={() => setShowReview(true)}>
              查看复盘
            </Button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      {!isFinished && (
        <div className="flex-shrink-0 flex gap-2 items-center">
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入你的回复..."
              disabled={isLoading}
              className="w-full px-4 py-2.5 pr-10 rounded-xl border border-white/60 bg-white/70 text-sm text-ink placeholder:text-subtext/50 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40 transition-all"
            />
          </div>
          <Button
            size="icon"
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            loading={isLoading}
            className="flex-shrink-0"
            aria-label="发送消息"
          >
            <Send size={16} aria-hidden />
          </Button>
        </div>
      )}
    </div>
  );
}

/** 聊天气泡 */
function ChatBubble({ message }: { message: ScenarioMessage }) {
  const isUser = message.speaker === 'user';
  const isSystem = message.speaker === 'system';

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <span className="text-xs text-subtext/60 bg-white/40 px-3 py-1 rounded-full">
          {message.content}
        </span>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
        {/* 说话者标签 */}
        <span className={`text-[10px] font-semibold mb-0.5 block ${isUser ? 'text-right text-primary' : 'text-subtext'}`}>
          {isUser ? '你' : '对方'}
          {message.state && (
            <span className="ml-1 opacity-60">· {message.state}</span>
          )}
        </span>
        {/* 气泡 */}
        <div className={`px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed ${
          isUser
            ? 'bg-primary text-white rounded-br-md'
            : 'bg-white/80 border border-white/60 text-ink rounded-bl-md shadow-sm'
        }`}>
          {message.content}
          {/* 证据标签 */}
          {message.evidenceTag && (
            <div className="mt-1.5">
              <Badge variant="warning" size="sm">
                <AlertTriangle size={10} aria-hidden />
                {message.evidenceTag}
              </Badge>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
