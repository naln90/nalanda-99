# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-07-22 — 启智杯参赛版本

### Added — 核心功能

- **五维能力测评体系**: 35题题库覆盖18种诈骗类型，支持10题快速测评 + 20题标准测评，输出识诈力/判断力/应对力/证据力/求助力五维能力画像
- **AI个性化任务包**: 根据能力画像弱项自动生成个性化训练任务，含激励文案个性化（3种风格变体）
- **有限状态机情景训练**: 10种诈骗场景类型（冒充客服/刷单返利/虚假投资/杀猪盘/冒充公检法/校园贷/AI换脸/冒充熟人/游戏交易/航班退改签），每场景含多状态转移与分支对话
- **AI对话引擎**: OpenAI兼容API接入，支持流式对话生成；规则引擎降级保障可用性
- **自动复盘+间隔复训**: 训练结束自动生成复盘报告；24h/3d/7d间隔复训触发器，3变体策略防死记硬背
- **紧急止损指引**: 7步紧急止损流程（止损→留存证据→报警→联系银行→冻结账户→修改密码→心理疏导）
- **可疑信息快速判断**: 风险文本分析引擎，输出风险等级/诈骗类型/置信度/关键词
- **反诈知识库**: 28+诈骗类型分类知识库，支持文字搜索 + 图片上传识别（模拟OCR + 关键词分类）
- **宠物成长系统**: 完整宠物养成激励机制，成长值/等级/技能解锁联动训练行为
- **匿名成长榜**: 校园匿名排行榜，按院系/年级维度展示
- **赛事证据中心**: 训练行为数据留存，支持导出为赛事评审材料
- **辅导员看板**: 班级整体能力分布、高风险学生预警、复训完成率统计
- **班会素材生成**: 基于班级数据自动生成班会PPT素材大纲
- **案例库浏览 + 人工审核**: 案例库分类浏览 + 管理员审核入库流程

### Added — 安全与质量保障

- **安全护栏**: 输入脱敏（手机号/身份证号/银行卡号自动遮蔽）+ 输出审查（敏感信息过滤）
- **风险测试样本集**: 220条结构化风险文本样本，覆盖10类诈骗各20条 + 安全负样本20条；三层标签（baseline 88 / challenge 70 / edge_case 62）
- **版本化提示词管理**: `backend/app/prompts/` 目录，JSON格式存储4个提示词模板（dialogue/risk_analysis/task_planning/review），支持版本化加载与热更新
- **图片分析模块**: `backend/app/image_analysis.py`，模拟OCR + 关键词匹配分类

### Added — 基础设施

- **Docker部署**: 多阶段构建（Node + Nginx 前端 / Python 后端），`docker-compose.yml` 一键编排
- **环境变量配置**: `.env.example` 统一管理前端API地址与功能开关
- **Feature Flag**: `VITE_ENABLE_EVIDENCE_CENTER` 控制证据中心页面显隐
- **数据重置脚本**: `backend/reset_demo.py` 一键重置演示数据
- **Alembic迁移**: 数据库版本管理框架

### Added — 前端架构

- **技术栈**: React 19 + TypeScript + Vite 8 + Tailwind CSS 3
- **状态管理**: Zustand 全局状态切片
- **路由**: React Router v7
- **UI组件库**: 自研 shadcn/ui 风格组件（Button/Card/Badge/Tabs/Toast/Progress等）
- **动效组件**: CountUp数字递增 / Confetti撒花 / FloatingParticles粒子 / RadarChart雷达图 / GlowCard发光卡片
- **页面**: 21个功能页面（首页/测评/测评结果/知识库/任务包/情景训练/结算/可疑判断/紧急止损/证据中心/案例库/辅导员看板/班会/管理审核/宠物/排行/登录等）

### Added — 后端架构

- **技术栈**: FastAPI + SQLAlchemy + SQLite + Pydantic
- **58条API路由**: 覆盖测评/训练/知识库/任务包/案例/辅导员/班会/图片分析等
- **模块化设计**: ai_service / rules / scenarios / scenario_state_machine / ability_profile / task_planner / review_engine / retrain_scheduler / safety_filter / risk_test_samples / image_analysis / question_bank / emergency_stop_loss
- **运行基线**: `baseline.md` 记录初始功能基线

### Changed — 持续改进

- 测评题库从32题补至35题，新增奖助学金/求职培训贷/网购退款场景
- AI服务层从硬编码提示词重构为外部JSON模板加载，支持版本管理与热更新
- 知识库页面新增图片上传识别功能（点击/拖拽/粘贴三种交互）
- 首页重构为Bento Grid布局
- 任务包页面压缩为单屏布局
- TypeScript编译0错误，Lint警告从11个降至6个（剩余为shadcn/ui标准模式与动画意图设计）

### Fixed — 关键修复

- 修复测评多选题按单选处理的问题
- 修复任务包完成状态与成长进度条不同步
- 修复情景训练场景类型显示异常
- 修复Store中replyScenarioTraining/completeTaskItem/finishScenarioTraining缺少ownerId
- 修复ScenarioTrainingPage中taskId类型转换问题
- 修复后端main.py关键业务逻辑Bug（会话管理/结算/任务包）
- 修复前端useEffect依赖项导致的无限渲染问题
- 修复未使用变量与导入的lint警告
