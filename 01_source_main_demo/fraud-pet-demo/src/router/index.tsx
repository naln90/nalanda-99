import { useEffect, lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import StudentLayout from '../components/layout/StudentLayout';
import SchoolLayout from '../components/layout/SchoolLayout';
import AssessmentPage from '../pages/AssessmentPage';
import AssessmentResultPage from '../pages/AssessmentResultPage';
import FreeTrainingPage from '../pages/FreeTrainingPage';
import HomePage from '../pages/HomePage';
import KnowledgePage from '../pages/KnowledgePage';
import LoginPage from '../pages/LoginPage';
import PetPage from '../pages/PetPage';
import PetSelectPage from '../pages/PetSelectPage';
import RankingPage from '../pages/RankingPage';
import SettlementPage from '../pages/SettlementPage';
import TrainingPage from '../pages/TrainingPage';
import TrainingSessionPage from '../pages/TrainingSessionPage';
import { useAppStore } from '../store/useAppStore';

// 新增页面（懒加载）
const TaskPackagePage = lazy(() => import('../pages/TaskPackagePage'));
const ScenarioTrainingPage = lazy(() => import('../pages/ScenarioTrainingPage'));
const EvidenceCenterPage = lazy(() => import('../pages/EvidenceCenterPage'));
const CounselorDashboardPage = lazy(() => import('../pages/CounselorDashboardPage'));
const ClassMeetingPage = lazy(() => import('../pages/ClassMeetingPage'));
const CaseLibraryPage = lazy(() => import('../pages/CaseLibraryPage'));
const AdminAuditPage = lazy(() => import('../pages/AdminAuditPage'));
const LearningGoalPage = lazy(() => import('../pages/LearningGoalPage'));
const LearningWorkspacePage = lazy(() => import('../pages/LearningWorkspacePage'));
const ArtifactStudioPage = lazy(() => import('../pages/ArtifactStudioPage'));
const LearningMarketPage = lazy(() => import('../pages/LearningMarketPage'));
const CampusActivitiesPage = lazy(() => import('../pages/CampusActivitiesPage'));
const ActivityIntroPage = lazy(() => import('../pages/ActivityIntroPage'));
const SocialCollaborationPage = lazy(() => import('../pages/SocialCollaborationPage'));
const RecommendPage = lazy(() => import('../pages/RecommendPage'));
// V3.0 双端口新增页面
const StudentThemePage = lazy(() => import('../pages/StudentThemePage'));
const ThemeTaskPage = lazy(() => import('../pages/ThemeTaskPage'));
const LearningTaskPage = lazy(() => import('../pages/LearningTaskPage'));
const GuardPage = lazy(() => import('../pages/GuardPage'));
const SchoolThemePage = lazy(() => import('../pages/SchoolThemePage'));
const SchoolLearningPage = lazy(() => import('../pages/SchoolLearningPage'));
const SchoolActivityPage = lazy(() => import('../pages/SchoolActivityPage'));

/** 带加载状态的懒加载包裹 */
function LazyPage({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<div className="flex items-center justify-center py-20 text-muted-foreground">加载中...</div>}>
      {children}
    </Suspense>
  );
}

export default function AppRouter() {
  const restoreSession = useAppStore((state) => state.restoreSession);
  const currentUser = useAppStore((state) => state.currentUser);
  const role = useAppStore((state) => state.role);

  // 启动时尝试恢复本地会话
  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  // V3.0 双端口：按角色决定登录后落点
  const effectiveRole = role ?? currentUser?.role ?? 'student';
  const homePath = effectiveRole === 'school' ? '/school/theme' : '/home';

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={currentUser ? <Navigate to={homePath} replace /> : <Navigate to="/login" replace />} />
        <Route path="/login" element={currentUser ? <Navigate to={homePath} replace /> : <LoginPage />} />
        <Route element={<StudentLayout />}>
          <Route path="/home" element={<HomePage />} />
          <Route path="/training" element={<TrainingPage />} />
          <Route path="/assessment" element={<AssessmentPage />} />
          <Route path="/assessment-result" element={<AssessmentResultPage />} />
          <Route path="/pet-select" element={<PetSelectPage />} />
          <Route path="/pet" element={<PetPage />} />
          <Route path="/training/session/:id" element={<TrainingSessionPage />} />
          <Route path="/training/settlement/:id" element={<SettlementPage />} />
          <Route path="/free-training" element={<FreeTrainingPage />} />
          <Route path="/ranking" element={<RankingPage />} />
          <Route path="/knowledge" element={<KnowledgePage />} />
          {/* V3.0 学生端新增：主题学习 & 守护共建 */}
          <Route path="/learning" element={<LazyPage><StudentThemePage /></LazyPage>} />
          <Route path="/learning/task/:itemId" element={<LazyPage><ThemeTaskPage /></LazyPage>} />
          <Route path="/learning/workspace/task/:itemId" element={<LazyPage><LearningTaskPage /></LazyPage>} />
          <Route path="/guard" element={<LazyPage><GuardPage /></LazyPage>} />
          {/* AI 学习集市主链路 */}
          <Route path="/learning/goal" element={<LazyPage><LearningGoalPage /></LazyPage>} />
          <Route path="/learning/workspace" element={<LazyPage><LearningWorkspacePage /></LazyPage>} />
          <Route path="/learning/artifacts" element={<LazyPage><ArtifactStudioPage /></LazyPage>} />
          <Route path="/learning/market" element={<LazyPage><LearningMarketPage /></LazyPage>} />
          <Route path="/learning/activities" element={<LazyPage><CampusActivitiesPage /></LazyPage>} />
          <Route path="/learning/activities/:activityId" element={<LazyPage><ActivityIntroPage /></LazyPage>} />
          <Route path="/learning/collaboration" element={<LazyPage><SocialCollaborationPage /></LazyPage>} />
          <Route path="/learning/social" element={<Navigate to="/learning/collaboration" replace />} />
          <Route path="/learning/recommend" element={<LazyPage><RecommendPage /></LazyPage>} />
          {/* 新增路由 */}
          <Route path="/task-package" element={<LazyPage><TaskPackagePage /></LazyPage>} />
          <Route path="/training/scenario/:type" element={<LazyPage><ScenarioTrainingPage /></LazyPage>} />
          <Route path="/evidence-center" element={<LazyPage><EvidenceCenterPage /></LazyPage>} />
          <Route path="/counselor/dashboard" element={<LazyPage><CounselorDashboardPage /></LazyPage>} />
          <Route path="/counselor/class-meeting" element={<LazyPage><ClassMeetingPage /></LazyPage>} />
          <Route path="/case-library" element={<LazyPage><CaseLibraryPage /></LazyPage>} />
          <Route path="/admin/audit" element={<LazyPage><AdminAuditPage /></LazyPage>} />
        </Route>
        {/* V3.0 校方发布端 */}
        <Route element={<SchoolLayout />}>
          <Route path="/school/theme" element={<LazyPage><SchoolThemePage /></LazyPage>} />
          <Route path="/school/learning" element={<LazyPage><SchoolLearningPage /></LazyPage>} />
          <Route path="/school/activity" element={<LazyPage><SchoolActivityPage /></LazyPage>} />
        </Route>
        <Route path="*" element={<Navigate to={homePath} replace />} />
      </Routes>
    </BrowserRouter>
  );
}
