# 诈醒学集

> 大学生 AI 主题学习与成果展示平台 — 启智杯参赛作品

基于 AI 驱动的校园主题学习与素养成长平台，覆盖反诈安全、网络安全、心理健康、求职就业、金融素养等 11 个主题。通过综合能力测评、情景对话训练、多主题知识库、个性化任务包与校园共建活动，帮助学生系统化提升安全与综合素养。

---

## 技术栈

| 层 | 技术 | 版本 |
|---|---|---|
| 前端 | React + TypeScript + Vite | 19 / 5 / 8 |
| 样式 | Tailwind CSS | 3.4 |
| 状态管理 | Zustand | 5.0 |
| 路由 | React Router | v7 |
| 图表 | ECharts + echarts-for-react | 6.1 |
| 后端 | FastAPI + SQLAlchemy | 0.115 / 2.0 |
| 数据库 | SQLite | — |
| AI | OpenAI 兼容 API（含规则引擎降级） | — |

---

## 快速启动

### 方式一：本地开发

**前端**

```bash
npm install
npm run dev
```

**后端**

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

前端默认请求 `http://127.0.0.1:8000/api`。如需修改，复制 `.env.example` 为 `.env` 并设置 `VITE_API_BASE_URL`。

### 方式二：Docker 一键部署

```bash
docker compose up --build
```

- 前端：`http://localhost`
- 后端 API：`http://localhost:8000/api`
- 数据库持久化：Docker volume `db-data`

---

## 功能模块

### 核心训练流程

```
登录 → 五维能力测评 → 领取宠物 → AI任务包推荐 → 情景对话训练
  → 自动复盘 → 宠物成长 → 间隔复训 → 匿名排行
```

| 模块 | 说明 |
|---|---|
| **综合能力测评** | 多主题题库，基于已参与主题输出辨识力/判断力/应变力/实证力/协作力五维雷达图 |
| **AI 任务包** | 根据弱项自动生成个性化学习计划，支持 7 天/14 天周期 |
| **情景对话训练** | 多种主题场景 FSM 状态机，AI 实时对话，支持分支与多轮交互 |
| **自动复盘** | 训练结束自动生成可解释复盘报告，标注关键决策点 |
| **间隔复训** | 24h/3d/7d 自动触发，多变体策略防止死记硬背 |
| **紧急止损** | 7 步止损流程指引（止损→留存证据→报警→银行→冻结→改密→疏导） |
| **可疑信息判断** | 风险文本分析，输出风险等级、证据标签与处置建议 |
| **多主题知识库** | 11 个主题、60+ 条知识，每条标注权威来源与可溯源外链 |
| **宠物成长** | 成长值/等级/技能解锁，联动学习行为 |
| **学习排行** | 按能力的成长值排行 |

### 管理端

| 模块 | 说明 |
|---|---|
| **辅导员看板** | 班级能力分布、高风险预警、复训完成率 |
| **班会素材** | 基于班级数据自动生成班会大纲 |
| **案例库** | 分类浏览 + 人工审核入库 |
| **赛事证据中心** | 训练行为数据留存与导出 |

### 安全保障

- **输入脱敏**：手机号/身份证号/银行卡号自动遮蔽
- **输出审查**：敏感信息过滤
- **风险测试集**：220条结构化样本（10类诈骗×20条 + 安全负样本20条）

---

## 项目结构

```
fraud-pet-demo/
├── src/                          # 前端源码
│   ├── pages/                    # 21个功能页面
│   ├── components/               # UI组件 + 动效组件
│   ├── store/                    # Zustand状态管理
│   ├── api/                      # API客户端
│   ├── types/                    # TypeScript类型定义
│   └── data/                     # 前端mock数据
├── backend/                      # 后端源码
│   ├── app/
│   │   ├── main.py               # FastAPI入口 (58条路由)
│   │   ├── models.py             # SQLAlchemy数据模型
│   │   ├── ai_service.py         # AI服务层 (OpenAI兼容 + 规则降级)
│   │   ├── rules.py               # 规则引擎
│   │   ├── scenarios.py           # 10种诈骗场景定义
│   │   ├── scenario_state_machine.py  # FSM状态机
│   │   ├── ability_profile.py    # 五维能力画像计算
│   │   ├── task_planner.py       # 个性化任务包生成
│   │   ├── review_engine.py      # 自动复盘引擎
│   │   ├── retrain_scheduler.py  # 间隔复训调度
│   │   ├── safety_filter.py      # 安全护栏 (输入脱敏+输出审查)
│   │   ├── question_bank.py      # 35题测评题库
│   │   ├── risk_test_samples.py  # 220条风险测试样本
│   │   ├── image_analysis.py     # 图片分析模块
│   │   ├── emergency_stop_loss.py # 紧急止损流程
│   │   ├── prompts/              # 版本化提示词 (JSON格式)
│   │   │   ├── __init__.py       # 提示词加载器
│   │   │   ├── dialogue_v1.json
│   │   │   ├── risk_analysis_v1.json
│   │   │   ├── task_planning_v1.json
│   │   │   └── review_v1.json
│   │   └── seed.py               # 数据初始化
│   ├── requirements.txt
│   └── Dockerfile
├── Dockerfile                    # 前端Dockerfile (Node+Nginx)
├── docker-compose.yml            # Docker编排
├── nginx.conf                    # Nginx配置
├── .env.example                  # 环境变量模板
├── baseline.md                   # 运行基线文档
└── CHANGELOG.md                  # 变更日志
```

---

## 测试

```bash
# 前端单元测试
npm test

# 前端构建检查
npm run build

# Lint检查
npm run lint

# 后端测试
python -m pytest backend/tests -q
```

---

## 账号说明

- 生产环境：使用真实账号/密码登录或校园统一认证登录；演示入口不展示。
- 本地调试：以开发模式（`vite` dev / 未打包）启动前端，且访问地址携带 `?demo=1`（如 `/login?demo=1`）时，登录页才会显示「体验账号一键进入」调试入口，需配合本地 `.env` 中的 `VITE_DEMO_OWNER_ID`。生产构建（`vite build`）默认不含该入口。生产部署请通过 `AUTH_REQUIRED=true` 关闭后端 `/demo-login`，强制真实账号或校园认证登录。

---

## API 概览

后端共 58 条 API 路由，主要分组：

| 前缀 | 说明 |
|---|---|
| `/api/auth` | 登录/注册/会话管理 |
| `/api/pets` | 宠物选择/成长/技能 |
| `/api/assessment` | 测评会话/提交/结果/能力画像 |
| `/api/task-package` | 任务包生成/列表/完成 |
| `/api/training` | 训练题目/提交结算 |
| `/api/scenario-training` | 情景对话训练(FSM) |
| `/api/knowledge` | 知识库/分类/图片识别 |
| `/api/suspicious-check` | 可疑信息分析 |
| `/api/emergency-stop-loss` | 紧急止损流程 |
| `/api/counselor` | 辅导员看板/班会素材 |
| `/api/cases` | 案例库浏览/审核 |
| `/api/ranking` | 匿名排行榜 |
| `/api/retrain` | 间隔复训任务 |
| `/api/risk-test` | 风险测试样本查询 |
| `/api/health` | 健康检查 |

---

## 合规边界

系统仅用于校园反诈教育训练和风险提示，不替代公安机关、金融机构或学校管理部门判断。不展示真实姓名、手机号、学号、身份证号和负面评价标签。

---

## License

MIT
