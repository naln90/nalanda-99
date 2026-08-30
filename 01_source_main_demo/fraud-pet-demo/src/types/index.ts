export interface User {
  ownerId: string;
  hasCompletedAssessment: boolean;
  hasPet: boolean;
  role?: 'student' | 'school';
}

// ==================== V3.0 双端口 & 统一盾能体系 ====================

export interface VideoLibraryEntry {
  id: number;
  theme: string;
  title: string;
  url: string;
  thumbnail: string | null;
  durationSeconds: number;
  source: string;
  sourceUrl: string | null;
}

export interface ThemeItem {
  id: string;
  planId: string;
  category: 'required' | 'elective' | 'outcome';
  title: string;
  description: string;
  resourceHint: string;
  acceptanceCriteria: string;
  energyReward: number;
  estimatedMinutes: number;
  dueDay: number;
  orderIndex: number;
  status: string;
  completedAt: string | null;
  videoUrl?: string | null;
  videoThumbnail?: string | null;
}

export interface ThemeInfo {
  id: string;
  title: string;
  description: string;
  periodDays: number;
  targetAudience: string;
  scope: string;
  baseRequired: string;
  electiveDirection: string;
  expectedOutcome: string;
  baseAssessment: string;
  publishTime: string;
  status: string;
  creatorId: string;
  planId: string | null;
  aiMetadata: { items?: ThemeItem[]; [k: string]: unknown };
  publishedAt: string | null;
  createdAt: string | null;
}

export interface EnergyBalance {
  ownerId: string;
  cumulativeEnergy: number;
  availableEnergy: number;
  contributedEnergy: number;
  level: number;
}

export interface EnergyLedgerEntry {
  id: number;
  txType: string;
  sourceRef: string;
  delta: number;
  cumulativeAfter: number;
  availableAfter: number;
  contributedAfter: number;
  note: string;
  createdAt: string;
}

export interface ActivityInfo {
  id: string;
  title: string;
  category: string;
  description: string;
  organizer: string;
  interestDirection: string;
  noticeUrl: string;
  targetEnergy: number;
  currentProgress: number;
  contributorCount: number;
  progressRatio: number;
  status: string;
  noticeText: string;
  releasedAt: string | null;
  myContribution: number;
  boundaryNotice: string;
}

export interface SchoolDashboard {
  totalUsers: number;
  studentCount: number;
  taskCompletionRate: number;
  activeTheme: ThemeInfo | null;
  activities: Array<{
    id: string;
    title: string;
    currentProgress: number;
    targetEnergy: number;
    status: string;
    contributorCount: number;
  }>;
}
export interface Pet {
  petId: string;
  ownerId: string;
  type: string;
  category: '动物类' | '机器人类' | '守护兽类';
  petName: string;
  avatarEmoji: string;
  level: number;
  stage: '幼崽期' | '学习期' | '成长期' | '进阶期' | '反诈守护者';
  growthValue: number;
  currentLevelMin: number;
  nextLevelValue: number;
  lastTrainingAt: string;
}

export interface TrainingTask {
  id: string;
  title: string;
  fraudType: string;
  riskLevel: '低风险' | '中风险' | '高风险';
  difficulty: '低' | '中等' | '高';
  duration: string;
  reward: number;
}

export interface AssessmentQuestion {
  id: string;
  questionType: 'single' | 'multiple';
  fraudType: string;
  stem: string;
  options: string[];
  correctAnswer?: string | string[];
  explanation?: string;
  /** 综合能力维度标签 */
  abilityDim?: string;
  /** 风险阶段标签 */
  riskStage?: string;
  /** 证据识别标签 */
  evidenceTags?: string[];
}

export interface TrainingQuestion {
  id: string;
  questionType: 'single' | 'multiple';
  stem: string;
  options: string[];
  correctAnswer: string | string[];
  explanation: string;
}

export interface TrainingTaskDetail {
  task: TrainingTask;
  scenario: {
    title: string;
    messages: Array<{ speaker: string; content: string }>;
  };
  questions: TrainingQuestion[];
}

export interface PetStage {
  name: string;
  levelRange: string;
  appearance: string;
}

export interface KnowledgeItem {
  id: string;
  theme: string;
  category: string;
  title: string;
  riskLevel: string;
  typicalPhrase: string;
  recognitionPoints: string;
  suggestions: string;
  relatedTaskId?: string | null;
  /** 内容来源，需正式、最新、可追溯 */
  source?: string | null;
  /** 来源参考链接 */
  sourceUrl?: string | null;
}

export interface AssessmentResult {
  accuracy: number;
  correctCount: number;
  totalCount: number;
  weakAreas: string[];
  growthAwarded: number;
  unlockedPetPool: boolean;
  currentUser: User;
  /** 综合能力画像数据 */
  abilityProfile?: AbilityProfile;
}

// ========== 综合能力画像 ==========

/** 综合能力维度名称（主题无关，适用于所有参与主题的综合画像） */
export type AbilityDimension = '辨识力' | '判断力' | '应变力' | '实证力' | '协作力';

/** 单维度得分 */
export interface DimensionScore {
  dimension: AbilityDimension;
  score: number;
  maxScore: number;
  percentage: number;
}

/** 综合能力画像（基于已参与主题的综合评估） */
export interface AbilityProfile {
  dimensions: DimensionScore[];
  overallScore: number;
  weakDimensions: AbilityDimension[];
  strongDimensions: AbilityDimension[];
  level: string;
  /** 上次画像时间（用于对比） */
  previousProfile?: AbilityProfile | null;
}

/** 能力画像变化量 */
export interface AbilityDelta {
  dimension: AbilityDimension;
  delta: number;
  direction: 'up' | 'down' | 'stable';
}

// ========== AI 任务包 ==========

/** 任务包类型 */
export type TaskPackageType = '7day' | '14day';

/** 任务包单项 */
export interface TaskPackageItem {
  id: string;
  day: number;
  dimension: AbilityDimension;
  title: string;
  description: string;
  taskType: 'assessment' | 'scenario' | 'retrain' | 'knowledge';
  fraudType?: string;
  isCompleted: boolean;
  completedAt?: string | null;
  score?: number | null;
}

/** AI 任务包 */
export interface TaskPackage {
  id: number;
  ownerId: string;
  planType: TaskPackageType;
  status: 'active' | 'completed' | 'expired';
  items: TaskPackageItem[];
  totalDays: number;
  completedDays: number;
  progress: number;
  createdAt: string;
  expiresAt?: string | null;
  abilitySnapshot: AbilityProfile;
}

// ========== 情景对话会话 ==========

/** 用户行为分类 */
export type UserBehavior = 'recognize_risk' | 'proceed' | 'ask_question' | 'hesitate' | 'other';

/** 对话消息 */
export interface ScenarioMessage {
  id: string;
  speaker: 'system' | 'ai' | 'user';
  content: string;
  state?: string;
  evidenceTag?: string;
  timestamp: string;
  behavior?: UserBehavior | null;
}

/** 情景对话状态 */
export type ScenarioState = 'S0' | 'S1' | 'S2' | 'S3' | 'S4' | 'S5';

/** 情景对话会话 */
export interface ScenarioSession {
  sessionId: string;
  ownerId: string;
  scenarioType: string;
  currentState: ScenarioState;
  messages: ScenarioMessage[];
  identifiedEvidence: string[];
  missedEvidence: string[];
  score: number;
  isSuccess: boolean;
  startedAt: string;
  finishedAt?: string | null;
}

/** 复盘报告 */
export interface ReviewReport {
  identifiedEvidence: string[];
  missedEvidence: string[];
  correctBehaviors: string[];
  riskyBehaviors: string[];
  nextSteps: string[];
  abilityChange: AbilityDelta[];
  reviewSummary: string;
  score: number;
  isSuccess: boolean;
}

// ========== 错题复训调度 ==========

/** 变体策略 */
export type VariantStrategy = 'change_options_order' | 'change_scenario_detail' | 'change_question_type';

/** 复训任务 */
export interface RetrainTask {
  id: number;
  ownerId: string;
  originalQuestionId: string;
  originalTaskId?: string | null;
  fraudType?: string;
  targetAbility?: string;
  attempt?: number;
  variantStrategy: VariantStrategy;
  scheduledAt: string;
  status: 'pending' | 'completed' | 'skipped';
  completedAt?: string | null;
  intervalDays: number;
}

// ========== AI 调用日志（赛事证据中心） ==========

/** AI 调用日志 */
export interface AICallLog {
  id: number;
  callType: string;
  promptVersion: string;
  inputSummary: string;
  outputSummary: string;
  modelUsed: string;
  latencyMs: number;
  tokenCount?: number | null;
  isSuccess: boolean;
  errorMessage?: string | null;
  createdAt: string;
}

/** AI 调用统计概览 */
export interface EvidenceOverview {
  totalCalls: number;
  successRate: number;
  avgLatencyMs: number;
  callTypeBreakdown: Record<string, number>;
  promptVersions: string[];
  dateRange: { from: string; to: string };
}

/** Prompt 版本清单 */
export interface PromptVersion {
  version: string;
  callType: string;
  description: string;
  isActive: boolean;
  createdAt: string;
}

// ========== 仪表盘 ==========

/** 仪表盘汇总数据 */
export interface DashboardSummary {
  user: User;
  pet: Pet | null;
  abilityProfile: AbilityProfile | null;
  activeTaskPackage: TaskPackage | null;
  todayTrainingCount: number;
  totalTrainingCount: number;
  consecutiveDays: number;
  pendingRetrains: number;
  recentAICallCount: number;
  lastTrainingAt: string | null;
}

// ========== 辅导员看板 ==========

/** 辅导员看板概览 */
export interface CounselorOverview {
  totalStudents: number;
  assessedRate: number;
  petRate: number;
  totalTraining: number;
  avgAccuracy: number;
}

/** 匿名学生画像 */
export interface StudentProfile {
  ownerId: string;
  overallScore: number;
  weakDimensions: string[];
  accuracy: number;
  petLevel: number;
  lastAssessment: string;
}

/** 辅导员看板数据 */
export interface CounselorDashboard {
  overview: CounselorOverview;
  avgScores: Record<string, number>;
  weakDistribution: Array<{ dimension: string; count: number }>;
  fraudDistribution: Array<{ type: string; count: number }>;
  trainingTrend: Array<{ date: string; count: number }>;
  studentProfiles: StudentProfile[];
}

/** 班会素材 */
export interface ClassMeeting {
  generatedAt: string;
  classProfile: { totalAssessed: number; topWeakDimensions: Array<{ dimension: string; count: number }> };
  topics: Array<{ dimension: string; weakCount: number; topic: string; questions: string[]; activity: string }>;
  suggestions: string[];
}
