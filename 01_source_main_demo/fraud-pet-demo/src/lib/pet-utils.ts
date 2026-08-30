/**
 * 宠物相关公共工具函数
 * 统一管理宠物 emoji 映射、类别样式等，避免多文件重复定义。
 */

/** 9 个宠物的 emoji 映射表 */
export const PET_EMOJI: Record<string, string> = {
  校园猫: '🐱',
  守护犬: '🐕',
  灵巧兔: '🐰',
  巡逻机器人: '🤖',
  反诈小卫士: '🦾',
  数据探测员: '📡',
  麒麟: '🦄',
  醒狮: '🦁',
  玄鸟: '🦅',
};

/** 获取宠物 emoji，未知类型返回守护盾牌 */
export function getPetEmoji(petType: string): string {
  return PET_EMOJI[petType] || '🛡️';
}

/**
 * 解析宠物实际展示用的 emoji 头像。
 * 优先使用用户自定义的 avatarEmoji（空字符串视为未设置），否则回退到类型默认。
 */
export function resolvePetAvatar(pet: { avatarEmoji?: string | null; type: string }): string {
  const custom = pet.avatarEmoji?.trim();
  return custom || getPetEmoji(pet.type);
}

/**
 * 解析宠物展示用名称。优先使用自定义昵称，否则回退到宠物类型名。
 */
export function resolvePetName(pet: { petName?: string | null; type: string }): string {
  const custom = pet.petName?.trim();
  return custom || pet.type;
}

/** 头像 emoji 候选池：用户在更换头像时可从中挑选。按类别组织便于查找。 */
export const AVATAR_EMOJI_CHOICES: { label: string; emojis: string[] }[] = [
  {
    label: '默认推荐',
    emojis: ['🐱', '🐕', '🐰', '🤖', '🦾', '📡', '🦄', '🦁', '🦅'],
  },
  {
    label: '可爱动物',
    emojis: ['🐾', '🐯', '🐻', '🐼', '🐨', '🦊', '🐮', '🐷', '🐸', '🐵', '🐔', '🦉', '🐢', '🐬'],
  },
  {
    label: '守护与能量',
    emojis: ['🛡️', '⭐', '✨', '🌟', '💫', '🔥', '⚡', '💎', '🚀', '🎯', '🌈', '☀️'],
  },
  {
    label: '趣味表情',
    emojis: ['😎', '🥳', '🤓', '🦸', '🧙', '🧚', '🦄', '🎩', '👑', '🦋'],
  },
];

/** 根据成长阶段获取带阶段修饰符的宠物 emoji（如 🐱📚） */
export function getPetStageEmoji(petType: string, stage: string): string {
  const base = getPetEmoji(petType);
  switch (stage) {
    case '学习期':
      return base + '📚';
    case '成长期':
      return base + '🛡️';
    case '进阶期':
      return base + '⚙️';
    case '反诈守护者':
      return base + '⭐';
    default:
      return base;
  }
}

/** 宠物类别对应的视觉样式（渐变/环/标签/徽章） */
export interface PetCategoryStyle {
  gradient: string;
  ring: string;
  chip: string;
  label: string;
}

export const PET_CATEGORY_STYLES: Record<string, PetCategoryStyle> = {
  动物类: {
    gradient: 'from-amber-50 to-orange-50',
    ring: 'ring-amber-200',
    chip: 'bg-amber-100 text-amber-700',
    label: '动物类',
  },
  机器人类: {
    gradient: 'from-blue-50 to-cyan-50',
    ring: 'ring-blue-200',
    chip: 'bg-blue-100 text-blue-700',
    label: '机器人类',
  },
  守护兽类: {
    gradient: 'from-violet-50 to-fuchsia-50',
    ring: 'ring-violet-200',
    chip: 'bg-violet-100 text-violet-700',
    label: '守护兽类',
  },
};

/** 获取宠物类别样式，未知类别回退到动物类 */
export function getPetCategoryStyle(category: string): PetCategoryStyle {
  return PET_CATEGORY_STYLES[category] || PET_CATEGORY_STYLES.动物类;
}
