export type LearningTaskCategory = 'required' | 'elective' | 'outcome';
export type LearningTaskStatus = 'not_started' | 'in_progress' | 'completed' | 'paused';

export interface GoalValidation {
  score: number;
  isExecutable: boolean;
  normalizedGoal: string;
  suggestions: string[];
  source: string;
}

export interface LearningGoal {
  id: string;
  ownerId: string;
  theme: string;
  learningType: string;
  periodDays: number;
  dailyMinutes: number;
  difficulty: string;
  expectedOutcome: string;
  majorDirection: string;
  electiveTracks: string[];
  validation: GoalValidation;
  status: string;
  createdAt: string;
}

export interface LearningPlanItem {
  id: string;
  planId: string;
  category: LearningTaskCategory;
  title: string;
  description: string;
  resourceHint: string;
  acceptanceCriteria: string;
  estimatedMinutes: number;
  dueDay: number;
  orderIndex: number;
  status: LearningTaskStatus;
  completionNote: string;
  completedAt: string | null;
  videoUrl?: string | null;
  videoThumbnail?: string | null;
}

export interface LearningPlan {
  id: string;
  goalId: string;
  ownerId: string;
  title: string;
  summary: string;
  source: string;
  status: string;
  shieldEnergy: number;
  guardianValue: number;
  extensionDays: number;
  progress: number;
  completedCount: number;
  totalCount: number;
  items: LearningPlanItem[];
  createdAt: string;
}

export interface ArtifactReview {
  score?: number;
  level?: string;
  strengths?: string[];
  issues?: string[];
  suggestions?: string[];
  reviewedAt?: string;
  source?: string;
}

export interface ArtifactVersion {
  id: number;
  versionNo: number;
  fileName: string;
  contentSummary: string;
  revisionNote: string;
  aiReview: ArtifactReview;
  createdAt: string;
}

export interface LearningArtifact {
  id: string;
  planId: string;
  ownerId: string;
  title: string;
  artifactType: string;
  description: string;
  visibility: 'private' | 'public' | 'friends';
  status: 'draft' | 'published';
  latestVersion: number;
  aiReview: ArtifactReview;
  versions: ArtifactVersion[];
  createdAt: string;
  updatedAt: string;
}

export interface CampusActivityRequirement {
  label: string;
  current: number;
  target: number;
  completed: boolean;
}

export interface CampusActivity {
  id: string;
  title: string;
  category: string;
  description: string;
  organizer: string;
  interestDirection: string;
  noticeUrl: string;
  status: 'locked' | 'unlocked';
  progress: number;
  requirements: CampusActivityRequirement[];
  unlockedAt: string | null;
  boundaryNotice: string;
}

export interface LearningDashboard {
  goal: LearningGoal | null;
  plan: LearningPlan | null;
  artifacts: LearningArtifact[];
  activities: CampusActivity[];
  boundaryNotice: string;
}

export interface LearningTemplate {
  id: string;
  title: string;
  theme: string;
  difficulty: string;
  periodDays: number;
  dailyMinutes: number;
  expectedOutcome: string;
  summary: string;
  tags: string[];
  electiveTracks: string[];
  reuseCount: number;
  featured: boolean;
  // 需求#7：任务包配置结构化（大纲/重难点/参考/考核）
  outline?: string[];
  keyDifficulties?: string[];
  referenceMaterials?: Array<{ title: string; detail: string }>;
  assessmentCriteria?: string[];
}

export interface MarketListing {
  id: string;
  ownerId: string;
  resourceType: 'plan' | 'artifact';
  resourceId: string;
  title: string;
  theme: string;
  summary: string;
  tags: string[];
  likes: number;
  favorites: number;
  reuseCount: number;
  ratingAvg?: number;
  ratingCount?: number;
  createdAt: string;
}

export interface MarketComment {
  id: number;
  ownerId: string;
  content: string;
  createdAt: string;
}

export interface NotificationItem {
  id: number;
  type: string;
  title: string;
  content: string;
  refId: string | null;
  isRead: boolean;
  createdAt: string;
}

// ==================== 项目式协作管控 (赛道 #13) ====================
export interface Team {
  id: string;
  name: string;
  goalId: string | null;
  ownerId: string;
}

export interface TeamMember {
  ownerId: string;
  role: string;
  createdAt: string;
}

export interface Milestone {
  id: number;
  title: string;
  dueDay: number;
  status: string; // pending | verified | rejected
  note: string;
}

export interface ProjectIssue {
  id: number;
  ownerId: string;
  title: string;
  description: string;
  status: string; // open | in_progress | resolved | closed
  createdAt: string;
}

// ==================== 社交与好友 (赛道 #32) ====================
export interface FriendInfo {
  friends: string[];
  pendingRequests: string[];
}

/** 成果隐私三级过滤后的可见成果摘要 */
export interface ArtifactSummary {
  id: string;
  ownerId: string;
  title: string;
  artifactType: string;
  visibility: 'private' | 'public' | 'friends';
  status: string;
  createdAt: string;
}

// ==================== 个性化推荐与督促 (赛道 #17/#27) ====================
export interface MarketRecommendation {
  id: string;
  title: string;
  theme: string;
  summary: string;
  tags: string[];
  matchScore: number;
  likes: number;
  ratingAvg: number | null;
}

export interface StudyReminder {
  pendingItems: Array<{ planId: string; itemId: string; title: string; dueDay: number; status: string }>;
  retrainTasks: Array<{ id: number; fraudType: string; attempt: number; scheduledAt: string }>;
  weakDimensions: string[];
}

// ==================== 代码调试答疑 (赛道 #16) ====================
export interface CodeDebugResult {
  language: string;
  detectedIssues: string[];
  hints: string[];
  safetyNotes: string[];
  nextStep: string;
  source: string;
}

// ==================== 延期申请 (赛道 #11) ====================
export interface PlanExtension {
  id: number;
  extraDays: number;
  reason: string;
  status: string;
  createdAt: string;
}

// ==================== 校园认证方式 (赛道 #30) ====================
export interface CampusAuthConfig {
  mode: 'demo' | 'cas' | 'oauth';
  providerLabel: string;
  configured: boolean;
}

