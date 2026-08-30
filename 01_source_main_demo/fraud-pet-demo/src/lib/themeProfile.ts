/**
 * 主题画像（需求：非反诈主题绝不与“诈骗”勾连；Python/编程主题使用编程相关的
 * 角色与内容，做到“人物设计”随主题变化）。
 *
 * 把任务包标题/学习目标主题映射为：
 *  - 角色名 / 头像 emoji / 开场白（学习陪伴人物主题化）
 *  - 答题题库（fraud=反诈题库；python=Python 基础题库；generic=中性学习自测）
 *  - 微课提示语
 *
 * 关键约束：非反诈主题下，所有生成内容都不得出现“诈骗/刷单/转账”等反诈措辞。
 */

export type ThemeKey = 'python' | 'generic';

export interface ThemeProfile {
  key: ThemeKey;
  /** 主题短标签（python=Python / generic=清洗后的主题名或“学习”），用于首页文案 */
  themeLabel: string;
  /** 学习陪伴角色名，随主题变化（人物设计主题化） */
  companionName: string;
  /** 角色头像 emoji */
  companionEmoji: string;
  /** 角色开场白 */
  companionIntro: string;
}

export interface QuizQuestion {
  id: string;
  stem: string;
  options: string[];
  correct: number;
  signal: string;
}

const PYTHON_WORDS = ['python', 'py', '编程', '代码', '程序', '脚本', '开发'];

export function isPythonTheme(themeText: string): boolean {
  const t = (themeText || '').toLowerCase();
  return PYTHON_WORDS.some((w) => t.includes(w));
}

/**
 * 从“主题 · N天个性化任务包”或自由文本中清洗出干净的主题名。
 * 例如：“Python编程入门 · 21天个性化任务包” -> “Python编程入门”。
 */
export function cleanTheme(themeText: string): string {
  let t = (themeText || '').trim();
  // 去掉 “ · N天个性化任务包” 这类后端生成的任务包后缀，得到干净主题名。
  // 注意：不能按字符全局剔除“学习/任务”，否则会破坏“机器学习”等组合词。
  t = t.replace(/\s*[·•・]\s*\d+\s*天.*$/, '');
  t = t.replace(/个性化任务包$/, '');
  return t.trim() || '本期主题';
}

export function resolveThemeProfile(themeText: string): ThemeProfile {
  if (isPythonTheme(themeText)) {
    return {
      key: 'python',
      themeLabel: 'Python',
      companionName: '小码灵',
      companionEmoji: '🐍',
      companionIntro: '我是小码灵。可以问我“今天先写什么”、某个语法点，或如何让代码跑通。',
    };
  }
  return {
    key: 'generic',
    themeLabel: cleanTheme(themeText) || '学习',
    companionName: '小知灵',
    companionEmoji: '📚',
    companionIntro: '我是小知灵。可以问我“今天先学什么”、某个知识点，或学习成果怎样打磨。',
  };
}

/** Python 基础题库：仅在 Python/编程主题下使用，与反诈完全无关 */
function getPythonPool(): QuizQuestion[] {
  return [
    {
      id: 'q1',
      stem: '在 Python 中，用来划分代码块（如函数体、循环体）的是？',
      options: ['缩进（空格/制表符）', '一对大括号 {}', '语句末尾的分号 ;', '关键字 end'],
      correct: 0,
      signal: 'Python 用缩进表示代码层级，而不是大括号。',
    },
    {
      id: 'q2',
      stem: '下列哪个可以作为合法的变量名？',
      options: ['1name', 'name_1', 'class', 'for'],
      correct: 1,
      signal: '变量名不能以数字开头，也不能是关键字（class、for 都是关键字）。',
    },
    {
      id: 'q3',
      stem: '执行 list_a = [1, 2, 3] 后，list_a[-1] 的值是？',
      options: ['1', '2', '3', '会报错'],
      correct: 2,
      signal: '负数索引从末尾计数，-1 表示最后一个元素。',
    },
    {
      id: 'q4',
      stem: '向列表末尾追加一个元素，应该使用哪个方法？',
      options: ['append()', 'push()', 'add()', 'insert_back()'],
      correct: 0,
      signal: 'Python 列表用 append() 在末尾添加元素。',
    },
    {
      id: 'q5',
      stem: '表达式 print(type(3)) 的输出更接近？',
      options: ["<class 'int'>", 'int', '3', '<type int>'],
      correct: 0,
      signal: 'type(3) 返回整数类型对象，打印出来是 <class \'int\'>。',
    },
    {
      id: 'q6',
      stem: '关于 Python 字典（dict）的“键”，下列说法正确的是？',
      options: ['键必须唯一且通常为不可变类型', '键可以重复', '键只能是数字', '键只能是字符串'],
      correct: 0,
      signal: '字典的键必须唯一，且一般使用不可变类型（如字符串、数字、元组）。',
    },
    {
      id: 'q7',
      stem: 'range(3) 生成的序列是？',
      options: ['0, 1, 2', '1, 2, 3', '0, 1, 2, 3', '0, 1, 2, 3, 4'],
      correct: 0,
      signal: 'range(n) 从 0 开始，到 n-1 结束。',
    },
    {
      id: 'q8',
      stem: '在 Python 中捕获异常，应该使用哪一组关键字？',
      options: ['try / except', 'if / else', 'for / while', 'switch / case'],
      correct: 0,
      signal: '异常处理使用 try 配合 except 捕获具体错误。',
    },
    {
      id: 'q9',
      stem: '定义一个函数，必须使用的关键字是？',
      options: ['def', 'function', 'func', 'define'],
      correct: 0,
      signal: 'Python 用 def 定义函数。',
    },
    {
      id: 'q10',
      stem: '字符串拼接 "abc" + "123" 的结果是？',
      options: ['"abc123"', '"abc 123"', '会报错', '"abcabc123"'],
      correct: 0,
      signal: 'Python 中相同类型的字符串可以直接用 + 拼接。',
    },
  ];
}

/** 中性学习自测题库：用于非反诈、非编程的其它主题，引用主题但不牵扯诈骗 */
function getGenericPool(theme: string): QuizQuestion[] {
  return [
    {
      id: 'q1',
      stem: `学习「${theme}」时，哪种做法更高效？`,
      options: ['先理解核心概念，再动手练习', '直接背诵结论', '只收藏资料不实践', '跳过基础直接做难题'],
      correct: 0,
      signal: '理解再实践，比单纯记忆或囤资料更扎实。',
    },
    {
      id: 'q2',
      stem: `遇到「${theme}」里的难点，首先应该？`,
      options: ['把问题拆小，逐步定位', '立刻放弃', '等别人给答案', '从头再学一遍'],
      correct: 0,
      signal: '把大问题拆成小步骤，更容易定位卡点。',
    },
    {
      id: 'q3',
      stem: `判断自己是否掌握「${theme}」的某个点，最可靠的是？`,
      options: ['能独立完成任务或讲清楚', '视频看了多久', '笔记写了多少页', '资料收藏了多少'],
      correct: 0,
      signal: '能输出、能讲清楚，才是真正掌握的标志。',
    },
    {
      id: 'q4',
      stem: `制定「${theme}」的复习计划，更合理的是？`,
      options: ['按薄弱点分步推进', '一次性全看完', '只做简单部分', '考前突击'],
      correct: 0,
      signal: '围绕薄弱点分步推进，比临时突击更稳。',
    },
    {
      id: 'q5',
      stem: `在「${theme}」上花时间，怎样收获更大？`,
      options: ['输出成果并复盘', '反复看同一页', '只记关键词', '囤课不学'],
      correct: 0,
      signal: '用“做出来+复盘”形成闭环，比被动输入更有效。',
    },
  ];
}

/** 根据主题画像返回对应题库 */
export function getQuizPool(profile: ThemeProfile, planTitle: string): QuizQuestion[] {
  if (profile.key === 'python') return getPythonPool();
  return getGenericPool(cleanTheme(planTitle));
}

/** 微课提示语：随主题给出相关的中性提示 */
export function getMicroCourseHint(profile: ThemeProfile, planTitle: string): string {
  if (profile.key === 'python') {
    return '小码灵提示：写 Python 时先把需求拆成小函数，遇到报错优先读最后一行错误信息定位问题，再动手改。';
  }
  const theme = cleanTheme(planTitle);
  return `小知灵提示：学习「${theme}」时，先把核心概念拆成可练习的小步骤，理解后再动手，定期用输出成果检验掌握程度。`;
}

/** 首页首屏问候语：随当前主题变化 */
export function getHomeGreeting(profile: ThemeProfile): string {
  switch (profile.key) {
    case 'python':
      return '今天也来写几行代码吧';
    default:
      return profile.themeLabel && profile.themeLabel !== '学习'
        ? `今天也来专注「${profile.themeLabel}」学习吧`
        : '今天也来专注学习吧';
  }
}

/** 首页每日提醒卡片：随当前主题变化 */
export function getDailyTip(profile: ThemeProfile): { label: string; text: string } {
  switch (profile.key) {
    case 'python':
      return {
        label: '每日编程提醒',
        text: '动手前先把需求拆成小函数；遇到报错优先读最后一行错误信息，再动手修改。',
      };
    default:
      return {
        label: `每日${profile.themeLabel}提醒`,
        text: '保持每天固定时段学习，先把目标拆成小步骤再动手，比临时突击更扎实。',
      };
  }
}
