import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertCircle,
  ArrowRight,
  Building2,
  Eye,
  EyeOff,
  GraduationCap,
  Lock,
  ShieldCheck,
  User as UserIcon,
  Zap,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Label } from '../components/ui/Label';
import { Separator } from '../components/ui/Separator';
import { useToast } from '../components/ui/Toast';

type Mode = 'login' | 'register' | 'campus';

export default function LoginPage() {
  const navigate = useNavigate();
  const login = useAppStore((state) => state.login);
  const loginWithCredentials = useAppStore((state) => state.loginWithCredentials);
  const register = useAppStore((state) => state.register);
  const schoolLogin = useAppStore((state) => state.schoolLogin);
  const campusLogin = useAppStore((state) => state.campusLogin);
  const isLoading = useAppStore((state) => state.isLoading);
  const error = useAppStore((state) => state.error);
  const { success } = useToast();

  const [mode, setMode] = useState<Mode>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [nickname, setNickname] = useState('');
  const [studentId, setStudentId] = useState('');
  const [school, setSchool] = useState('');
  const [department, setDepartment] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  // 演示入口：仅开发环境且显式携带 ?demo=1 时可见；生产构建默认隐藏
  const demoEnabled = import.meta.env.DEV && new URLSearchParams(window.location.search).get('demo') === '1';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);

    if (mode === 'campus') {
      if (studentId.trim().length < 4) {
        setLocalError('请输入至少 4 位学号');
        return;
      }
      if (school.trim().length < 2) {
        setLocalError('请输入学校名称');
        return;
      }
      const ok = await campusLogin(studentId.trim(), school.trim(), department.trim());
      if (ok) {
        success('校园账号登录成功');
        navigate('/home');
      }
      return;
    }

    if (mode === 'register') {
      if (username.trim().length < 3) {
        setLocalError('账号名至少 3 个字符');
        return;
      }
      if (password.length < 6) {
        setLocalError('密码至少 6 位');
        return;
      }
      if (password !== confirmPassword) {
        setLocalError('两次输入的密码不一致');
        return;
      }
      const ok = await register(username.trim(), password, nickname.trim());
      if (ok) {
        success('注册成功，欢迎加入诈醒学集');
        navigate('/home');
      }
    } else {
      if (!username.trim() || !password) {
        setLocalError('请输入账号和密码');
        return;
      }
      const ok = await loginWithCredentials(username.trim(), password);
      if (ok) {
        success('登录成功，欢迎回来');
        navigate('/home');
      }
    }
  };

  const handleDemoLogin = async () => {
    setLocalError(null);
    const demoOwnerId = import.meta.env.VITE_DEMO_OWNER_ID || '';
    if (!demoOwnerId) {
      setLocalError('体验账号未配置，无法进入');
      return;
    }
    await login(demoOwnerId);
    const currentUser = useAppStore.getState().currentUser;
    if (currentUser) {
      success('登录成功，欢迎回来');
      navigate('/home');
    }
  };

  const handleSchoolLogin = async () => {
    setLocalError(null);
    const ok = await schoolLogin();
    if (ok) {
      success('已进入校方发布端');
      navigate('/school/theme');
    }
  };

  const displayError = localError || error;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex">
      {/* 左侧品牌区 */}
      <div className="hidden lg:flex lg:w-1/2 bg-white border-r border-slate-200 flex-col justify-between p-12 xl:p-16">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center">
              <GraduationCap size={22} className="text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-slate-900">诈醒学集</h1>
              <p className="text-xs text-slate-500">大学生 AI 主题学习与成果展示平台</p>
            </div>
          </div>

          <div className="mt-16 max-w-md">
              <h2 className="text-4xl xl:text-5xl font-semibold text-slate-900 leading-tight">
                在 AI 主题中
                <br />
                <span className="text-indigo-600">系统学习与成果展示</span>
              </h2>
              <p className="mt-5 text-slate-600 leading-relaxed">
                通过 AI 测评、情景训练、多主题知识库与成果创作，帮助大学生在网络安全、心理健康、求职就业、金融素养等 11 个主题中系统学习、持续成长并展示学习成果。
              </p>
          </div>
        </div>

        <p className="text-xs text-slate-400">启智杯 AI 应用成果挑战赛 · 参赛作品</p>
      </div>

      {/* 右侧认证区 */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-md">
          {/* 移动端品牌 */}
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center">
              <GraduationCap size={22} className="text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-slate-900">诈醒学集</h1>
              <p className="text-[11px] text-slate-500">大学生 AI 主题学习与成果展示平台</p>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-7 sm:p-9 shadow-sm">
            <div className="mb-6">
              <h2 className="text-2xl font-semibold mb-1.5 text-slate-900">
                {mode === 'login' ? '欢迎回来' : mode === 'register' ? '创建账号' : '校园账号登录'}
              </h2>
              <p className="text-sm text-slate-500">
                {mode === 'login'
                  ? '登录后开启你的主题学习计划'
                  : mode === 'register'
                  ? '注册后自动生成学习身份，数据由你掌控'
                  : '使用学号和学校信息登录'}
              </p>
            </div>

            {/* 模式切换 */}
            <div
              role="tablist"
              aria-label="认证模式"
              className="grid grid-cols-3 gap-1 p-1 rounded-xl bg-slate-100 mb-6"
            >
              {(['login', 'register', 'campus'] as Mode[]).map((m) => (
                <button
                  key={m}
                  role="tab"
                  aria-selected={mode === m}
                  onClick={() => { setMode(m); setLocalError(null); }}
                  className={`inline-flex h-9 items-center justify-center rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${
                    mode === m
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  {m === 'login' ? '登录' : m === 'register' ? '注册' : '校园账号'}
                </button>
              ))}
            </div>

            <form onSubmit={handleSubmit} noValidate autoComplete="off" className="space-y-4">
              {mode === 'campus' ? (
                <>
                  <Field
                    id="login-studentId"
                    icon={<GraduationCap size={16} className="text-slate-400" />}
                    label="学号"
                    type="text"
                    value={studentId}
                    onChange={setStudentId}
                    placeholder="请输入学号（至少 4 位）"
                    autoComplete="off"
                    invalid={Boolean(displayError)}
                  />
                  <Field
                    id="login-school"
                    icon={<Building2 size={16} className="text-slate-400" />}
                    label="学校"
                    type="text"
                    value={school}
                    onChange={setSchool}
                    placeholder="例如：某某大学"
                    autoComplete="off"
                    invalid={Boolean(displayError)}
                  />
                  <Field
                    id="login-department"
                    icon={<Building2 size={16} className="text-slate-400" />}
                    label="院系（选填）"
                    type="text"
                    value={department}
                    onChange={setDepartment}
                    placeholder="例如：计算机学院"
                    autoComplete="off"
                  />
                </>
              ) : (
                <>
                  <Field
                    id="login-username"
                    icon={<UserIcon size={16} className="text-slate-400" />}
                    label="账号"
                    type="text"
                    value={username}
                    onChange={setUsername}
                    placeholder="3-20 位账号名"
                    autoComplete="new-username"
                    invalid={Boolean(displayError)}
                  />
                  {mode === 'register' && (
                    <Field
                      id="login-nickname"
                      icon={<UserIcon size={16} className="text-slate-400" />}
                      label="昵称（选填）"
                      type="text"
                      value={nickname}
                      onChange={setNickname}
                      placeholder="给自己起个昵称"
                    />
                  )}
                </>
              )}

              {mode !== 'campus' && (
                <div>
                  <Label htmlFor="login-password" className="text-xs text-slate-600 mb-1.5 block">
                    密码
                  </Label>
                  <div className="relative">
                    <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" aria-hidden="true">
                      <Lock size={16} />
                    </span>
                    <Input
                      id="login-password"
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder={mode === 'register' ? '至少 6 位' : '请输入密码'}
                      autoComplete="new-password"
                      aria-invalid={Boolean(displayError)}
                      className="bg-white border-slate-200 text-slate-900 placeholder:text-slate-400 pl-10 pr-11 h-11 rounded-xl focus-visible:border-indigo-500 focus-visible:ring-indigo-500/20"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((v) => !v)}
                      aria-label={showPassword ? '隐藏密码' : '显示密码'}
                      aria-pressed={showPassword}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 rounded-md p-0.5"
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>
              )}

              {mode === 'register' && (
                <Field
                  id="login-confirm"
                  icon={<Lock size={16} className="text-slate-400" />}
                  label="确认密码"
                  type="password"
                  value={confirmPassword}
                  onChange={setConfirmPassword}
                  placeholder="再次输入密码"
                  autoComplete="new-password"
                  invalid={Boolean(displayError)}
                />
              )}

              {displayError && (
                <div
                  role="alert"
                  aria-live="assertive"
                  className="flex items-start gap-2 text-sm text-rose-600 bg-rose-50 border border-rose-200 rounded-xl px-3.5 py-2.5"
                >
                  <AlertCircle size={16} className="mt-0.5 flex-shrink-0" aria-hidden="true" />
                  <span>{displayError}</span>
                </div>
              )}

              <Button
                type="submit"
                size="lg"
                loading={isLoading}
                fullWidth
                className="mt-1 bg-indigo-600 hover:bg-indigo-700 text-white"
              >
                {isLoading ? '处理中...' : (
                  <>
                    {mode === 'login' ? '登录' : mode === 'register' ? '注册并进入' : '校园账号登录'}
                    <ArrowRight size={18} aria-hidden="true" />
                  </>
                )}
              </Button>
            </form>

            {mode === 'register' && password.length > 0 && (
              <div className="text-[11px] text-slate-500 mt-3" aria-live="polite">
                {password.length < 6
                  ? '密码至少 6 位，建议字母数字混合'
                  : '密码强度合格'}
              </div>
            )}

            {demoEnabled && (
              <>
                <div className="flex items-center gap-3 my-6">
                  <Separator className="flex-1 bg-slate-200" />
                  <span className="text-xs text-slate-400">快速体验</span>
                  <Separator className="flex-1 bg-slate-200" />
                </div>
                <div className="space-y-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="lg"
                    fullWidth
                    onClick={handleDemoLogin}
                    disabled={isLoading}
                    className="border-slate-200 text-slate-700 hover:bg-slate-50"
                  >
                    <Zap size={15} className="text-amber-500" />
                    体验账号一键进入
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="lg"
                    fullWidth
                    onClick={handleSchoolLogin}
                    disabled={isLoading}
                    className="border-slate-200 text-slate-700 hover:bg-slate-50"
                  >
                    <ShieldCheck size={15} className="text-indigo-500" />
                    校方发布端入口
                  </Button>
                </div>
              </>
            )}

            <p className="text-[11px] text-slate-400 text-center mt-6 leading-relaxed">
              本平台用于大学生 AI 主题学习与成果展示，不替代学校专业指导。
            </p>
          </div>

          <p className="text-center text-xs text-slate-500 mt-5">
            {mode === 'login' ? '还没有账号？' : '已有账号？'}
            <button
              onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setLocalError(null); }}
              className="ml-1 text-indigo-600 hover:text-indigo-700 font-medium"
            >
              {mode === 'login' ? '立即注册' : '去登录'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

interface FieldProps {
  icon: React.ReactNode;
  label: string;
  type: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  autoComplete?: string;
  id: string;
  invalid?: boolean;
}

function Field({ icon, label, type, value, onChange, placeholder, autoComplete, id, invalid }: FieldProps) {
  return (
    <div>
      <Label htmlFor={id} className="text-xs text-slate-600 mb-1.5 block">{label}</Label>
      <div className="relative">
        <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" aria-hidden="true">{icon}</span>
        <Input
          id={id}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoComplete={autoComplete}
          aria-invalid={invalid}
          className="bg-white border-slate-200 text-slate-900 placeholder:text-slate-400 pl-10 pr-4 h-11 rounded-xl focus-visible:border-indigo-500 focus-visible:ring-indigo-500/20"
        />
      </div>
    </div>
  );
}
