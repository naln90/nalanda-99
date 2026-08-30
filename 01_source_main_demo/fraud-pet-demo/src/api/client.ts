/**
 * API Client — 前端与后端的通信桥梁
 *
 * 所有后端响应在此层通过 transform 函数转换为前端 TypeScript 类型，
 * 确保组件代码不需要关心后端实际返回格式的差异。
 */

import type {
  AbilityDimension,
  AbilityProfile,
  AICallLog,
  AssessmentQuestion,
  AssessmentResult,
  DashboardSummary,
  DimensionScore,
  EvidenceOverview,
  Pet,
  PetStage,
  PromptVersion,
  ReviewReport,
  ScenarioMessage,
  ScenarioSession,
  ScenarioState,
  TaskPackage,
  TaskPackageItem,
  TrainingTask,
  TrainingTaskDetail,
  User,
  ThemeInfo,
  ThemeItem,
  VideoLibraryEntry,
  EnergyBalance,
  EnergyLedgerEntry,
  ActivityInfo,
  SchoolDashboard,
} from '../types';
import type {
  CampusActivity,
  GoalValidation,
  LearningArtifact,
  LearningDashboard,
  LearningGoal,
  LearningPlan,
  LearningPlanItem,
  LearningTemplate,
  MarketListing,
  MarketComment,
  NotificationItem,
  Team,
  TeamMember,
  Milestone,
  ProjectIssue,
  ArtifactSummary,
  MarketRecommendation,
  StudyReminder,
  ArtifactReview,
  CodeDebugResult,
  PlanExtension,
  CampusAuthConfig,
} from '../types/learning';

// 默认走相对路径 /api：本地 dev 由 vite 代理转发，容器内由 nginx 反代到后端。
// 如需独立域名部署，可在构建时注入 VITE_API_BASE_URL=https://your-domain.com/api
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '');

export interface PetPoolItem {
  name: string;
  category: Pet['category'];
  desc: string;
}

export interface LoginResponse {
  currentUser: User;
  hasCompletedAssessment: boolean;
  hasPet: boolean;
  nickname?: string;
  token?: string;
}

export interface PetResponse {
  pet: Pet;
  currentUser?: User;
}

export interface TrainingSubmitResponse {
  score: number;
  accuracy: number;
  growth: {
    basePoints: number;
    accuracyBonus: number;
    difficultyBonus: number;
    finalGrowth: number;
  };
  rewardStatus: 'AWARDED' | 'NO_REWARD';
  rewardMessage: string;
  pet: Pet;
}

export interface RiskAnalyzeResponse {
  riskScore: number;
  riskLevel: '低风险' | '中风险' | '高风险';
  fraudType: string;
  evidence: string[];
  suggestions: string[];
  growthAwarded: number;
  rewardStatus: 'AWARDED' | 'NO_REWARD';
  complianceNotice: string;
}

export interface RankingRow {
  rank: number;
  petId: string;
  ownerId: string;
  petType: string;
  level: number;
  growthValue: number;
  lastTrainingAt: string;
  distanceToPrevious?: number;
}

export interface RankingResponse {
  type: string;
  myRank: RankingRow | null;
  list: RankingRow[];
  sortRule: string[];
  privacyNotice: string;
}

export interface TrainingRecordItem {
  taskId: string;
  score: number;
  accuracy: number;
  finalGrowth: number;
  rewardStatus: 'AWARDED' | 'NO_REWARD';
  rewardMessage: string;
  createdAt: string;
}

export interface RecordsResponse {
  trainingRecords: TrainingRecordItem[];
}

const SESSION_KEY = 'fzzy.session';

function getAuthToken(): string | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as { token?: string };
    return data.token ?? null;
  } catch {
    return null;
  }
}

// ==================== 统一错误模型 ====================
// 对外只暴露对用户友好的文案，原始错误细节仅保留在 detail 中（R1/P1）
export class ApiError extends Error {
  status: number;
  detail?: unknown;
  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

const STATUS_MESSAGES: Record<number, string> = {
  400: '请求参数有误，请检查输入内容',
  401: '登录状态已失效，请重新登录',
  403: '没有权限执行该操作',
  404: '请求的内容不存在或已被移除',
  409: '操作冲突，请刷新页面后重试',
  413: '文件过大，请压缩后重试',
  415: '不支持的文件类型',
  422: '提交内容未通过校验，请检查后重试',
  500: '服务器开小差了，请稍后重试',
  502: '服务暂时不可用，请稍后重试',
  503: '服务暂时不可用，请稍后重试',
  504: '服务响应超时，请稍后重试',
};

function extractServerMessage(body: unknown): string | undefined {
  if (!body || typeof body !== 'object') return undefined;
  const obj = body as Record<string, unknown>;
  if (typeof obj.detail === 'string') return obj.detail;
  if (typeof obj.message === 'string') return obj.message;
  if (typeof obj.error === 'string') return obj.error;
  return undefined;
}

/** 将任意错误（网络错误 / HTTP 错误）归一为对用户友好的 ApiError */
export function toFriendlyError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;
  if (error instanceof TypeError && /fetch|network|failed/i.test(error.message)) {
    return new ApiError(0, '网络连接失败，请检查网络后重试');
  }
  if (error instanceof Error) {
    return new ApiError(0, error.message || '操作失败，请稍后重试');
  }
  return new ApiError(0, '操作失败，请稍后重试');
}

function buildAuthHeaders(): Record<string, string> {
  const token = getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ==================== 文件上传（前端侧校验 + 统一错误） ====================
const IMAGE_MAX_SIZE = 10 * 1024 * 1024; // 10MB
const ARTIFACT_MAX_SIZE = 25 * 1024 * 1024; // 25MB
const ALLOWED_IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/webp', 'image/gif'];

function validateFile(file: File, allowedTypes: string[], maxSize: number, kind: string): void {
  if (!file || file.size === 0) throw new ApiError(400, `请选择要上传的${kind}文件`);
  if (file.size > maxSize) {
    throw new ApiError(413, `文件过大，请控制在 ${Math.round(maxSize / 1024 / 1024)}MB 以内`);
  }
  if (allowedTypes.length > 0 && file.type && !allowedTypes.includes(file.type)) {
    throw new ApiError(415, `不支持的文件类型，请上传${kind}支持的格式`);
  }
}

async function apiUpload<T>(path: string, file: File, fieldName = 'file'): Promise<T> {
  const form = new FormData();
  form.append(fieldName, file);
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: buildAuthHeaders(),
      body: form,
    });
  } catch {
    throw new ApiError(0, '网络连接失败，请检查网络后重试');
  }
  if (!response.ok) {
    let detail: unknown;
    let serverMsg: string | undefined;
    try {
      const data = await response.json();
      detail = data;
      serverMsg = extractServerMessage(data);
    } catch {
      // 忽略非 JSON 响应
    }
    const friendly = STATUS_MESSAGES[response.status] ?? `上传失败（${response.status}）`;
    throw new ApiError(response.status, serverMsg ?? friendly, detail);
  }
  return response.json() as Promise<T>;
}

function buildHeaders(custom: HeadersInit = {}): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  const token = getAuthToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const merged = { ...headers, ...(custom as Record<string, string>) };
  return merged;
}

async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: buildHeaders(options.headers),
    });
  } catch {
    throw new ApiError(0, '网络连接失败，请检查网络后重试');
  }
  if (!response.ok) {
    let detail: unknown;
    let serverMsg: string | undefined;
    try {
      const data = await response.json();
      detail = data;
      serverMsg = extractServerMessage(data);
    } catch {
      // 非 JSON 响应体，忽略解析错误
    }
    const friendly = STATUS_MESSAGES[response.status] ?? `请求失败（${response.status}）`;
    const message = serverMsg && serverMsg !== friendly ? `${friendly}：${serverMsg}` : friendly;
    throw new ApiError(response.status, message, detail);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

// ==================== 响应转换函数 ====================

const DIMENSIONS: AbilityDimension[] = ['辨识力', '判断力', '应变力', '实证力', '协作力'];

// 旧维度名（去反诈化前）-> 新维度名，用于兼容后端尚未热更新的历史返回
export const DIMENSION_KEY_MAP: Record<string, AbilityDimension> = {
  '识诈力': '辨识力',
  '判断力': '判断力',
  '应对力': '应变力',
  '证据力': '实证力',
  '求助力': '协作力',
};

/** 将后端返回的维度得分键归一为当前主题无关维度名（兼容旧版后端 / 历史数据） */
function normalizeScoreKeys(scores: Record<string, number> | undefined): Record<string, number> {
  const out: Record<string, number> = {};
  for (const [k, v] of Object.entries(scores ?? {})) {
    const nk = DIMENSION_KEY_MAP[k] ?? (k as AbilityDimension);
    out[nk] = v;
  }
  return out;
}

/** 将后端 scores dict 转换为前端 DimensionScore[]（键已归一为中性维度名） */
function transformScoresToDimensions(scores: Record<string, number>): DimensionScore[] {
  const norm = normalizeScoreKeys(scores);
  return DIMENSIONS.map((dim) => ({
    dimension: dim,
    score: norm[dim] ?? 0,
    maxScore: 100,
    percentage: norm[dim] ?? 0,
  }));
}

/** 计算能力等级（主题无关，与后端 v1 _compute_level 规则一致） */
export function computeLevel(overallScore: number): string {
  if (overallScore >= 85) return '综合卓越';
  if (overallScore >= 70) return '综合优秀';
  if (overallScore >= 50) return '综合良好';
  return '综合入门';
}

/** 转换后端 AbilityProfile → 前端 AbilityProfile */
function transformAbilityProfile(raw: any): AbilityProfile | null {
  if (!raw) return null;
  // 后端返回可能是 dict（dashboard）或带 scores 的结构（assessment）
  if (raw.scores && typeof raw.scores === 'object' && !Array.isArray(raw.scores)) {
    // 格式: {scores: {辨识力: 60, ...}, weakDimensions, overallScore, descriptions, suggestions}
    const scores = normalizeScoreKeys(raw.scores as Record<string, number>);
    const dimensions = transformScoresToDimensions(scores);
    const weakDimensions = ((raw.weakDimensions ?? []) as string[]).map(
      (k) => DIMENSION_KEY_MAP[k] ?? k,
    ) as AbilityDimension[];
    const strongDimensions = DIMENSIONS.filter((d) => (scores[d] ?? 0) >= 80);
    const overallScore = raw.overallScore ?? Math.round(dimensions.reduce((s, d) => s + d.score, 0) / dimensions.length);
    return {
      dimensions,
      overallScore,
      weakDimensions,
      strongDimensions,
      level: computeLevel(overallScore),
    };
  } else if (typeof raw === 'object' && !raw.scores) {
    // 格式: {辨识力: 60, 判断力: 40, ...} — dashboard 的 abilityProfile 字段
    const scores = normalizeScoreKeys(raw as Record<string, number>);
    const dimensions = transformScoresToDimensions(scores);
    const weakDimensions = DIMENSIONS.filter((d) => (scores[d] ?? 0) < 60);
    const strongDimensions = DIMENSIONS.filter((d) => (scores[d] ?? 0) >= 80);
    const overallScore = Math.round(dimensions.reduce((s, d) => s + d.score, 0) / dimensions.length);
    return {
      dimensions,
      overallScore,
      weakDimensions,
      strongDimensions,
      level: computeLevel(overallScore),
    };
  }
  return null;
}

/** 转换后端 Dashboard Summary → 前端 DashboardSummary */
function transformDashboard(raw: any): DashboardSummary {
  const user: User = {
    ownerId: raw.ownerId ?? '',
    hasCompletedAssessment: raw.hasCompletedAssessment ?? false,
    hasPet: raw.hasPet ?? false,
  };

  const abilityProfile = transformAbilityProfile(raw.abilityProfile);

  // 后端 packageProgress → 前端 activeTaskPackage
  let activeTaskPackage: TaskPackage | null = null;
  if (raw.packageProgress) {
    const pp = raw.packageProgress;
    activeTaskPackage = {
      id: 0, // 后端用 string id, 前端用 number — 这里用 0 占位（不影响展示）
      ownerId: raw.ownerId ?? '',
      planType: pp.planType ?? '7day',
      status: 'active',
      items: [], // 实际 items 需要通过 getCurrentTaskPackage 获取
      totalDays: pp.planType === '14day' ? 14 : 7,
      completedDays: pp.completedItems ?? 0,
      progress: pp.progressPercent ?? 0,
      createdAt: new Date().toISOString(),
      expiresAt: null,
      abilitySnapshot: abilityProfile ?? {
        dimensions: DIMENSIONS.map(d => ({ dimension: d, score: 0, maxScore: 100, percentage: 0 })),
        overallScore: 0,
        weakDimensions: [],
        strongDimensions: [],
        level: '幼崽期',
      },
    };
  }

  return {
    user,
    pet: raw.pet ?? null,
    abilityProfile,
    activeTaskPackage,
    todayTrainingCount: 0,
    totalTrainingCount: raw.recentTrainingCount ?? 0,
    consecutiveDays: 0,
    pendingRetrains: raw.dueRetrainCount ?? 0,
    recentAICallCount: 0,
    lastTrainingAt: null,
  };
}

/** 转换后端 Task Package (generate / current) → 前端 TaskPackage */
function transformTaskPackage(raw: any): TaskPackage {
  // v1 current 接口返回: {taskPackage: {...}}；v1 generate 直接返回 {...items}
  const pkgRaw = raw?.taskPackage ?? raw;
  const items = pkgRaw?.items ?? raw?.items ?? [];

  if (pkgRaw?.packageId && items) {
    const totalDays = pkgRaw.totalDays ?? (pkgRaw.planType === '14day' ? 14 : 7);
    const completedCount = items.filter((i: any) => i.status === 'completed').length;
    const progress = pkgRaw.progress ?? (items.length > 0 ? Math.round(completedCount / items.length * 100) : 0);

    return {
      id: 0,
      ownerId: '', // ownerId 在请求中发送，后端不返回
      planType: pkgRaw.planType ?? '7day',
      status: pkgRaw.status ?? 'active',
      items: items.map(transformTaskPackageItem),
      totalDays,
      completedDays: completedCount,
      progress,
      createdAt: pkgRaw.createdAt ?? new Date().toISOString(),
      expiresAt: pkgRaw.expiresAt ?? null,
      abilitySnapshot: {
        dimensions: DIMENSIONS.map(d => ({ dimension: d, score: 0, maxScore: 100, percentage: 0 })),
        overallScore: 0,
        weakDimensions: [],
        strongDimensions: [],
        level: '幼崽期',
      },
    };
  }

  // 兜底
  return {
    id: 0,
    ownerId: '',
    planType: '7day',
    status: 'active',
    items: [],
    totalDays: 7,
    completedDays: 0,
    progress: 0,
    createdAt: new Date().toISOString(),
    expiresAt: null,
    abilitySnapshot: {
      dimensions: DIMENSIONS.map(d => ({ dimension: d, score: 0, maxScore: 100, percentage: 0 })),
      overallScore: 0,
      weakDimensions: [],
      strongDimensions: [],
      level: '幼崽期',
    },
  };
}

/** 转换后端 Task Package Item → 前端 TaskPackageItem */
function transformTaskPackageItem(raw: any): TaskPackageItem {
  // 后端: {id: "item-xxx", dayIndex, taskType: "scenario_training", taskRef, taskTitle, targetAbility, estimatedMinutes, status}
  // 前端: {id: number, day, dimension, title, description, taskType, fraudType, isCompleted, completedAt, score}
  const taskTypeMap: Record<string, TaskPackageItem['taskType']> = {
    'scenario_training': 'scenario',  // 旧格式
    'assessment_review': 'assessment',  // 旧格式
    'risk_check': 'scenario',  // 旧格式
    'knowledge_read': 'knowledge',  // 旧格式
    'retrain': 'retrain',
    // 新格式（Phase 1.4 直接发送）
    'scenario': 'scenario',
    'assessment': 'assessment',
    'knowledge': 'knowledge',
  };

  return {
    id: raw.id ?? '', // 后端用 string id (如 "item-xxx")
    day: raw.dayIndex ?? 1,
    dimension: (raw.targetAbility ?? '辨识力') as AbilityDimension,
    title: raw.taskTitle ?? '训练任务',
    description: `${raw.estimatedMinutes ?? 15} 分钟 · ${raw.targetAbility ?? '辨识力'}维度提升`,
    taskType: taskTypeMap[raw.taskType] ?? 'scenario',
    fraudType: raw.taskRef ?? 'brush_orders',
    isCompleted: raw.status === 'completed',
    completedAt: raw.completedAt ?? null,
    score: raw.score ?? null,
  };
}

/** 转换后端 Scenario Start → 前端 ScenarioSession */
function transformScenarioStart(raw: any): ScenarioSession {
  const now = new Date().toISOString();
  return {
    sessionId: raw.sessionId ?? '',
    ownerId: '', // ownerId 在请求中发送，后端不返回
    scenarioType: raw.scenarioType ?? 'brush_orders',
    currentState: (raw.currentState ?? 'S0') as ScenarioState,
    messages: [
      {
        id: 'msg-system-0',
        speaker: 'system',
        content: `情景训练开始：${raw.scenarioType ?? '刷单返利'}`,
        state: raw.currentState ?? 'S0',
        timestamp: now,
      },
      {
        id: 'msg-ai-0',
        speaker: 'ai',
        content: raw.initialMessage ?? '你好，我是你的情景训练伙伴。',
        state: raw.currentState ?? 'S0',
        timestamp: now,
      },
    ],
    identifiedEvidence: [],
    missedEvidence: raw.allEvidence ?? [],
    score: 0,
    isSuccess: false,
    startedAt: now,
    finishedAt: null,
  };
}

/** v1: 转换后端 Scenario Start → 前端 ScenarioSession */
function transformScenarioStartV1(raw: any): ScenarioSession {
  const now = new Date().toISOString();
  return {
    sessionId: raw.sessionId ?? '',
    ownerId: '',
    scenarioType: raw.scenarioType ?? '刷单返利',
    currentState: (raw.currentState ?? 'S0') as ScenarioState,
    messages: [
      {
        id: 'msg-system-0',
        speaker: 'system',
        content: `情景训练开始：${raw.scenarioType ?? '刷单返利'}`,
        state: raw.currentState ?? 'S0',
        timestamp: now,
      },
      {
        id: 'msg-ai-0',
        speaker: 'ai',
        content: raw.initialMessage ?? '你好，我是你的情景训练伙伴。',
        state: raw.currentState ?? 'S0',
        timestamp: now,
      },
    ],
    identifiedEvidence: [],
    missedEvidence: raw.allEvidence ?? [],
    score: 0,
    isSuccess: false,
    startedAt: now,
    finishedAt: null,
  };
}

/** 转换后端 Scenario Reply → 前端需要的格式 */
function transformScenarioReply(raw: any): { reply: string; state: string; behavior: string; identifiedEvidence: string[]; newEvidence: string[]; isTerminal: boolean; isCompleted: boolean } {
  return {
    reply: raw.scammerReply ?? '',
    state: raw.newState ?? 'S0',
    behavior: raw.behavior ?? 'other',
    identifiedEvidence: raw.identifiedEvidence ?? [],
    newEvidence: raw.newEvidence ?? [],
    isTerminal: raw.isTerminal ?? false,
    isCompleted: raw.isCompleted ?? false,
  };
}

/** 转换后端 Review → 前端 ReviewReport */
function transformReviewReport(raw: any): ReviewReport {
  // 后端 correctBehaviors / riskyBehaviors 可能是 [{behavior, message, state}] 或 string[]
  const correctBehaviors = (raw.correctBehaviors ?? []).map((b: any) =>
    typeof b === 'string' ? b : b.behavior ?? b.message ?? ''
  );
  const riskyBehaviors = (raw.riskyBehaviors ?? []).map((b: any) =>
    typeof b === 'string' ? b : b.behavior ?? b.message ?? ''
  );

  // 后端 abilityChange: {辨识力: 10, 应变力: 8} → 前端 AbilityDelta[]
  const abilityChange: ReviewReport['abilityChange'] = [];
  if (raw.abilityChange && typeof raw.abilityChange === 'object') {
    for (const [dim, delta] of Object.entries(raw.abilityChange as Record<string, number>)) {
      if (DIMENSIONS.includes(dim as AbilityDimension)) {
        abilityChange.push({
          dimension: dim as AbilityDimension,
          delta: delta,
          direction: delta > 0 ? 'up' : delta < 0 ? 'down' : 'stable',
        });
      }
    }
  }

  return {
    identifiedEvidence: raw.identifiedEvidence ?? [],
    missedEvidence: raw.missedEvidence ?? [],
    correctBehaviors,
    riskyBehaviors,
    nextSteps: raw.nextSteps ?? [],
    abilityChange,
    reviewSummary: raw.reviewSummary ?? '',
    score: raw.score ?? 0,
    isSuccess: raw.isSuccess ?? false,
  };
}

/** 转换后端 Evidence Overview → 前端 EvidenceOverview */
function transformEvidenceOverview(raw: any): EvidenceOverview {
  // 后端格式: {totalCalls, safetyBlocked, fallbackUsed, avgResponseTime, totalTokens, byType, promptVersions, modelInfo}
  // 前端格式: {totalCalls, successRate, avgLatencyMs, callTypeBreakdown, promptVersions: string[], dateRange}

  const totalCalls = raw.totalCalls ?? 0;
  const safetyBlocked = raw.safetyBlocked ?? 0;
  const successRate = totalCalls > 0 ? (totalCalls - safetyBlocked) / totalCalls : 1;

  // byType 可能是 {dialogue: {count: 5, avgResponseTime: 120}} 或 {dialogue: 5}
  const callTypeBreakdown: Record<string, number> = {};
  if (raw.byType && typeof raw.byType === 'object') {
    for (const [type, val] of Object.entries(raw.byType as Record<string, any>)) {
      callTypeBreakdown[type] = typeof val === 'object' ? val.count ?? 0 : val;
    }
  }

  // promptVersions 可能是 {dialogue: "v1.0", ...} 或 string[]
  let promptVersions: string[] = [];
  if (raw.promptVersions && typeof raw.promptVersions === 'object') {
    promptVersions = Object.entries(raw.promptVersions as Record<string, string>).map(
      ([type, version]) => `${type}: ${version}`
    );
  }

  const now = new Date();
  const dateRange = {
    from: new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10),
    to: now.toISOString().slice(0, 10),
  };

  return {
    totalCalls,
    successRate,
    avgLatencyMs: raw.avgResponseTime ?? 0,
    callTypeBreakdown,
    promptVersions,
    dateRange,
  };
}

/** 转换后端 AI Log → 前端 AICallLog */
function transformAILog(raw: any): AICallLog {
  return {
    id: raw.id ?? 0,
    callType: raw.callType ?? '',
    promptVersion: raw.promptVersion ?? '',
    inputSummary: raw.inputSummary ?? '',
    outputSummary: typeof raw.outputStruct === 'string' ? raw.outputStruct.slice(0, 100) : JSON.stringify(raw.outputStruct ?? {}).slice(0, 100),
    modelUsed: raw.modelName ?? '',
    latencyMs: raw.responseTimeMs ?? 0,
    tokenCount: raw.tokenUsage ?? null,
    isSuccess: !(raw.safetyBlocked ?? false) && !(raw.errorMessage ?? false),
    errorMessage: raw.errorMessage ?? null,
    createdAt: raw.createdAt ?? new Date().toISOString(),
  };
}

// ==================== API 函数 ====================

export const api = {
  // ========== 认证 ==========
  demoLogin(ownerId: string) {
    return apiRequest<LoginResponse>('/auth/demo-login', {
      method: 'POST',
      body: JSON.stringify({ ownerId }),
    });
  },
  register(username: string, password: string, nickname = '') {
    return apiRequest<LoginResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, nickname }),
    });
  },
  login(username: string, password: string) {
    return apiRequest<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  },

  // ========== 测评 ==========
  getAssessmentQuestions(count: number = 5) {
    return apiRequest<{ questions: AssessmentQuestion[] }>(`/assessment/questions?count=${count}`);
  },
  submitAssessment(ownerId: string, answers: Array<{ questionId: string; answer: string | string[] }> = []) {
    return apiRequest<AssessmentResult>('/assessment/submit', {
      method: 'POST',
      body: JSON.stringify({ ownerId, answers }),
    });
  },

  // ── v1 测评 API（Phase 1.2：基于会话的测评）──

  /** 创建测评会话 */
  createAssessmentSession(ownerId: string, mode: 'quick' | 'standard' = 'quick') {
    return apiRequest<{
      sessionId: string;
      mode: string;
      totalQuestions: number;
      questions: AssessmentQuestion[];
    }>('/v1/assessment/sessions', {
      method: 'POST',
      body: JSON.stringify({ ownerId, mode }),
    });
  },

  /** 提交单题答案 */
  submitAssessmentAnswer(sessionId: string, questionId: string, answer: string | string[]) {
    return apiRequest<{
      isCorrect: boolean;
      score: number;
      correctAnswer: string | string[];
      explanation: string;
      alreadyAnswered: boolean;
    }>('/v1/assessment/sessions/answer', {
      method: 'POST',
      body: JSON.stringify({ sessionId, questionId, answer }),
    });
  },

  /** 完成测评会话 */
  completeAssessmentSession(sessionId: string) {
    return apiRequest<AssessmentResult & {
      sessionId: string;
      abilityProfile: { scores: Record<string, number>; weakDimensions: string[] };
    }>('/v1/assessment/sessions/complete', {
      method: 'POST',
      body: JSON.stringify({ sessionId }),
    });
  },

  // ========== v1 能力画像 (Phase 1.3) ==========

  /** 获取综合能力画像（含历史趋势可选） */
  getAbilityProfileV1(ownerId: string, includeHistory = false) {
    const params = new URLSearchParams({ ownerId });
    if (includeHistory) params.set('includeHistory', 'true');
    return apiRequest<{
      profile: AbilityProfile & { petStage: string; assessmentTime: string } | null;
      hasCompletedAssessment: boolean;
      history?: { id: number; scores: Record<string, number>; overallScore: number; triggerEvent: string; createdAt: string }[];
      message?: string;
    }>(`/v1/assessment/ability-profile?${params.toString()}`);
  },

  // ========== 宠物 ==========
  getPetsPool() {
    return apiRequest<{ pets: PetPoolItem[] }>('/pets/pool');
  },
  claimPet(ownerId: string, petType: string, petName?: string, avatarEmoji?: string) {
    return apiRequest<PetResponse>('/pets/claim', {
      method: 'POST',
      body: JSON.stringify({ ownerId, petType, petName: petName || null, avatarEmoji: avatarEmoji || null }),
    });
  },
  updatePetProfile(ownerId: string, data: { petName?: string | null; avatarEmoji?: string | null }) {
    return apiRequest<PetResponse>('/pets/profile', {
      method: 'PATCH',
      body: JSON.stringify({ ownerId, ...data }),
    });
  },
  getMyPet(ownerId: string) {
    return apiRequest<PetResponse>(`/pets/my?ownerId=${encodeURIComponent(ownerId)}`);
  },
  getPetStages() {
    return apiRequest<{ stages: PetStage[] }>('/pets/stages');
  },

  // ========== 训练 ==========
  getTrainingTasks() {
    return apiRequest<{ tasks: TrainingTask[] }>('/training/tasks');
  },
  getTrainingTask(taskId: string) {
    return apiRequest<TrainingTaskDetail>(`/training/tasks/${taskId}`);
  },
  submitTraining(ownerId: string, taskId: string, answers: Array<{ questionId: string; answer: string[] }>, mode = 'recommended') {
    return apiRequest<TrainingSubmitResponse>('/training/submit', {
      method: 'POST',
      body: JSON.stringify({ ownerId, taskId, answers, mode }),
    });
  },

  // ========== 风险分析 ==========
  analyzeRisk(ownerId: string, text: string, sourceType = '聊天记录') {
    return apiRequest<RiskAnalyzeResponse>('/risk/analyze', {
      method: 'POST',
      body: JSON.stringify({ ownerId, text, sourceType }),
    });
  },
  analyzeRiskAI(ownerId: string, text: string, sourceType = '聊天记录') {
    return apiRequest<RiskAnalyzeResponse & { aiEnhanced: boolean }>('/risk/analyze-ai', {
      method: 'POST',
      body: JSON.stringify({ ownerId, text, sourceType }),
    });
  },

  // ========== 排行榜 ==========
  getRanking(type = 'total', ownerId?: string) {
    const params = new URLSearchParams({ type });
    if (ownerId) params.set('ownerId', ownerId);
    return apiRequest<RankingResponse>(`/ranking?${params.toString()}`);
  },

  // ========== 知识库 ==========
  getKnowledgeCategories(theme?: string) {
    const query = theme ? `?theme=${encodeURIComponent(theme)}` : '';
    return apiRequest<{ categories: string[] }>(`/knowledge/categories${query}`);
  },
  getKnowledgeThemes() {
    return apiRequest<{ themes: Record<string, string[]> }>('/knowledge/themes');
  },
  getKnowledgeItems(category?: string, theme?: string) {
    const params = new URLSearchParams();
    if (category) params.set('category', category);
    if (theme) params.set('theme', theme);
    const query = params.toString() ? `?${params.toString()}` : '';
    return apiRequest<{ items: import('../types').KnowledgeItem[] }>(`/knowledge/items${query}`);
  },
  /** 上传聊天截图，返回 OCR 文本与推荐分类（图片识别搜索） */
  async analyzeImage(file: File) {
    validateFile(file, ALLOWED_IMAGE_TYPES, IMAGE_MAX_SIZE, '图片');
    return apiUpload<{
      success: boolean;
      filename: string;
      fileSize?: number;
      extractedText?: string;
      fraudType?: string;
      riskLevel?: string;
      confidence?: number;
      matchedKeywords?: string[];
      suggestedKeywords?: string[];
      suggestedCategories?: string[];
      isSafe?: boolean;
      analysisNote?: string;
      analyzedAt?: string;
      error?: string;
    }>(`/knowledge/analyze-image`, file, 'image');
  },

  // ========== 记录 ==========
  getRecords(ownerId: string) {
    return apiRequest<RecordsResponse>(`/records?ownerId=${encodeURIComponent(ownerId)}`);
  },

  // ========== 仪表盘 (带转换) ==========
  async getDashboard(ownerId: string): Promise<DashboardSummary> {
    const raw = await apiRequest<any>(`/dashboard/summary?ownerId=${encodeURIComponent(ownerId)}`);
    return transformDashboard(raw);
  },

  // ========== 能力画像 (带转换) ==========
  async getAbilityProfile(ownerId: string): Promise<{ profile: AbilityProfile | null }> {
    const raw = await apiRequest<any>(`/assessment/ability-profile?ownerId=${encodeURIComponent(ownerId)}`);
    if (!raw.profile) return { profile: null };
    return { profile: transformAbilityProfile(raw.profile) };
  },

  // ========== AI 任务包 (带转换) ==========
  async generateTaskPackage(ownerId: string, planType: '7day' | '14day'): Promise<TaskPackage> {
    const raw = await apiRequest<any>('/v1/task-package/generate', {
      method: 'POST',
      body: JSON.stringify({ ownerId, planType }),
    });
    // v1: 如果后端返回 "已有进行中的任务包"，需要拉取当前任务包
    if (raw.message && raw.packageId && !raw.items) {
      const currentRaw = await apiRequest<any>(`/v1/task-package/current?ownerId=${encodeURIComponent(ownerId)}`);
      return transformTaskPackage(currentRaw);
    }
    return transformTaskPackage(raw);
  },
  async getCurrentTaskPackage(ownerId: string): Promise<{ taskPackage: TaskPackage | null }> {
    const raw = await apiRequest<any>(`/v1/task-package/current?ownerId=${encodeURIComponent(ownerId)}`);
    if (!raw.taskPackage) return { taskPackage: null };
    return { taskPackage: transformTaskPackage(raw) };
  },
  async completeTaskPackageItem(itemId: string, ownerId: string, score?: number | null): Promise<{ success: boolean; taskPackage: TaskPackage }> {
    // 调用后端完成端点
    await apiRequest<any>(`/task-package/items/${encodeURIComponent(itemId)}/complete`, {
      method: 'POST',
      body: JSON.stringify({ ownerId, score: score ?? null }),
    });
    // 完成后重新拉取当前任务包获取最新状态
    const raw = await apiRequest<any>(`/v1/task-package/current?ownerId=${encodeURIComponent(ownerId)}`);
    const taskPackage = raw.taskPackage ? transformTaskPackage(raw) : null;
    return { success: true, taskPackage: taskPackage ?? null as unknown as TaskPackage };
  },

  // ========== 情景对话训练 (带转换) ==========
  async startScenario(ownerId: string, scenarioType: string, taskId?: string): Promise<ScenarioSession> {
    // 后端需要 {ownerId, taskId}，不是 {ownerId, scenarioType}
    // taskId 是训练任务 ID (如 "task-001")，不是任务包条目 ID
    // 如果没有 taskId，使用 scenarioType 对应的训练任务 ID
    const taskRefMap: Record<string, string> = {
      brush_orders: 'task-brush-orders',
      brush: 'task-brush-orders',
      game_trade: 'task-game-trade',
      fake_customer_service: 'task-fake-cs',
      fake_teacher: 'task-fake-teacher',
      fake_recruitment: 'task-recruitment',
      investment: 'task-investment',
      refund: 'task-refund',
      '刷单返利': 'task-brush-orders',
      '游戏交易': 'task-game-trade',
      '虚假客服': 'task-fake-cs',
      '冒充老师': 'task-fake-teacher',
      '虚假招聘': 'task-recruitment',
      '虚假投资': 'task-investment',
    };

    // 如果有 taskIdFromQuery，直接使用；否则尝试映射
    const effectiveTaskId = taskId ?? taskRefMap[scenarioType] ?? 'task-brush-orders';

    const raw = await apiRequest<any>('/training/scenario/start', {
      method: 'POST',
      body: JSON.stringify({ ownerId, taskId: effectiveTaskId }),
    });
    return transformScenarioStart(raw);
  },
  async replyScenario(sessionId: string, ownerId: string, message: string): Promise<{ reply: string; state: string; behavior: string; identifiedEvidence: string[]; newEvidence: string[]; isTerminal: boolean; isCompleted: boolean }> {
    // 后端需要 {ownerId, message}
    const raw = await apiRequest<any>(`/training/scenario/${sessionId}/reply`, {
      method: 'POST',
      body: JSON.stringify({ ownerId, message }),
    });
    return transformScenarioReply(raw);
  },
  async finishScenario(sessionId: string, ownerId: string): Promise<{ session: ScenarioSession; review: ReviewReport }> {
    // 后端需要 {ownerId}
    const raw = await apiRequest<any>(`/training/scenario/${sessionId}/finish`, {
      method: 'POST',
      body: JSON.stringify({ ownerId }),
    });

    // 后端返回 {sessionId, review} — 没有 session 对象
    // 构造一个简单的 session 标记为完成
    const session: ScenarioSession = {
      sessionId: raw.sessionId ?? sessionId,
      ownerId,
      scenarioType: '',
      currentState: 'S5' as ScenarioState,
      messages: [],
      identifiedEvidence: [],
      missedEvidence: [],
      score: raw.review?.score ?? 0,
      isSuccess: raw.review?.isSuccess ?? false,
      startedAt: new Date().toISOString(),
      finishedAt: new Date().toISOString(),
    };

    const review = transformReviewReport(raw.review ?? {});

    return { session, review };
  },

  // ========== v1 情景训练 (State Machine + Rule-based, Phase 1.5) ==========
  /** v1: 以 scenarioType 直接启动，无需 taskId 映射。
   *  scenarioType 支持中文（"刷单返利"）和英文别名（"brush_orders"）。 */
  async startScenarioV1(ownerId: string, scenarioType: string): Promise<ScenarioSession> {
    // 英文别名 → 中文场景名（v1 后端使用中文 FSM key）
    const SCENARIO_ALIAS_MAP: Record<string, string> = {
      brush_orders: '刷单返利',
      brush: '刷单返利',
      brushing: '刷单返利',
      game_trade: '游戏交易',
      fake_customer_service: '虚假客服',
      fake_teacher: '冒充老师',
      fake_recruitment: '虚假招聘',
      scholarship: '奖助学金',
      ai_face_swap: 'AI换脸',
      training_loan: '求职培训贷',
      refund: '网购退款',
      investment: '虚假投资理财',
    };
    const resolvedType = SCENARIO_ALIAS_MAP[scenarioType] ?? scenarioType;

    const raw = await apiRequest<any>('/v1/training/scenario/start', {
      method: 'POST',
      body: JSON.stringify({ ownerId, scenarioType: resolvedType }),
    });
    return transformScenarioStartV1(raw);
  },
  /** v1: 发送消息推进 FSM */
  async replyScenarioV1(sessionId: string, message: string): Promise<{
    reply: string; state: string; behavior: string;
    identifiedEvidence: string[]; newEvidence: string[];
    isTerminal: boolean; isCompleted: boolean;
  }> {
    const raw = await apiRequest<any>(`/v1/training/scenario/${sessionId}/reply`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
    return {
      reply: raw.scammerReply ?? '',
      state: raw.newState ?? 'S0',
      behavior: raw.behavior ?? 'hesitate',
      identifiedEvidence: raw.identifiedEvidence ?? [],
      newEvidence: raw.newEvidence ?? [],
      isTerminal: raw.isTerminal ?? false,
      isCompleted: raw.isCompleted ?? false,
    };
  },
  /** v1: 结束训练，获取复盘报告 */
  async finishScenarioV1(sessionId: string): Promise<{ session: ScenarioSession; review: ReviewReport }> {
    const raw = await apiRequest<any>(`/v1/training/scenario/${sessionId}/finish`, {
      method: 'POST',
    });
    const session: ScenarioSession = {
      sessionId: raw.sessionId ?? sessionId,
      ownerId: '',
      scenarioType: '',
      currentState: 'S5' as ScenarioState,
      messages: [],
      identifiedEvidence: raw.review?.identifiedEvidence ?? [],
      missedEvidence: raw.review?.missedEvidence ?? [],
      score: raw.review?.score ?? 0,
      isSuccess: raw.review?.isSuccess ?? false,
      startedAt: new Date().toISOString(),
      finishedAt: new Date().toISOString(),
    };
    const review = transformReviewReport(raw.review ?? {});
    return { session, review };
  },
  /** v1: 获取会话详情（页面恢复/刷新） */
  async getScenarioSessionV1(sessionId: string): Promise<ScenarioSession> {
    const raw = await apiRequest<any>(`/v1/training/scenario/sessions/${sessionId}`);
    // 将会话消息转换为前端 ScenarioSession 格式
    const scenarioType = raw.scenarioType ?? '';
    const currentState = (raw.currentState ?? 'S0') as ScenarioState;
    const messages: ScenarioMessage[] = (raw.messages ?? []).map((m: any, i: number) => ({
      id: `msg-${m.role}-${i}`,
      speaker: m.role === 'scammer' ? 'ai' : m.role === 'user' ? 'user' : 'system',
      content: m.content ?? '',
      state: m.state ?? currentState,
      timestamp: m.timestamp ?? raw.startedAt,
    }));
    return {
      sessionId: raw.sessionId ?? '',
      ownerId: raw.ownerId ?? '',
      scenarioType,
      currentState,
      messages,
      identifiedEvidence: raw.identifiedEvidence ?? [],
      missedEvidence: [],
      score: 0,
      isSuccess: false,
      startedAt: raw.startedAt ?? new Date().toISOString(),
      finishedAt: raw.completedAt ?? null,
    };
  },

  // ========== 赛事证据中心 (带转换) ==========
  async getEvidenceOverview(ownerId?: string): Promise<EvidenceOverview> {
    const query = ownerId ? `?ownerId=${encodeURIComponent(ownerId)}` : '';
    const raw = await apiRequest<any>(`/evidence/overview${query}`);
    return transformEvidenceOverview(raw);
  },
  async getAILogs(ownerId?: string, limit = 20): Promise<{ logs: AICallLog[]; total: number }> {
    const params = new URLSearchParams({ limit: String(limit) });
    if (ownerId) params.set('ownerId', ownerId);
    const raw = await apiRequest<any>(`/evidence/ai-logs?${params.toString()}`);
    const logs = (raw.logs ?? []).map(transformAILog);
    return { logs, total: raw.total ?? logs.length };
  },
  async getPromptVersions(): Promise<{ versions: PromptVersion[] }> {
    const raw = await apiRequest<any>('/evidence/prompt-versions');
    // 后端返回: {versions: [{type, version, description}]}
    // 前端期望: {versions: PromptVersion[]} where PromptVersion = {version, callType, description, isActive, createdAt}
    const versions = (raw.versions ?? []).map((v: any) => ({
      version: v.version ?? '',
      callType: v.type ?? '',
      description: v.description ?? '',
      isActive: true,
      createdAt: new Date().toISOString(),
    }));
    return { versions };
  },

  // ========== 复训 ==========
  async getDueRetrains(ownerId: string): Promise<{ retrains: import('../types').RetrainTask[]; total: number }> {
    const raw = await apiRequest<any>(`/retrain/due?ownerId=${encodeURIComponent(ownerId)}`);
    const retrains = (raw.retrains ?? []).map((r: any) => ({
      id: r.id ?? 0,
      ownerId,
      originalQuestionId: r.originalQuestionId ?? '',
      variantStrategy: (r.variantStrategy ?? 'change_options_order') as import('../types').VariantStrategy,
      scheduledAt: r.scheduledAt ?? new Date().toISOString(),
      status: (r.status ?? 'pending') as 'pending' | 'completed' | 'skipped',
      completedAt: r.completedAt ?? null,
      intervalDays: r.attempt ?? 1,
    }));
    return { retrains, total: raw.total ?? retrains.length };
  },

  // ========== 辅导员看板 ==========
  async getCounselorDashboard(): Promise<{
    overview: { totalStudents: number; assessedRate: number; petRate: number; totalTraining: number; avgAccuracy: number };
    avgScores: Record<string, number>;
    weakDistribution: Array<{ dimension: string; count: number }>;
    fraudDistribution: Array<{ type: string; count: number }>;
    trainingTrend: Array<{ date: string; count: number }>;
    studentProfiles: Array<{ ownerId: string; overallScore: number; weakDimensions: string[]; accuracy: number; petLevel: number; lastAssessment: string }>;
  }> {
    return apiRequest<any>('/counselor/dashboard');
  },

  async getClassMeetingMaterials(): Promise<{
    generatedAt: string;
    classProfile: { totalAssessed: number; topWeakDimensions: Array<{ dimension: string; count: number }> };
    topics: Array<{ dimension: string; weakCount: number; topic: string; questions: string[]; activity: string }>;
    suggestions: string[];
  }> {
    return apiRequest<any>('/counselor/class-meeting');
  },

  // ========== AI 学习集市 ==========
  async getLearningTemplates(): Promise<{ templates: LearningTemplate[]; total: number }> {
    return apiRequest('/learning/templates');
  },

  async validateLearningGoal(payload: {
    theme: string;
    periodDays: number;
    dailyMinutes: number;
    difficulty: string;
    expectedOutcome: string;
  }): Promise<GoalValidation> {
    return apiRequest('/learning/goals/validate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async createLearningGoal(payload: {
    ownerId: string;
    theme: string;
    learningType: string;
    periodDays: number;
    dailyMinutes: number;
    difficulty: string;
    expectedOutcome: string;
    majorDirection: string;
    electiveTracks: string[];
    tags?: string[];
  }): Promise<{ goal: LearningGoal; plan: LearningPlan; message: string }> {
    return apiRequest('/learning/goals', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getLearningDashboard(ownerId: string): Promise<LearningDashboard> {
    return apiRequest(`/learning/dashboard?ownerId=${encodeURIComponent(ownerId)}`);
  },

  async updateLearningPlanItem(
    itemId: string,
    payload: {
      ownerId: string;
      title?: string;
      description?: string;
      estimatedMinutes?: number;
      dueDay?: number;
      status?: string;
      completionNote?: string;
    },
  ): Promise<{ item: LearningPlanItem }> {
    return apiRequest(`/learning/plan-items/${encodeURIComponent(itemId)}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  async completeLearningPlanItem(
    itemId: string,
    ownerId: string,
    completionNote = '',
  ): Promise<{ awarded: number; message: string; plan: LearningPlan }> {
    return apiRequest(`/learning/plan-items/${encodeURIComponent(itemId)}/complete`, {
      method: 'POST',
      body: JSON.stringify({ ownerId, completionNote }),
    });
  },

  async replaceLearningPlanItem(
    itemId: string,
    ownerId: string,
    direction: string,
  ): Promise<{ item: LearningPlanItem; message: string }> {
    return apiRequest(`/learning/plan-items/${encodeURIComponent(itemId)}/replace`, {
      method: 'POST',
      body: JSON.stringify({ ownerId, direction }),
    });
  },

  async askLearningCompanion(
    ownerId: string,
    planId: string,
    message: string,
  ): Promise<{ reply: string; source: string; nextTask: LearningPlanItem | null }> {
    return apiRequest('/learning/companion', {
      method: 'POST',
      body: JSON.stringify({ ownerId, planId, message }),
    });
  },

  async createLearningArtifact(payload: {
    ownerId: string;
    planId: string;
    title: string;
    artifactType: string;
    description: string;
    visibility: string;
  }): Promise<{ artifact: LearningArtifact }> {
    return apiRequest('/learning/artifacts', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async addLearningArtifactVersion(
    artifactId: string,
    payload: {
      ownerId: string;
      fileName: string;
      contentSummary: string;
      revisionNote: string;
    },
  ): Promise<{ artifact: LearningArtifact; review: LearningArtifact['aiReview']; message: string }> {
    return apiRequest(`/learning/artifacts/${encodeURIComponent(artifactId)}/versions`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async uploadLearningArtifactFile(
    artifactId: string,
    ownerId: string,
    file: File,
  ): Promise<{ fileName: string; storageKey: string; size: number; message: string }> {
    validateFile(file, [], ARTIFACT_MAX_SIZE, '文件');
    return apiUpload(
      `/learning/artifacts/${encodeURIComponent(artifactId)}/upload?ownerId=${encodeURIComponent(ownerId)}`,
      file,
      'file',
    );
  },

  async publishLearningArtifact(
    artifactId: string,
    ownerId: string,
    visibility: 'private' | 'public' | 'friends',
  ): Promise<{ artifact: LearningArtifact; message: string }> {
    return apiRequest(`/learning/artifacts/${encodeURIComponent(artifactId)}/publish`, {
      method: 'POST',
      body: JSON.stringify({ ownerId, visibility }),
    });
  },

  async shareLearningPlan(planId: string, ownerId: string): Promise<{ listingId: string; message: string }> {
    return apiRequest(`/learning/plans/${encodeURIComponent(planId)}/share`, {
      method: 'POST',
      body: JSON.stringify({ ownerId }),
    });
  },

  async getLearningMarket(
    resourceType: 'all' | 'plan' | 'artifact' = 'all',
  ): Promise<{ templates: LearningTemplate[]; listings: MarketListing[] }> {
    return apiRequest(`/learning/market?resourceType=${encodeURIComponent(resourceType)}`);
  },

  async reuseLearningMarketResource(
    resourceId: string,
    ownerId: string,
  ): Promise<{ goal: LearningGoal; plan: LearningPlan; message: string }> {
    return apiRequest(`/learning/market/${encodeURIComponent(resourceId)}/reuse`, {
      method: 'POST',
      body: JSON.stringify({ ownerId }),
    });
  },

  async getCampusActivities(
    ownerId: string,
  ): Promise<{
    activities: CampusActivity[];
    plan: { id: string; shieldEnergy: number; guardianValue: number } | null;
    boundaryNotice: string;
  }> {
    return apiRequest(`/learning/activities?ownerId=${encodeURIComponent(ownerId)}`);
  },

  async getCampusActivity(
    ownerId: string,
    activityId: string,
  ): Promise<{
    activity: CampusActivity;
    plan: { id: string; shieldEnergy: number; guardianValue: number } | null;
    boundaryNotice: string;
  }> {
    return apiRequest(
      `/learning/activities/${encodeURIComponent(activityId)}?ownerId=${encodeURIComponent(ownerId)}`,
    );
  },

  // ========== V3.0 双端口 & 统一盾能体系 ==========
  async schoolDemoLogin() {
    return apiRequest<{ ownerId: string; nickname: string; currentUser: User }>('/school/demo-login', {
      method: 'POST',
      body: JSON.stringify({}),
    });
  },
  async createTheme(payload: {
    ownerId: string;
    title: string;
    description?: string;
    periodDays?: number;
    targetAudience?: string;
    scope?: string;
    baseRequired?: string;
    electiveDirection?: string;
    expectedOutcome?: string;
    baseAssessment?: string;
    publishTime?: string;
  }) {
    return apiRequest<ThemeInfo>('/theme/create', { method: 'POST', body: JSON.stringify(payload) });
  },
  async generateTheme(themeId: string, ownerId: string) {
    return apiRequest<ThemeInfo>(`/theme/${themeId}/generate`, {
      method: 'POST',
      body: JSON.stringify({ ownerId }),
    });
  },
  async confirmTheme(themeId: string, ownerId: string, edits?: { items?: ThemeItem[] }) {
    return apiRequest<{ theme: ThemeInfo; planId: string }>(`/theme/${themeId}/confirm`, {
      method: 'POST',
      body: JSON.stringify({ ownerId, edits }),
    });
  },
  async listThemes(ownerId: string) {
    return apiRequest<ThemeInfo[]>(`/theme/list?ownerId=${encodeURIComponent(ownerId)}`);
  },
  async getActiveTheme(ownerId?: string) {
    const q = ownerId ? `?ownerId=${encodeURIComponent(ownerId)}` : '';
    return apiRequest<{ theme: ThemeInfo | null; items: ThemeItem[]; joined: boolean; planId: string | null }>(
      `/theme/active${q}`,
    );
  },
  async getVideoLibrary(theme?: string) {
    const q = theme ? `?theme=${encodeURIComponent(theme)}` : '';
    return apiRequest<{ videos: VideoLibraryEntry[] }>(`/video-library${q}`);
  },
  async joinTheme(themeId: string, ownerId: string) {
    return apiRequest<{ planId: string; items: ThemeItem[] }>(`/theme/${themeId}/join`, {
      method: 'POST',
      body: JSON.stringify({ ownerId }),
    });
  },
  async completeThemeItem(itemId: string, ownerId: string) {
    return apiRequest<
      { item: ThemeItem; balances: EnergyBalance } | { alreadyDone: boolean; balances: EnergyBalance }
    >(`/theme/items/${itemId}/complete`, { method: 'POST', body: JSON.stringify({ ownerId }) });
  },
  async getEnergyBalance(ownerId: string) {
    return apiRequest<EnergyBalance>(`/energy/balance?ownerId=${encodeURIComponent(ownerId)}`);
  },
  async getEnergyLedger(ownerId: string) {
    return apiRequest<{ ownerId: string; ledger: EnergyLedgerEntry[] }>(
      `/energy/ledger?ownerId=${encodeURIComponent(ownerId)}`,
    );
  },
  async listActivities(ownerId: string) {
    return apiRequest<ActivityInfo[]>(`/activities?ownerId=${encodeURIComponent(ownerId)}`);
  },
  async createActivity(payload: {
    ownerId: string;
    title: string;
    category?: string;
    description?: string;
    organizer?: string;
    interestDirection?: string;
    targetEnergy?: number;
    noticeUrl?: string;
  }) {
    return apiRequest<ActivityInfo>('/activities/create', { method: 'POST', body: JSON.stringify(payload) });
  },
  async contributeActivity(activityId: string, ownerId: string, amount: number) {
    return apiRequest<{ activity: ActivityInfo; balances: EnergyBalance }>(
      `/activities/${activityId}/contribute`,
      { method: 'POST', body: JSON.stringify({ ownerId, amount }) },
    );
  },
  async releaseActivityNotice(activityId: string, ownerId: string, noticeText: string, noticeUrl?: string) {
    return apiRequest<ActivityInfo>(`/activities/${activityId}/release-notice`, {
      method: 'POST',
      body: JSON.stringify({ ownerId, noticeText, noticeUrl }),
    });
  },
  async getSchoolDashboard(ownerId: string) {
    return apiRequest<SchoolDashboard>(`/school/dashboard?ownerId=${encodeURIComponent(ownerId)}`);
  },

  // ========== 校园账号登录 (赛道 #30) ==========
  async campusLogin(
    studentId: string,
    school: string,
    department = '',
    password = '',
  ): Promise<{ currentUser: User; token?: string; message: string }> {
    return apiRequest('/campus/login', {
      method: 'POST',
      body: JSON.stringify({ studentId, school, department, password }),
    });
  },

  // ========== 集市互动：点赞 / 收藏 / 评分 / 评论 (赛道 #24/#26) ==========
  async marketLike(listingId: string, ownerId: string): Promise<{ likes: number; liked: boolean }> {
    return apiRequest(`/market/${encodeURIComponent(listingId)}/like?ownerId=${encodeURIComponent(ownerId)}`, {
      method: 'POST',
    });
  },
  async marketFavorite(listingId: string, ownerId: string): Promise<{ favorites: number; favorited: boolean }> {
    return apiRequest(`/market/${encodeURIComponent(listingId)}/favorite?ownerId=${encodeURIComponent(ownerId)}`, {
      method: 'POST',
    });
  },
  async marketRate(listingId: string, ownerId: string, score: number): Promise<{ ratingAvg: number; ratingCount: number; myScore: number }> {
    return apiRequest(`/market/${encodeURIComponent(listingId)}/rate`, {
      method: 'POST',
      body: JSON.stringify({ ownerId, score }),
    });
  },
  async getMarketComments(listingId: string): Promise<{ comments: MarketComment[] }> {
    return apiRequest(`/market/${encodeURIComponent(listingId)}/comments`);
  },
  async addMarketComment(listingId: string, ownerId: string, content: string): Promise<MarketComment> {
    return apiRequest(`/market/${encodeURIComponent(listingId)}/comments`, {
      method: 'POST',
      body: JSON.stringify({ ownerId, content }),
    });
  },

  // ========== 消息通知 (赛道 #31) ==========
  async getNotifications(ownerId: string, unreadOnly = false): Promise<{ notifications: NotificationItem[] }> {
    return apiRequest(
      `/notifications?ownerId=${encodeURIComponent(ownerId)}${unreadOnly ? '&unreadOnly=true' : ''}`,
    );
  },
  async getUnreadCount(ownerId: string): Promise<{ unreadCount: number }> {
    return apiRequest(`/notifications/unread-count?ownerId=${encodeURIComponent(ownerId)}`);
  },
  async markNotificationRead(notificationId: number, ownerId: string): Promise<{ message: string }> {
    return apiRequest(`/notifications/${notificationId}/read`, {
      method: 'POST',
      body: JSON.stringify({ ownerId }),
    });
  },
  async markAllNotificationsRead(ownerId: string): Promise<{ message: string; count: number }> {
    return apiRequest('/notifications/read-all', {
      method: 'POST',
      body: JSON.stringify({ ownerId }),
    });
  },

  // ========== 项目式协作管控 (赛道 #13) ==========
  async createTeam(
    ownerId: string,
    name: string,
    description = '',
    goalId: string | null = null,
  ): Promise<{ id: string; name: string; ownerId: string }> {
    return apiRequest('/teams', {
      method: 'POST',
      body: JSON.stringify({ ownerId, name, description, goalId }),
    });
  },
  async listTeams(ownerId: string): Promise<{ teams: Team[] }> {
    return apiRequest(`/teams?ownerId=${encodeURIComponent(ownerId)}`);
  },
  async addTeamMember(
    teamId: string,
    ownerId: string,
    memberOwnerId: string,
    role = '成员',
  ): Promise<{ message: string }> {
    return apiRequest(`/teams/${encodeURIComponent(teamId)}/members`, {
      method: 'POST',
      body: JSON.stringify({ ownerId, memberOwnerId, role }),
    });
  },
  async listTeamMembers(teamId: string): Promise<{ members: TeamMember[] }> {
    return apiRequest(`/teams/${encodeURIComponent(teamId)}/members`);
  },
  async removeTeamMember(
    teamId: string,
    memberOwnerId: string,
    ownerId: string,
  ): Promise<{ message: string }> {
    return apiRequest(
      `/teams/${encodeURIComponent(teamId)}/members/${encodeURIComponent(memberOwnerId)}?ownerId=${encodeURIComponent(ownerId)}`,
      { method: 'DELETE' },
    );
  },
  async addMilestone(
    teamId: string,
    ownerId: string,
    title: string,
    dueDay = 7,
  ): Promise<{ id: number; title: string; dueDay: number; status: string }> {
    return apiRequest(`/teams/${encodeURIComponent(teamId)}/milestones`, {
      method: 'POST',
      body: JSON.stringify({ ownerId, title, dueDay }),
    });
  },
  async listMilestones(teamId: string): Promise<{ milestones: Milestone[] }> {
    return apiRequest(`/teams/${encodeURIComponent(teamId)}/milestones`);
  },
  async verifyMilestone(
    teamId: string,
    milestoneId: number,
    ownerId: string,
    status: 'verified' | 'rejected',
    note = '',
  ): Promise<{ id: number; status: string; note: string }> {
    return apiRequest(`/teams/${encodeURIComponent(teamId)}/milestones/${milestoneId}/verify`, {
      method: 'POST',
      body: JSON.stringify({ ownerId, status, note }),
    });
  },
  async addIssue(
    teamId: string,
    ownerId: string,
    title: string,
    description = '',
  ): Promise<{ id: number; title: string; status: string }> {
    return apiRequest(`/teams/${encodeURIComponent(teamId)}/issues`, {
      method: 'POST',
      body: JSON.stringify({ ownerId, title, description }),
    });
  },
  async listIssues(teamId: string): Promise<{ issues: ProjectIssue[] }> {
    return apiRequest(`/teams/${encodeURIComponent(teamId)}/issues`);
  },
  async updateIssue(
    teamId: string,
    issueId: number,
    ownerId: string,
    status: string,
  ): Promise<{ id: number; status: string }> {
    return apiRequest(`/teams/${encodeURIComponent(teamId)}/issues/${issueId}`, {
      method: 'PATCH',
      body: JSON.stringify({ ownerId, status }),
    });
  },

  // ========== 社交与好友 (赛道 #32) ==========
  async friendRequest(ownerId: string, friendOwnerId: string): Promise<{ status: string; message: string }> {
    return apiRequest('/social/friends/request', {
      method: 'POST',
      body: JSON.stringify({ ownerId, friendOwnerId }),
    });
  },
  async friendAccept(ownerId: string, friendOwnerId: string): Promise<{ status: string; message: string }> {
    return apiRequest('/social/friends/accept', {
      method: 'POST',
      body: JSON.stringify({ ownerId, friendOwnerId }),
    });
  },
  async listFriends(ownerId: string): Promise<{ friends: string[]; pendingRequests: string[] }> {
    return apiRequest(`/social/friends?ownerId=${encodeURIComponent(ownerId)}`);
  },
  async removeFriend(ownerId: string, friendOwnerId: string): Promise<{ message: string }> {
    return apiRequest('/social/friends', {
      method: 'DELETE',
      body: JSON.stringify({ ownerId, friendOwnerId }),
    });
  },

  // ========== 成果隐私三级过滤 (赛道 #32) ==========
  async listArtifacts(ownerId = '', viewerId = ''): Promise<{ artifacts: ArtifactSummary[] }> {
    const params = new URLSearchParams();
    if (ownerId) params.set('ownerId', ownerId);
    if (viewerId) params.set('viewerId', viewerId);
    return apiRequest(`/artifacts?${params.toString()}`);
  },

  // ========== 个性化推荐与学习督促 (赛道 #17/#27) ==========
  async recommendMarket(ownerId: string, limit = 10): Promise<{ recommendations: MarketRecommendation[] }> {
    return apiRequest(`/recommend/market?ownerId=${encodeURIComponent(ownerId)}&limit=${limit}`);
  },
  async studyReminders(ownerId: string): Promise<StudyReminder> {
    return apiRequest(`/recommend/study?ownerId=${encodeURIComponent(ownerId)}`);
  },

  // ========== 校园认证方式 (赛道 #30) ==========
  async getCampusAuthConfig(): Promise<CampusAuthConfig> {
    return apiRequest('/campus/auth-config');
  },

  // ========== 延期申请 (赛道 #11) ==========
  async requestPlanExtension(
    planId: string,
    payload: { ownerId: string; extraDays: number; reason: string },
  ): Promise<{ plan: LearningPlan; extensions: PlanExtension[]; message: string }> {
    return apiRequest(`/learning/plans/${encodeURIComponent(planId)}/extend`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // ========== 代码调试答疑 (赛道 #16) ==========
  async codeDebug(payload: {
    ownerId: string;
    planId?: string;
    language: string;
    code: string;
    question: string;
  }): Promise<CodeDebugResult> {
    return apiRequest('/learning/code-debug', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // ========== AI 成果独立初审 (赛道 #21) ==========
  async reviewArtifact(
    artifactId: string,
    payload: { ownerId: string; contentSummary: string; revisionNote?: string; fileName?: string },
  ): Promise<{ review: ArtifactReview; message: string }> {
    return apiRequest(`/learning/artifacts/${encodeURIComponent(artifactId)}/review`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
