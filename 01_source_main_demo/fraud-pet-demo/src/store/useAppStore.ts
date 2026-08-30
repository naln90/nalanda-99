import { create } from 'zustand';
import { api, type PetPoolItem, type RankingResponse, type RiskAnalyzeResponse, type TrainingSubmitResponse } from '../api/client';
import { emitToast } from '../components/ui/Toast';
import { petsPool as mockPetsPool, trainingTasks as mockTrainingTasks } from '../data/mockData';
import type {
  AbilityProfile,
  AICallLog,
  AssessmentResult,
  CounselorDashboard,
  DashboardSummary,
  EnergyBalance,
  EvidenceOverview,
  ActivityInfo,
  Pet,
  RetrainTask,
  ReviewReport,
  ScenarioSession,
  SchoolDashboard,
  TaskPackage,
  ThemeInfo,
  ThemeItem,
  TrainingTask,
  User,
} from '../types';
import type { NotificationItem } from '../types/learning';

const SESSION_KEY = 'fzzy.session';

interface SessionData {
  currentUser: User;
  nickname?: string;
  token?: string;
}

function loadSession(): SessionData | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as SessionData;
  } catch (error) {
    console.error('[useAppStore] 读取会话失败:', error);
    return null;
  }
}

function saveSession(data: SessionData | null) {
  try {
    if (data) localStorage.setItem(SESSION_KEY, JSON.stringify(data));
    else localStorage.removeItem(SESSION_KEY);
  } catch (error) {
    console.error('[useAppStore] 保存会话失败:', error);
  }
}

const initialSession = loadSession();

interface AppState {
  currentUser: User | null;
  nickname: string | null;
  pet: Pet | null;
  petsPool: PetPoolItem[];
  trainingTasks: TrainingTask[];
  ranking: RankingResponse | null;
  riskResult: RiskAnalyzeResponse | null;
  lastSettlement: TrainingSubmitResponse | null;
  assessmentResult: AssessmentResult | null;
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
  // auth
  register: (username: string, password: string, nickname?: string) => Promise<boolean>;
  loginWithCredentials: (username: string, password: string) => Promise<boolean>;
  login: (ownerId?: string) => Promise<void>;
  logout: () => void;
  restoreSession: () => Promise<boolean>;
  // business
  adoptPet: (petType: string, petName?: string, avatarEmoji?: string) => Promise<boolean>;
  updatePetProfile: (data: { petName?: string | null; avatarEmoji?: string | null }) => Promise<boolean>;
  completeAssessment: (answers: Array<{ questionId: string; answer: string | string[] }>) => Promise<AssessmentResult | null>;
  loadPetsPool: () => Promise<void>;
  loadTrainingTasks: () => Promise<void>;
  submitTraining: (taskId: string, answers: Array<{ questionId: string; answer: string[] }>) => Promise<TrainingSubmitResponse | null>;
  analyzeSuspicious: (text: string) => Promise<RiskAnalyzeResponse | null>;
  loadRanking: () => Promise<void>;
  refreshPet: () => Promise<void>;
  // 新增：能力画像 & 仪表盘
  dashboard: DashboardSummary | null;
  abilityProfile: AbilityProfile | null;
  loadDashboard: () => Promise<void>;
  loadAbilityProfile: () => Promise<void>;
  // 新增：当前学习主题（随用户激活的学习计划变化，用于外壳主题自适应，避免写死“反诈”）
  activeLearningTheme: string | null;
  setActiveLearningTheme: (theme: string | null) => void;
  // 新增：AI 任务包
  activeTaskPackage: TaskPackage | null;
  generateTaskPackage: (planType: '7day' | '14day') => Promise<TaskPackage | null>;
  loadCurrentTaskPackage: () => Promise<void>;
  completeTaskItem: (itemId: string) => Promise<boolean>;
  // 新增：情景对话训练
  scenarioSession: ScenarioSession | null;
  reviewReport: ReviewReport | null;
  startScenarioTraining: (scenarioType: string) => Promise<ScenarioSession | null>;
  replyScenarioTraining: (message: string) => Promise<{
    reply: string;
    state: string;
    behavior: string;
    identifiedEvidence: string[];
    newEvidence: string[];
    isTerminal: boolean;
    isCompleted: boolean;
  } | null>;
  finishScenarioTraining: () => Promise<ScenarioSession | null>;
  // 新增：证据中心
  evidenceOverview: EvidenceOverview | null;
  aiLogs: AICallLog[];
  loadEvidenceOverview: () => Promise<void>;
  loadAILogs: (limit?: number) => Promise<void>;
  // 新增：复训
  dueRetrains: RetrainTask[];
  loadDueRetrains: () => Promise<void>;
  // 新增：辅导员看板
  counselorDashboard: CounselorDashboard | null;
  loadCounselorDashboard: () => Promise<void>;
  // ========== V3.0 双端口 & 统一盾能 ==========
  role: 'student' | 'school' | null;
  activeTheme: { theme: ThemeInfo | null; items: ThemeItem[]; joined: boolean; planId: string | null } | null;
  energyBalance: EnergyBalance | null;
  activities: ActivityInfo[];
  schoolDashboard: SchoolDashboard | null;
  schoolThemes: ThemeInfo[];
  loadActiveTheme: (ownerId?: string) => Promise<void>;
  joinActiveTheme: (ownerId: string, themeId: string) => Promise<void>;
  completeThemeItemV3: (itemId: string, ownerId: string) => Promise<void>;
  loadEnergy: (ownerId: string) => Promise<void>;
  loadActivities: (ownerId: string) => Promise<void>;
  contributeActivity: (activityId: string, ownerId: string, amount: number) => Promise<boolean>;
  loadSchoolDashboard: (ownerId: string) => Promise<void>;
  schoolCreateTheme: (payload: {
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
  }) => Promise<ThemeInfo | null>;
  schoolGenerateTheme: (themeId: string, ownerId: string) => Promise<void>;
  schoolConfirmTheme: (themeId: string, ownerId: string) => Promise<void>;
  schoolCreateActivity: (payload: {
    ownerId: string;
    title: string;
    category?: string;
    description?: string;
    organizer?: string;
    interestDirection?: string;
    targetEnergy?: number;
    noticeUrl?: string;
  }) => Promise<void>;
  schoolReleaseNotice: (activityId: string, ownerId: string, noticeText: string) => Promise<void>;
  schoolLogin: () => Promise<boolean>;
  // ========== 校园账号登录 (赛道 #30) ==========
  campusLogin: (studentId: string, school: string, department?: string, password?: string) => Promise<boolean>;
  // ========== 消息通知 (赛道 #31) ==========
  notifications: NotificationItem[];
  unreadCount: number;
  loadNotifications: () => Promise<void>;
  markNotificationRead: (notificationId: number) => Promise<void>;
  markAllNotificationsRead: () => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  currentUser: initialSession?.currentUser ?? null,
  nickname: initialSession?.nickname ?? null,
  pet: null,
  petsPool: mockPetsPool,
  trainingTasks: mockTrainingTasks,
  ranking: null,
  riskResult: null,
  lastSettlement: null,
  assessmentResult: null,
  isLoading: false,
  error: null,
  clearError: () => set({ error: null }),
  dashboard: null,
  abilityProfile: null,
  activeLearningTheme: null,
  activeTaskPackage: null,
  scenarioSession: null,
  reviewReport: null,
  evidenceOverview: null,
  aiLogs: [],
  dueRetrains: [],
  counselorDashboard: null,
  // V3.0
  role: null,
  activeTheme: null,
  energyBalance: null,
  activities: [],
  schoolDashboard: null,
  schoolThemes: [],
  // 校园账号 & 通知
  notifications: [],
  unreadCount: 0,

  register: async (username, password, nickname = '') => {
    set({ isLoading: true, error: null });
    try {
      const result = await api.register(username, password, nickname);
      saveSession({ currentUser: result.currentUser, nickname: result.nickname, token: result.token });
      let pet: Pet | null = null;
      if (result.currentUser.hasPet) {
        pet = (await api.getMyPet(result.currentUser.ownerId)).pet;
      }
      set({ currentUser: result.currentUser, nickname: result.nickname ?? null, pet, role: result.currentUser.role ?? 'student', isLoading: false });
      return true;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '注册失败', isLoading: false });
      return false;
    }
  },

  loginWithCredentials: async (username, password) => {
    set({ isLoading: true, error: null });
    try {
      const result = await api.login(username, password);
      saveSession({ currentUser: result.currentUser, nickname: result.nickname, token: result.token });
      let pet: Pet | null = null;
      if (result.currentUser.hasPet) {
        pet = (await api.getMyPet(result.currentUser.ownerId)).pet;
      }
      set({ currentUser: result.currentUser, nickname: result.nickname ?? null, pet, role: result.currentUser.role ?? 'student', isLoading: false });
      return true;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '登录失败', isLoading: false });
      return false;
    }
  },

  login: async (ownerId) => {
    set({ isLoading: true, error: null });
    try {
      const targetId = ownerId?.trim() || import.meta.env.VITE_DEMO_OWNER_ID || '';
      const result = await api.demoLogin(targetId);
      saveSession({ currentUser: result.currentUser });
      let pet: Pet | null = null;
      if (result.currentUser.hasPet) {
        pet = (await api.getMyPet(result.currentUser.ownerId)).pet;
      }
      set({ currentUser: result.currentUser, nickname: null, pet, role: result.currentUser.role ?? 'student', isLoading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '登录失败', isLoading: false });
    }
  },

  logout: () => {
    saveSession(null);
    set({
      currentUser: null,
      nickname: null,
      pet: null,
      riskResult: null,
      lastSettlement: null,
      assessmentResult: null,
      role: null,
      activeTheme: null,
      energyBalance: null,
      activities: [],
      schoolDashboard: null,
      schoolThemes: [],
    });
  },

  restoreSession: async () => {
    const session = loadSession();
    if (!session?.currentUser) return false;
    // 先同步恢复用户与昵称，让路由守卫立即可用
    set({ currentUser: session.currentUser, nickname: session.nickname ?? null, pet: null, role: session.currentUser.role ?? 'student' });
    // 若用户已领养宠物，则异步拉取最新宠物档案（刷新后仍保留宠物信息）
    if (session.currentUser.hasPet) {
      try {
        const petResp = await api.getMyPet(session.currentUser.ownerId);
        set({ pet: petResp.pet });
      } catch (error) {
        console.error('[useAppStore] 恢复会话时宠物加载失败(可忽略):', error);
      }
    }
    return true;
  },

  adoptPet: async (petType, petName, avatarEmoji) => {
    set({ isLoading: true, error: null });
    try {
      const ownerId = get().currentUser?.ownerId || '';
      const result = await api.claimPet(ownerId, petType, petName, avatarEmoji);
      const nextUser = result.currentUser ?? get().currentUser;
      if (nextUser) saveSession({ currentUser: nextUser, nickname: get().nickname ?? undefined, token: loadSession()?.token });
      set({ pet: result.pet, currentUser: nextUser, isLoading: false });
      return true;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '领取宠物失败', isLoading: false });
      return false;
    }
  },

  updatePetProfile: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const ownerId = get().currentUser?.ownerId || '';
      const result = await api.updatePetProfile(ownerId, data);
      set({ pet: result.pet, isLoading: false });
      return true;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '宠物资料更新失败', isLoading: false });
      return false;
    }
  },

  completeAssessment: async (answers) => {
    set({ isLoading: true, error: null });
    try {
      const ownerId = get().currentUser?.ownerId || '';
      const result = await api.submitAssessment(ownerId, answers);
      if (result.currentUser) saveSession({ currentUser: result.currentUser, nickname: get().nickname ?? undefined, token: loadSession()?.token });
      set({ currentUser: result.currentUser, assessmentResult: result, isLoading: false });
      return result;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '测评提交失败', isLoading: false });
      return null;
    }
  },

  loadPetsPool: async () => {
    try {
      const result = await api.getPetsPool();
      set({ petsPool: result.pets });
    } catch (error) {
      // 后台静默加载，避免污染全局 error 导致其它页面误显示（跨页错误泄漏 P1）
      console.error('[useAppStore] 宠物池加载失败(可忽略):', error);
      emitToast('warning', '宠物数据加载失败，请稍后重试');
    }
  },

  loadTrainingTasks: async () => {
    try {
      const result = await api.getTrainingTasks();
      set({ trainingTasks: result.tasks });
    } catch (error) {
      // 后台静默加载，避免污染全局 error（跨页错误泄漏 P1）
      console.error('[useAppStore] 训练任务加载失败(可忽略):', error);
      emitToast('warning', '训练任务加载失败，请稍后重试');
    }
  },

  submitTraining: async (taskId, answers) => {
    set({ isLoading: true, error: null });
    try {
      const ownerId = get().currentUser?.ownerId || '';
      const result = await api.submitTraining(ownerId, taskId, answers);
      set({ pet: result.pet, lastSettlement: result, isLoading: false });
      return result;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '训练结算失败', isLoading: false });
      return null;
    }
  },

  analyzeSuspicious: async (text) => {
    set({ isLoading: true, error: null, riskResult: null });
    try {
      const ownerId = get().currentUser?.ownerId || '';
      const result = await api.analyzeRisk(ownerId, text);
      let pet = get().pet;
      if (pet) {
        pet = (await api.getMyPet(ownerId)).pet;
      }
      set({ riskResult: result, pet, isLoading: false });
      return result;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '风险判断失败', isLoading: false });
      return null;
    }
  },

  loadRanking: async () => {
    try {
      const ownerId = get().currentUser?.ownerId;
      const ranking = await api.getRanking('total', ownerId);
      set({ ranking });
    } catch (error) {
      // 后台静默加载，避免污染全局 error（跨页错误泄漏 P1）
      console.error('[useAppStore] 排行榜加载失败(可忽略):', error);
      emitToast('warning', '排行榜加载失败，请稍后重试');
    }
  },

  refreshPet: async () => {
    try {
      const ownerId = get().currentUser?.ownerId || '';
      const result = await api.getMyPet(ownerId);
      set({ pet: result.pet });
    } catch (error) {
      console.error('[useAppStore] 加载失败:', error);
    }
  },

  // ========== 新增：能力画像 & 仪表盘 ==========
  loadDashboard: async () => {
    try {
      const ownerId = get().currentUser?.ownerId || '';
      const dashboard = await api.getDashboard(ownerId);
      set({ dashboard, pet: dashboard.pet, abilityProfile: dashboard.abilityProfile, activeTaskPackage: dashboard.activeTaskPackage });
    } catch (error) {
      console.error('[useAppStore] 仪表盘加载失败(可忽略):', error);
    }
  },
  loadAbilityProfile: async () => {
    try {
      const ownerId = get().currentUser?.ownerId || '';
      const { profile } = await api.getAbilityProfile(ownerId);
      set({ abilityProfile: profile });
    } catch (error) {
      console.error('[useAppStore] 加载失败:', error);
    }
  },
  setActiveLearningTheme: (theme) => {
    if (get().activeLearningTheme !== theme) set({ activeLearningTheme: theme });
  },

  // ========== 新增：AI 任务包 ==========
  generateTaskPackage: async (planType) => {
    set({ isLoading: true, error: null });
    try {
      const ownerId = get().currentUser?.ownerId || '';
      const taskPackage = await api.generateTaskPackage(ownerId, planType);
      set({ activeTaskPackage: taskPackage, isLoading: false });
      return taskPackage;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '任务包生成失败', isLoading: false });
      return null;
    }
  },
  loadCurrentTaskPackage: async () => {
    try {
      const ownerId = get().currentUser?.ownerId || '';
      const { taskPackage } = await api.getCurrentTaskPackage(ownerId);
      set({ activeTaskPackage: taskPackage });
    } catch (error) {
      console.error('[useAppStore] 加载失败:', error);
    }
  },
  completeTaskItem: async (itemId) => {
    try {
      const ownerId = get().currentUser?.ownerId || '';
      const { taskPackage } = await api.completeTaskPackageItem(itemId, ownerId);
      set({ activeTaskPackage: taskPackage });
      return true;
    } catch (error) {
      console.error('[useAppStore] 完成任务项失败:', error);
      return false;
    }
  },

  // ========== 新增：情景对话训练 (v1 API) ==========
  startScenarioTraining: async (scenarioType) => {
    set({ isLoading: true, error: null, reviewReport: null });
    try {
      const ownerId = get().currentUser?.ownerId || '';
      const session = await api.startScenarioV1(ownerId, scenarioType);
      set({ scenarioSession: session, isLoading: false });
      return session;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '情景训练启动失败', isLoading: false });
      return null;
    }
  },
  replyScenarioTraining: async (message) => {
    const sessionId = get().scenarioSession?.sessionId;
    if (!sessionId) return null;
    try {
      const result = await api.replyScenarioV1(sessionId, message);
      // 更新 session 中的消息列表和证据
      const current = get().scenarioSession;
      if (current) {
        const updatedSession: ScenarioSession = {
          ...current,
          currentState: result.state as ScenarioSession['currentState'],
          identifiedEvidence: result.identifiedEvidence as string[],
          messages: [
            ...current.messages,
            { id: `user-${Date.now()}`, speaker: 'user', content: message, timestamp: new Date().toISOString() },
            { id: `ai-${Date.now()}`, speaker: 'ai', content: result.reply, state: result.state, timestamp: new Date().toISOString() },
          ],
        };
        set({ scenarioSession: updatedSession });
      }
      return result;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '对话回复失败' });
      return null;
    }
  },
  finishScenarioTraining: async () => {
    const sessionId = get().scenarioSession?.sessionId;
    if (!sessionId) return null;
    set({ isLoading: true, error: null });
    try {
      const { session, review } = await api.finishScenarioV1(sessionId);
      set({ scenarioSession: session, reviewReport: review, isLoading: false });
      return session;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '情景训练结束失败', isLoading: false });
      return null;
    }
  },

  // ========== 新增：证据中心 ==========
  loadEvidenceOverview: async () => {
    try {
      const ownerId = get().currentUser?.ownerId;
      const overview = await api.getEvidenceOverview(ownerId);
      set({ evidenceOverview: overview });
    } catch (error) {
      console.error('[useAppStore] 加载失败:', error);
    }
  },
  loadAILogs: async (limit = 20) => {
    try {
      const ownerId = get().currentUser?.ownerId;
      const { logs } = await api.getAILogs(ownerId, limit);
      set({ aiLogs: logs });
    } catch (error) {
      console.error('[useAppStore] 加载失败:', error);
    }
  },

  // ========== 新增：复训 ==========
  loadDueRetrains: async () => {
    try {
      const ownerId = get().currentUser?.ownerId || '';
      const { retrains } = await api.getDueRetrains(ownerId);
      set({ dueRetrains: retrains });
    } catch (error) {
      console.error('[useAppStore] 加载失败:', error);
    }
  },

  // ========== 新增：辅导员看板 ==========
  loadCounselorDashboard: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await api.getCounselorDashboard();
      set({ counselorDashboard: data, isLoading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '加载看板失败', isLoading: false });
    }
  },

  // ========== V3.0 双端口 & 统一盾能 ==========
  loadActiveTheme: async (ownerId) => {
    try {
      const oid = ownerId ?? get().currentUser?.ownerId;
      const data = await api.getActiveTheme(oid);
      set({ activeTheme: data });
    } catch (error) {
      console.error('[useAppStore] 加载失败:', error);
    }
  },

  joinActiveTheme: async (ownerId, themeId) => {
    set({ isLoading: true, error: null });
    try {
      await api.joinTheme(themeId, ownerId);
      const data = await api.getActiveTheme(ownerId);
      set({ activeTheme: data, isLoading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '加入主题失败', isLoading: false });
    }
  },

  completeThemeItemV3: async (itemId, ownerId) => {
    try {
      const result = await api.completeThemeItem(itemId, ownerId);
      if ('balances' in result && result.balances) {
        set({ energyBalance: result.balances });
      }
      // 刷新主题任务列表
      const data = await api.getActiveTheme(ownerId);
      set({ activeTheme: data });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '任务完成失败' });
    }
  },

  loadEnergy: async (ownerId) => {
    try {
      const balance = await api.getEnergyBalance(ownerId);
      set({ energyBalance: balance });
    } catch (error) {
      console.error('[useAppStore] 加载失败:', error);
    }
  },

  loadActivities: async (ownerId) => {
    try {
      const activities = await api.listActivities(ownerId);
      set({ activities });
    } catch (error) {
      console.error('[useAppStore] 加载失败:', error);
    }
  },

  contributeActivity: async (activityId, ownerId, amount) => {
    set({ error: null });
    try {
      const { activity, balances } = await api.contributeActivity(activityId, ownerId, amount);
      set((state) => ({
        energyBalance: balances,
        activities: state.activities.map((a) => (a.id === activity.id ? activity : a)),
      }));
      return true;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '盾能投放失败' });
      return false;
    }
  },

  loadSchoolDashboard: async (ownerId) => {
    try {
      const data = await api.getSchoolDashboard(ownerId);
      set({ schoolDashboard: data });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '校方看板加载失败' });
    }
  },

  schoolCreateTheme: async (payload) => {
    set({ isLoading: true, error: null });
    try {
      const theme = await api.createTheme(payload);
      const themes = await api.listThemes(payload.ownerId);
      set({ schoolThemes: themes, isLoading: false });
      return theme;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '主题创建失败', isLoading: false });
      return null;
    }
  },

  schoolGenerateTheme: async (themeId, ownerId) => {
    set({ isLoading: true, error: null });
    try {
      await api.generateTheme(themeId, ownerId);
      const themes = await api.listThemes(ownerId);
      set({ schoolThemes: themes, isLoading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'AI 任务包生成失败', isLoading: false });
    }
  },

  schoolConfirmTheme: async (themeId, ownerId) => {
    set({ isLoading: true, error: null });
    try {
      await api.confirmTheme(themeId, ownerId);
      const themes = await api.listThemes(ownerId);
      set({ schoolThemes: themes, isLoading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '主题发布失败', isLoading: false });
    }
  },

  schoolCreateActivity: async (payload) => {
    set({ isLoading: true, error: null });
    try {
      await api.createActivity(payload);
      const activities = await api.listActivities(payload.ownerId);
      set({ activities, isLoading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '活动创建失败', isLoading: false });
    }
  },

  schoolReleaseNotice: async (activityId, ownerId, noticeText) => {
    set({ isLoading: true, error: null });
    try {
      const activity = await api.releaseActivityNotice(activityId, ownerId, noticeText);
      set((state) => ({
        activities: state.activities.map((a) => (a.id === activity.id ? activity : a)),
        isLoading: false,
      }));
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '通知发布失败', isLoading: false });
    }
  },

  schoolLogin: async () => {
    set({ isLoading: true, error: null });
    try {
      const result = await api.schoolDemoLogin();
      saveSession({ currentUser: result.currentUser, nickname: result.nickname });
      set({
        currentUser: result.currentUser,
        nickname: result.nickname ?? null,
        role: 'school',
        isLoading: false,
      });
      return true;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '校方登录失败', isLoading: false });
      return false;
    }
  },

  // ========== 校园账号登录 (赛道 #30) ==========
  campusLogin: async (studentId, school, department = '', password = '') => {
    set({ isLoading: true, error: null });
    try {
      const result = await api.campusLogin(studentId, school, department, password);
      saveSession({ currentUser: result.currentUser, token: result.token });
      let pet: Pet | null = null;
      if (result.currentUser.hasPet) {
        pet = (await api.getMyPet(result.currentUser.ownerId)).pet;
      }
      set({
        currentUser: result.currentUser,
        nickname: `校园·${school}`,
        pet,
        role: 'student',
        isLoading: false,
      });
      return true;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '校园账号登录失败', isLoading: false });
      return false;
    }
  },

  // ========== 消息通知 (赛道 #31) ==========
  loadNotifications: async () => {
    const ownerId = get().currentUser?.ownerId;
    if (!ownerId) return;
    try {
      const [{ notifications }, { unreadCount }] = await Promise.all([
        api.getNotifications(ownerId),
        api.getUnreadCount(ownerId),
      ]);
      set({ notifications, unreadCount });
    } catch (error) {
      console.error('[useAppStore] 通知加载失败(可忽略):', error);
    }
  },
  markNotificationRead: async (notificationId) => {
    const ownerId = get().currentUser?.ownerId;
    if (!ownerId) return;
    try {
      await api.markNotificationRead(notificationId, ownerId);
      set((state) => ({
        notifications: state.notifications.map((n) => (n.id === notificationId ? { ...n, isRead: true } : n)),
        unreadCount: Math.max(0, state.unreadCount - 1),
      }));
    } catch (error) {
      console.error('[useAppStore] 标记已读失败(可忽略):', error);
    }
  },
  markAllNotificationsRead: async () => {
    const ownerId = get().currentUser?.ownerId;
    if (!ownerId) return;
    try {
      await api.markAllNotificationsRead(ownerId);
      set((state) => ({
        notifications: state.notifications.map((n) => ({ ...n, isRead: true })),
        unreadCount: 0,
      }));
    } catch (error) {
      console.error('[useAppStore] 全部已读失败(可忽略):', error);
    }
  },
}));
