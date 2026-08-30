import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Award, Calendar, Edit3, Loader2, PawPrint, Sparkles, X, Zap } from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/useAppStore';
import { useToast } from '../components/ui/Toast';
import {
  AVATAR_EMOJI_CHOICES,
  getPetEmoji,
  resolvePetAvatar,
  resolvePetName,
} from '../lib/pet-utils';
import { CountUp, GlowCard } from '../components/effects';
import type { PetStage } from '../types';

const STAGE_APPEARANCES: Record<string, { emoji: string; elements: string; desc: string }> = {
  幼崽期: { emoji: '🐣', elements: '基础可爱形态', desc: '刚刚诞生的守护宠物，充满好奇心' },
  学习期: { emoji: '📚', elements: '书包、徽章、提示牌', desc: '开始学习反诈知识，佩戴学习装备' },
  成长期: { emoji: '🛡️', elements: '护盾、警示灯、识别器', desc: '具备反诈能力，装备守护工具' },
  进阶期: { emoji: '⚙️', elements: '更明显的守护装备', desc: '守护能力提升，装备全面升级' },
  反诈守护者: { emoji: '⭐', elements: '完整守护形态', desc: '完整守护形态，反诈能力满级' },
};

export default function PetPage() {
  const navigate = useNavigate();
  const { pet, currentUser, updatePetProfile } = useAppStore();
  const { success, error: showError } = useToast();
  const [stages, setStages] = useState<PetStage[]>([]);

  /* 编辑资料弹窗状态 */
  const [editOpen, setEditOpen] = useState(false);
  const [editName, setEditName] = useState('');
  const [editEmoji, setEditEmoji] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    void api.getPetStages().then((res) => setStages(res.stages)).catch(() => {});
  }, []);

  if (!pet) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh] animate-fade-in">
        <div className="w-24 h-24 rounded-3xl bg-slate-50 flex items-center justify-center mb-5 border-2 border-dashed border-slate-200">
          <PawPrint size={36} className="text-slate-300" />
        </div>
        <button onClick={() => navigate('/pet-select')} className="btn-primary px-8 py-3">去领取宠物</button>
      </div>
    );
  }

  const allStages = stages.length > 0 ? stages : [
    { name: '幼崽期', levelRange: 'Lv.1-Lv.3', appearance: '基础可爱形态' },
    { name: '学习期', levelRange: 'Lv.4-Lv.7', appearance: '增加书包、徽章、提示牌等学习元素' },
    { name: '成长期', levelRange: 'Lv.8-Lv.12', appearance: '增加护盾、警示灯、识别器等反诈元素' },
    { name: '进阶期', levelRange: 'Lv.13-Lv.16', appearance: '增加更明显的守护装备' },
    { name: '反诈守护者', levelRange: 'Lv.17-Lv.20', appearance: '完整守护形态' },
  ];

  const currentStageIdx = allStages.findIndex((s) => s.name === pet.stage);
  const displayName = resolvePetName(pet);
  const displayAvatar = resolvePetAvatar(pet);
  const toNextLevel = pet.nextLevelValue - pet.growthValue;
  const progress = Math.min((pet.growthValue / pet.nextLevelValue) * 100, 100);

  const openEdit = () => {
    // 初始化编辑字段：若用户已设置，预填当前值
    setEditName(pet.petName || '');
    setEditEmoji(pet.avatarEmoji || '');
    setEditOpen(true);
  };

  const handleSave = async () => {
    setSaving(true);
    const trimmedName = editName.trim();
    const trimmedEmoji = editEmoji.trim();
    const ok = await updatePetProfile({
      petName: trimmedName || null,
      avatarEmoji: trimmedEmoji || null,
    });
    setSaving(false);
    if (ok) {
      success('宠物资料已更新');
      setEditOpen(false);
    } else {
      showError('资料更新失败，请稍后重试');
    }
  };

  return (
    <div className="space-y-5">
      {/* 宠物档案卡 */}
      <GlowCard className="animate-slide-up" glowColor="rgba(16,185,129,0.18)">
        <div className="relative p-7 overflow-hidden">
        <div className="absolute inset-0 bg-mesh opacity-70" />
        <div className="relative flex items-start justify-between mb-6">
          <div className="flex items-center gap-5">
            {/* 宠物形象 */}
            <div className="relative">
              <div className="w-28 h-28 rounded-3xl bg-gradient-to-br from-primary-soft via-white to-emerald-50 flex items-center justify-center border border-primary/15 shadow-glow-sm">
                <span className="text-5xl">{displayAvatar}</span>
              </div>
              {/* 阶段标记 */}
              {currentStageIdx >= 1 && <span className="absolute top-1 right-1 text-lg">{STAGE_APPEARANCES.学习期.emoji}</span>}
              {currentStageIdx >= 2 && <span className="absolute bottom-1 left-1 text-lg">{STAGE_APPEARANCES.成长期.emoji}</span>}
              {currentStageIdx >= 3 && <span className="absolute top-1 left-1 text-lg">{STAGE_APPEARANCES.进阶期.emoji}</span>}
              {currentStageIdx >= 4 && <span className="absolute -top-2 left-1/2 -translate-x-1/2 text-lg">{STAGE_APPEARANCES.反诈守护者.emoji}</span>}
              {/* 呼吸光环 */}
              <div className="absolute inset-0 w-28 h-28 rounded-3xl bg-primary/30 blur-xl -z-10 animate-pulse-soft" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-2.5 flex-wrap">
                <h2 className="text-2xl font-extrabold text-ink">{displayName}</h2>
                {pet.petName && pet.petName.trim() && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-subtext">{pet.type}</span>
                )}
                <span className="chip bg-slate-100 text-subtext">{pet.category}</span>
              </div>
              <div className="space-y-1.5">
                <p className="text-xs text-subtext flex items-center"><Award size={13} className="mr-1.5 text-primary" /> 宠物 ID: <span className="font-semibold text-ink ml-1">{pet.petId}</span></p>
                <p className="text-xs text-subtext flex items-center"><Activity size={13} className="mr-1.5 text-emerald-500" /> 主人 ID: <span className="font-semibold text-ink ml-1">{currentUser?.ownerId}</span></p>
                <p className="text-xs text-subtext flex items-center"><Calendar size={13} className="mr-1.5 text-violet-500" /> 最近训练: <span className="font-semibold text-ink ml-1">{pet.lastTrainingAt || '暂无'}</span></p>
              </div>
            </div>
          </div>
          <div className="text-right flex flex-col items-end gap-2">
            <div className="flex items-center gap-2 mb-1 justify-end">
              <span className="text-2xl font-black text-gradient">Lv.{pet.level}</span>
              <span className="chip bg-primary-soft text-primary">{pet.stage}</span>
            </div>
            <p className="text-3xl font-black text-growth">
              <CountUp value={pet.growthValue} duration={700} />
            </p>
            <button
              onClick={openEdit}
              className="btn-ghost px-3 py-1.5 text-xs flex items-center gap-1.5 mt-1"
            >
              <Edit3 size={13} /> 编辑资料
            </button>
          </div>
        </div>

        {/* 成长进度条 */}
        <div className="relative">
          <div className="flex justify-between text-xs text-subtext mb-1.5">
            <span>距下一级还差 <span className="font-bold text-growth">{toNextLevel}</span> 成长值</span>
            <span className="font-medium">{pet.growthValue} / {pet.nextLevelValue}</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
            <div className="h-3 rounded-full bg-gradient-to-r from-safe to-emerald-400 transition-all duration-700" style={{ width: `${progress}%` }} />
          </div>
        </div>
        </div>
      </GlowCard>

      {/* 成长阶段与外观进化预览 */}
      <div className="app-card p-7 animate-slide-up" style={{ animationDelay: '80ms' }}>
        <h3 className="font-extrabold text-ink mb-6 flex items-center">
          <Zap size={18} className="mr-2 text-warning" /> 成长阶段与外观进化
        </h3>
        <div className="flex justify-between relative mb-6">
          <div className="absolute top-6 left-[10%] right-[10%] h-0.5 bg-slate-100 -z-10" />
          {allStages.map((stage, idx) => {
            const isUnlocked = idx <= currentStageIdx;
            const isCurrent = idx === currentStageIdx;
            return (
              <div key={idx} className="flex flex-col items-center text-center" style={{ width: '20%' }}>
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center mb-2 border-2 transition-all ${
                    isCurrent ? 'bg-gradient-to-br from-primary to-primary-deep text-white border-primary scale-110 shadow-glow-sm' :
                    isUnlocked ? 'bg-emerald-50 text-safe border-emerald-200' :
                    'bg-slate-50 text-slate-300 border-slate-200'
                  }`}
                >
                  {isUnlocked ? <span className="text-lg">{displayAvatar}</span> : <span className="text-sm font-bold">{idx + 1}</span>}
                </div>
                <p className={`text-xs font-medium mb-0.5 ${isUnlocked ? 'text-ink' : 'text-subtext'}`}>{stage.name}</p>
                <p className="text-[10px] text-subtext">{stage.levelRange}</p>
              </div>
            );
          })}
        </div>

        {/* 当前阶段外观详情 */}
        <div className="rounded-2xl p-4 bg-gradient-to-br from-primary-soft/50 to-emerald-50/50 border border-primary/10">
          <div className="flex items-start gap-3">
            <span className="text-2xl">{displayAvatar}{currentStageIdx >= 1 && STAGE_APPEARANCES[pet.stage]?.emoji}</span>
            <div>
              <p className="text-sm font-semibold text-ink mb-0.5">当前外观: {pet.stage}</p>
            </div>
          </div>
        </div>
      </div>

      {/* 成长记录 */}
      <div className="app-card p-7 animate-slide-up" style={{ animationDelay: '160ms' }}>
        <h3 className="font-extrabold text-ink mb-4 flex items-center"><Sparkles size={18} className="mr-2 text-primary" /> 成长记录</h3>
        <div className="space-y-3">
          <RecordRow emoji="📋" title="完成首次测评" desc="解锁宠物选择池" status="已完成" statusColor="safe" />
          <RecordRow emoji="🐾" title="领取守护宠物" desc={`${displayName}（${pet.type}） · ${pet.petId}`} status="已完成" statusColor="safe" />
          <RecordRow emoji="💪" title="当前成长值" desc={`Lv.${pet.level} · ${pet.growthValue} 成长值`} status="进行中" statusColor="primary" />
        </div>
      </div>

      {/* ── 编辑资料弹窗 ── */}
      {editOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => !saving && setEditOpen(false)} />
          <div className="relative z-10 w-full max-w-lg max-h-[90vh] overflow-y-auto bg-white rounded-3xl shadow-glow-lg">
            {/* 头部 */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 sticky top-0 bg-white/95 backdrop-blur-sm z-10">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{displayAvatar}</span>
                <div>
                  <h3 className="text-lg font-bold text-ink">编辑宠物资料</h3>
                  <p className="text-xs text-subtext">设置昵称与头像，让你的伙伴更独特</p>
                </div>
              </div>
              <button
                onClick={() => !saving && setEditOpen(false)}
                disabled={saving}
                className="btn-ghost p-2 rounded-full disabled:opacity-50"
                aria-label="关闭"
              >
                <X size={20} />
              </button>
            </div>

            {/* 表单内容 */}
            <div className="px-6 py-5 space-y-5">
              {/* 昵称输入 */}
              <div>
                <label className="block text-sm font-semibold text-ink mb-2">
                  宠物昵称
                </label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value.slice(0, 20))}
                  placeholder={`例如：${pet.type}小宝`}
                  maxLength={20}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-sm text-ink placeholder:text-subtext/50 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 focus:bg-white transition"
                />
                <div className="flex justify-between mt-1.5">
                  <p className="text-[11px] text-subtext">{editName.length}/20</p>
                </div>
              </div>

              {/* 头像选择 */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-semibold text-ink">头像 Emoji</label>
                  <button
                    type="button"
                    onClick={() => setEditEmoji('')}
                    className="text-xs text-subtext hover:text-primary transition"
                  >
                    恢复默认（{getPetEmoji(pet.type)}）
                  </button>
                </div>
                {/* 当前选中预览 */}
                <div className="flex items-center gap-3 mb-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-soft via-white to-emerald-50 flex items-center justify-center border border-primary/15">
                    <span className="text-2xl">{editEmoji.trim() || getPetEmoji(pet.type)}</span>
                  </div>
                  <span className="text-sm font-semibold text-ink">
                    {editName.trim() || pet.type}
                  </span>
                </div>
                {/* 候选网格 */}
                <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
                  {AVATAR_EMOJI_CHOICES.map((group) => (
                    <div key={group.label}>
                      <p className="text-[11px] text-subtext/70 mb-1.5 font-medium uppercase tracking-wide">{group.label}</p>
                      <div className="flex flex-wrap gap-1.5">
                        {group.emojis.map((emoji) => {
                          const isSelectedEmoji = emoji === editEmoji.trim();
                          const isDefault = emoji === getPetEmoji(pet.type);
                          return (
                            <button
                              key={emoji}
                              type="button"
                              onClick={() => setEditEmoji(emoji)}
                              className={`relative w-10 h-10 rounded-xl flex items-center justify-center text-xl transition-all ${
                                isSelectedEmoji
                                  ? 'bg-primary-soft ring-2 ring-primary scale-110'
                                  : 'bg-white hover:bg-slate-50 hover:scale-105 border border-slate-100'
                              }`}
                            >
                              {emoji}
                              {isDefault && !isSelectedEmoji && (
                                <span className="absolute -top-1 -right-1 px-1 py-0.5 rounded-full bg-emerald-100 text-emerald-700 text-[8px] font-bold leading-none">
                                  默认
                                </span>
                              )}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* 底部操作栏 */}
            <div className="px-6 py-4 border-t border-slate-100 flex items-center justify-end gap-3 sticky bottom-0 bg-white/95 backdrop-blur-sm">
              <button
                onClick={() => setEditOpen(false)}
                disabled={saving}
                className="btn-ghost px-5 py-2.5 disabled:opacity-50"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="btn-primary px-6 py-2.5 flex items-center gap-2 disabled:opacity-60"
              >
                {saving ? <Loader2 size={15} className="animate-spin" /> : <Edit3 size={15} />}
                {saving ? '保存中...' : '保存资料'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function RecordRow({ emoji, title, desc, status, statusColor }: { emoji: string; title: string; desc: string; status: string; statusColor: 'safe' | 'primary' }) {
  const colorCls = statusColor === 'safe' ? 'text-safe' : 'text-primary';
  return (
    <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50/80 border border-slate-100 hover:border-primary/20 transition-colors">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-white border border-slate-100 flex items-center justify-center text-base shadow-sm">{emoji}</div>
        <div>
          <p className="text-sm font-semibold text-ink">{title}</p>
          <p className="text-xs text-subtext">{desc}</p>
        </div>
      </div>
      <span className={`text-xs font-semibold ${colorCls}`}>{status}</span>
    </div>
  );
}
