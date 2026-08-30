import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Heart, Sparkles, X, ChevronLeft, ChevronRight, Eye, Smile } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { PET_EMOJI, getPetEmoji, getPetCategoryStyle, AVATAR_EMOJI_CHOICES } from '../lib/pet-utils';
import { useToast } from '../components/ui/Toast';


/* ── 5阶段IP形象图路径 ── */
const PET_STAGE_IMAGES: Record<string, string[]> = {
  校园猫: [
    '/pets/校园猫/01_幼年态_Lv1-Lv3.png',
    '/pets/校园猫/02_学习态_Lv4-Lv7.png',
    '/pets/校园猫/03_成长态_Lv8-Lv12.png',
    '/pets/校园猫/04_进阶段_Lv13-Lv16.png',
    '/pets/校园猫/05_反诈守护者_Lv17-Lv20.png',
  ],
  守护犬: [
    '/pets/守护犬/01_幼年态_Lv1-Lv3.png',
    '/pets/守护犬/02_学习态_Lv4-Lv7.png',
    '/pets/守护犬/03_成长态_Lv8-Lv12.png',
    '/pets/守护犬/04_进阶段_Lv13-Lv16.png',
    '/pets/守护犬/05_反诈守护者_Lv17-Lv20.png',
  ],
  灵巧兔: [
    '/pets/灵巧兔/01_幼年态_Lv1-Lv3.png',
    '/pets/灵巧兔/02_学习态_Lv4-Lv7.png',
    '/pets/灵巧兔/03_成长态_Lv8-Lv12.png',
    '/pets/灵巧兔/04_进阶段_Lv13-Lv16.png',
    '/pets/灵巧兔/05_反诈守护者_Lv17-Lv20.png',
  ],
  巡逻机器人: [
    '/pets/巡逻机器人/01_幼年态_Lv1-Lv3.png',
    '/pets/巡逻机器人/02_学习态_Lv4-Lv7.png',
    '/pets/巡逻机器人/03_成长态_Lv8-Lv12.png',
    '/pets/巡逻机器人/04_进阶段_Lv13-Lv16.png',
    '/pets/巡逻机器人/05_反诈守护者_Lv17-Lv20.png',
  ],
  反诈小卫士: [
    '/pets/反诈小卫士/01_幼年态_Lv1-Lv3.png',
    '/pets/反诈小卫士/02_学习态_Lv4-Lv7.png',
    '/pets/反诈小卫士/03_成长态_Lv8-Lv12.png',
    '/pets/反诈小卫士/04_进阶段_Lv13-Lv16.png',
    '/pets/反诈小卫士/05_反诈守护者_Lv17-Lv20.png',
  ],
  数据探测员: [
    '/pets/数据探测员/01_幼年态_Lv1-Lv3.png',
    '/pets/数据探测员/02_学习态_Lv4-Lv7.png',
    '/pets/数据探测员/03_成长态_Lv8-Lv12.png',
    '/pets/数据探测员/04_进阶段_Lv13-Lv16.png',
    '/pets/数据探测员/05_反诈守护者_Lv17-Lv20.png',
  ],
  麒麟: [
    '/pets/麒麟/01_幼年态_Lv1-Lv3.png',
    '/pets/麒麟/02_学习态_Lv4-Lv7.png',
    '/pets/麒麟/03_成长态_Lv8-Lv12.png',
    '/pets/麒麟/04_进阶段_Lv13-Lv16.png',
    '/pets/麒麟/05_反诈守护者_Lv17-Lv20.png',
  ],
  醒狮: [
    '/pets/醒狮/01_幼年态_Lv1-Lv3.png',
    '/pets/醒狮/02_学习态_Lv4-Lv7.png',
    '/pets/醒狮/03_成长态_Lv8-Lv12.png',
    '/pets/醒狮/04_进阶段_Lv13-Lv16.png',
    '/pets/醒狮/05_反诈守护者_Lv17-Lv20.png',
  ],
  玄鸟: [
    '/pets/玄鸟/01_幼年态_Lv1-Lv3.png',
    '/pets/玄鸟/02_学习态_Lv4-Lv7.png',
    '/pets/玄鸟/03_成长态_Lv8-Lv12.png',
    '/pets/玄鸟/04_进阶段_Lv13-Lv16.png',
    '/pets/玄鸟/05_反诈守护者_Lv17-Lv20.png',
  ],
};

const STAGE_META = [
  { name: '幼年态', level: 'Lv1-Lv3', color: 'bg-emerald-100 text-emerald-700', border: 'border-emerald-200' },
  { name: '学习态', level: 'Lv4-Lv7', color: 'bg-sky-100 text-sky-700', border: 'border-sky-200' },
  { name: '成长态', level: 'Lv8-Lv12', color: 'bg-amber-100 text-amber-700', border: 'border-amber-200' },
  { name: '进阶段', level: 'Lv13-Lv16', color: 'bg-violet-100 text-violet-700', border: 'border-violet-200' },
  { name: '反诈守护者', level: 'Lv17-Lv20', color: 'bg-rose-100 text-rose-700', border: 'border-rose-200' },
];

export default function PetSelectPage() {
  const navigate = useNavigate();
  const { adoptPet, loadPetsPool, petsPool, error } = useAppStore();
  const { success, error: showError } = useToast();
  const [selectedPet, setSelectedPet] = useState<(typeof petsPool)[0] | null>(null);
  const [adopting, setAdopting] = useState(false);

  /* 用户自定义昵称与头像 */
  const [petName, setPetName] = useState('');
  const [avatarEmoji, setAvatarEmoji] = useState<string>('');
  const [showAvatarPicker, setShowAvatarPicker] = useState(false);

  /* IP形象展示弹窗状态 */
  const [showcasePet, setShowcasePet] = useState<string | null>(null);
  const [showcaseStage, setShowcaseStage] = useState(0);
  const [imgLoaded, setImgLoaded] = useState(false);

  useEffect(() => {
    void loadPetsPool();
  }, [loadPetsPool]);

  // 切换选中宠物时重置昵称与头像（保证默认体验）
  const handleSelectPet = (p: (typeof petsPool)[0]) => {
    setSelectedPet(p);
    setPetName('');
    setAvatarEmoji('');
    setShowAvatarPicker(false);
  };

  const handleAdopt = async () => {
    if (!selectedPet) return;
    setAdopting(true);
    const trimmedName = petName.trim();
    const trimmedEmoji = avatarEmoji.trim();
    const ok = await adoptPet(selectedPet.name, trimmedName || undefined, trimmedEmoji || undefined);
    setAdopting(false);
    if (ok) {
      const displayName = trimmedName || selectedPet.name;
      success(`已成功领养 ${displayName}，开始你的反诈训练之旅吧！`);
      navigate('/pet');
    } else if (error) {
      showError(error);
    } else {
      showError('领取宠物失败，请稍后重试');
    }
  };

  // 当前展示用 emoji：用户选择了自定义则用自定义，否则用类型默认
  const currentDisplayEmoji = avatarEmoji || (selectedPet ? getPetEmoji(selectedPet.name) : '🛡️');

  const openShowcase = (petName: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setShowcasePet(petName);
    setShowcaseStage(0);
    setImgLoaded(false);
  };

  const closeShowcase = () => {
    setShowcasePet(null);
    setShowcaseStage(0);
  };

  const changeStage = (dir: number) => {
    if (!showcasePet) return;
    const stages = PET_STAGE_IMAGES[showcasePet] ?? [];
    const next = (showcaseStage + dir + stages.length) % stages.length;
    setShowcaseStage(next);
    setImgLoaded(false);
  };

  return (
    <div className="space-y-6">
      <div className="text-center mb-4 animate-slide-up">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary-soft text-primary text-xs font-medium mb-3">
          <Sparkles size={13} /> 宠物选择池已解锁
        </div>
        <h2 className="text-3xl font-black text-ink mb-2">选择你的反诈守护宠</h2>
        <p className="text-sm text-subtext max-w-2xl mx-auto">所有宠物成长规则完全一致，外观不同但不影响成长速度和排行榜公平性，请选择你喜欢的伙伴</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {petsPool.map((p, idx) => {
          const isSelected = selectedPet?.name === p.name;
          const emoji = PET_EMOJI[p.name] || '🛡️';
          const style = getPetCategoryStyle(p.category);
          return (
            <div
              key={idx}
              onClick={() => handleSelectPet(p)}
              className={`relative app-card p-5 cursor-pointer transition-all duration-300 animate-slide-up overflow-hidden ${
                isSelected
                  ? 'border-primary ring-2 ring-primary/30 shadow-glow -translate-y-1'
                  : 'app-card-hover'
              }`}
              style={{ animationDelay: `${idx * 50}ms` }}
            >
              {isSelected && (
                <div className="absolute top-3 right-3 w-7 h-7 rounded-full bg-gradient-to-br from-primary to-primary-deep flex items-center justify-center shadow-glow-sm z-10">
                  <Check size={15} className="text-white" />
                </div>
              )}
              <div className={`relative w-full h-36 rounded-2xl bg-gradient-to-br ${style.gradient} flex justify-center items-center border border-white/60 mb-4 overflow-hidden`}>
                <div className="absolute -top-4 -right-4 w-20 h-20 rounded-full bg-white/40 blur-2xl" />
                <div className="absolute -bottom-6 -left-6 w-24 h-24 rounded-full bg-white/30 blur-2xl" />
                <span className="relative text-6xl transition-transform duration-300 group-hover:scale-110" style={{ transform: isSelected ? 'scale(1.1)' : undefined }}>{emoji}</span>
              </div>
              <h3 className="font-extrabold text-ink text-center mb-1.5">{p.name}</h3>
              <div className="flex justify-center mb-2.5">
                <span className={`chip ${style.chip}`}>{style.label}</span>
              </div>
              {/* 查看IP形象按钮 */}
              <div className="flex justify-center">
                <button
                  onClick={(e) => openShowcase(p.name, e)}
                  className="btn-ghost px-3 py-1.5 text-xs flex items-center gap-1.5"
                >
                  <Eye size={13} /> 查看IP形象
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* 底部确认栏 */}
      <div className="sticky bottom-4 z-20">
        <div className="glass rounded-2xl p-5 shadow-glow space-y-4">
          {/* 第一行：昵称 + 头像选择 + 确认按钮 */}
          <div className="flex flex-col md:flex-row md:items-center gap-4">
            <div className="flex-1 min-w-0">
              <label className="block text-xs text-subtext mb-1.5 font-medium">
                给它取个名字
                <span className="text-subtext/60">（选填，留空使用默认类型名）</span>
              </label>
              <input
                type="text"
                value={petName}
                onChange={(e) => setPetName(e.target.value.slice(0, 20))}
                placeholder={selectedPet ? `例如：${selectedPet.name}小宝` : '请先选择宠物'}
                disabled={!selectedPet}
                maxLength={20}
                className="w-full px-4 py-2.5 rounded-xl bg-white/80 border border-slate-200 text-sm text-ink placeholder:text-subtext/50 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 transition disabled:opacity-50 disabled:cursor-not-allowed"
              />
            </div>

            {/* 头像选择 */}
            <div className="md:w-auto">
              <label className="block text-xs text-subtext mb-1.5 font-medium">头像</label>
              <button
                type="button"
                onClick={() => setShowAvatarPicker((v) => !v)}
                disabled={!selectedPet}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/80 border border-slate-200 hover:border-primary/40 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span className="text-2xl leading-none">{currentDisplayEmoji}</span>
                <Smile size={16} className="text-subtext" />
                <span className="text-xs text-subtext">{avatarEmoji ? '已自定义' : '默认'}</span>
              </button>
            </div>

            <button
              disabled={!selectedPet || adopting}
              onClick={handleAdopt}
              className="btn-primary px-8 py-3 flex items-center gap-2 justify-center md:self-end"
            >
              <Heart size={16} /> {adopting ? '领取中...' : '确认领取'}
            </button>
          </div>

          {/* 第二行：头像候选网格（折叠展开） */}
          {showAvatarPicker && selectedPet && (
            <div className="rounded-xl bg-white/70 border border-slate-100 p-4 animate-fade-in">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs font-semibold text-ink">选择喜欢的头像</p>
                <button
                  type="button"
                  onClick={() => {
                    setAvatarEmoji('');
                    setShowAvatarPicker(false);
                  }}
                  className="text-xs text-subtext hover:text-primary transition"
                >
                  恢复默认
                </button>
              </div>
              <div className="space-y-3 max-h-52 overflow-y-auto">
                {AVATAR_EMOJI_CHOICES.map((group) => (
                  <div key={group.label}>
                    <p className="text-[11px] text-subtext/70 mb-1.5 font-medium uppercase tracking-wide">{group.label}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {group.emojis.map((emoji) => {
                        const isSelectedEmoji = emoji === avatarEmoji;
                        const isDefault = emoji === getPetEmoji(selectedPet.name);
                        return (
                          <button
                            key={emoji}
                            type="button"
                            onClick={() => {
                              setAvatarEmoji(emoji);
                              setShowAvatarPicker(false);
                            }}
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
          )}

          {/* 当前选择摘要 */}
          <div className="text-sm text-subtext text-center border-t border-slate-100 pt-3">
            已选择：<span className="font-bold text-primary text-base">{selectedPet ? `${currentDisplayEmoji} ${petName.trim() || selectedPet.name}` : '未选择'}</span>
          </div>
        </div>
      </div>

      {/* ── IP形象展示弹窗 ── */}
      {showcasePet && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8">
          {/* 遮罩 */}
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={closeShowcase} />
          {/* 内容面板 */}
          <div className="relative z-10 w-full max-w-5xl max-h-[92vh] bg-white rounded-3xl shadow-glow-lg overflow-hidden flex flex-col">
            {/* 头部 */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-white/80 backdrop-blur-sm z-10">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{PET_EMOJI[showcasePet] || '🛡️'}</span>
                <div>
                  <h3 className="text-lg font-bold text-ink">{showcasePet} · 3D IP形象</h3>
                </div>
              </div>
              <button onClick={closeShowcase} className="btn-ghost p-2 rounded-full">
                <X size={20} />
              </button>
            </div>

            {/* 主图区域 */}
            <div className="flex-1 flex flex-col items-center justify-center bg-gradient-to-b from-gray-50 to-white px-6 py-4 min-h-[300px] relative">
              {/* 左右切换 */}
              <button
                onClick={() => changeStage(-1)}
                className="absolute left-3 top-1/2 -translate-y-1/2 btn-ghost p-2 rounded-full z-10"
              >
                <ChevronLeft size={24} />
              </button>
              <button
                onClick={() => changeStage(1)}
                className="absolute right-3 top-1/2 -translate-y-1/2 btn-ghost p-2 rounded-full z-10"
              >
                <ChevronRight size={24} />
              </button>

              <div className="relative w-full max-w-3xl flex justify-center items-center">
                {!imgLoaded && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-10 h-10 rounded-full border-2 border-primary border-t-transparent animate-spin" />
                  </div>
                )}
                <img
                  key={showcaseStage}
                  src={PET_STAGE_IMAGES[showcasePet][showcaseStage]}
                  alt={`${showcasePet} ${STAGE_META[showcaseStage].name}`}
                  className={`max-w-full max-h-[55vh] object-contain rounded-2xl transition-opacity duration-300 ${imgLoaded ? 'opacity-100' : 'opacity-0'}`}
                  onLoad={() => setImgLoaded(true)}
                />
              </div>

              {/* 阶段信息 */}
              <div className="mt-4 text-center">
                <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold mb-1 ${STAGE_META[showcaseStage].color}`}>
                  {STAGE_META[showcaseStage].name} · {STAGE_META[showcaseStage].level}
                </span>
              </div>
            </div>

            {/* 底部阶段切换条 */}
            <div className="px-6 py-4 bg-white border-t border-gray-100">
              <div className="grid grid-cols-5 gap-2">
                {STAGE_META.map((stage, idx) => {
                  const isActive = idx === showcaseStage;
                  const imgPath = PET_STAGE_IMAGES[showcasePet][idx];
                  return (
                    <button
                      key={idx}
                      onClick={() => { setShowcaseStage(idx); setImgLoaded(false); }}
                      className={`relative rounded-xl p-2 transition-all duration-200 flex flex-col items-center gap-1 ${
                        isActive
                          ? `bg-white ring-2 ring-offset-1 ring-primary shadow-glow-sm ${stage.border}`
                          : 'bg-gray-50 hover:bg-gray-100'
                      }`}
                    >
                      <div className="w-full aspect-[4/3] rounded-lg overflow-hidden bg-white">
                        <img
                          src={imgPath}
                          alt={stage.name}
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                      </div>
                      <span className={`text-[10px] font-semibold leading-tight ${isActive ? 'text-primary' : 'text-gray-500'}`}>{stage.name}</span>
                      <span className="text-[9px] text-gray-400 leading-tight">{stage.level}</span>
                      {isActive && (
                        <div className="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full bg-primary text-white flex items-center justify-center text-[10px] font-bold shadow-sm">
                          {idx + 1}
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
