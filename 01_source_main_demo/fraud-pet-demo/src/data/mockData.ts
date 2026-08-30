import type { User, Pet, TrainingTask } from '../types';

export const mockUser: User = {
  ownerId: 'U-2408**',
  hasCompletedAssessment: false,
  hasPet: false,
};

export const petsPool: Array<{
  name: string;
  category: Pet['category'];
  desc: string;
}> = [
  { name: '校园猫', category: '动物类', desc: '机敏观察，擅长发现异常话术' },
  { name: '守护犬', category: '动物类', desc: '可靠坚定，提醒你核验身份' },
  { name: '灵巧兔', category: '动物类', desc: '反应迅速，识别限时诱导' },
  { name: '巡逻机器人', category: '机器人类', desc: '扫描风险信号，守护账户安全' },
  { name: '反诈小卫士', category: '机器人类', desc: '佩戴盾牌徽章，陪伴完成训练' },
  { name: '数据探测员', category: '机器人类', desc: '用数据雷达发现高危话术' },
  { name: '麒麟', category: '守护兽类', desc: '东方守护兽，象征安全与判断力' },
  { name: '醒狮', category: '守护兽类', desc: '醒目警示，提醒识别骗局' },
  { name: '玄鸟', category: '守护兽类', desc: '数据光翼，快速识别异常' },
];

export const trainingTasks: TrainingTask[] = [
  { id: 'ai-face', title: 'AI 换脸借钱识别', fraudType: 'AI 换脸', riskLevel: '高风险', difficulty: '中等', duration: '6 分钟', reward: 80 },
  { id: 'brushing', title: '兼职刷单返利骗局', fraudType: '刷单返利', riskLevel: '高风险', difficulty: '中等', duration: '5 分钟', reward: 70 },
  { id: 'refund', title: '网购退款屏幕共享', fraudType: '冒充客服', riskLevel: '高风险', difficulty: '中等', duration: '5 分钟', reward: 60 },
  { id: 'game', title: '游戏账号交易保证金', fraudType: '游戏交易', riskLevel: '中风险', difficulty: '低', duration: '4 分钟', reward: 40 },
  { id: 'investment', title: '虚假投资理财平台', fraudType: '虚假投资', riskLevel: '高风险', difficulty: '高', duration: '8 分钟', reward: 90 },
  { id: 'teacher-fee', title: '冒充老师收费二维码', fraudType: '冒充老师', riskLevel: '高风险', difficulty: '低', duration: '4 分钟', reward: 50 },
];
