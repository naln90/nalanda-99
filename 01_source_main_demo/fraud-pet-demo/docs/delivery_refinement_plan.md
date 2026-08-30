# 诈醒学集交付落地细化修正方案

> 针对导师反馈："不要带着演示、模拟的想法去做；要带着交付、落地目的，让使用对象下载客户端或打开网页输入账号密码就能直接使用；后续能联网、不增加门槛；UI 持续完善为简洁清晰商业风。"

---

## 一、导师要求拆解为可验收标准

| 导师原话 | 核心指标 | 当前状态 | 目标状态 |
|---|---|---|---|
| 不要演示、模拟 | 系统打开后无 "演示入口""一键体验""Demo" 字样 | 登录页开发环境仍显示演示入口；生产环境已隐藏 | **生产环境完全去 Demo 化**；本地开发也弱化 Demo 入口 |
| 交付、落地、真实使用逻辑 | 登录 → 使用 → 退出，路径符合真实产品预期 | 账号密码/校园账号/注册已通 | 默认账号密码登录；演示入口需要显式申请/配置 |
| 客户端/App/网页端，输入账号密码即用 | 支持 Web 生产部署；后续可扩展为 App/PWA | 仅 Web 前端 | Web 端已可部署；补齐 PWA 离线能力 |
| 能联网、不局限本地 | 部署到公网/校园服务器，数据云端持久化 | 本地 SQLite + localhost | 生产 PostgreSQL + 域名/HTTPS |
| 不增加使用门槛 | 任何人打开网页即可注册/登录，无需预先配置 | 需要 `VITE_DEMO_MODE`、演示账号等知识 | 用户零配置，打开即用 |
| UI 简洁、明了、清晰 | 去除装饰、统一设计系统、信息密度适中 | 已扁平化登录页；仍有玻璃拟态、多处图标堆叠 | 建立 Design System，全站统一 |

---

## 二、当前已具备的交付能力（优势清单）

> 用于回应导师"不能只有前端"：项目已具备真实后端 + 数据库 + 部署能力，只是默认走演示态。

1. **完整后端服务体系**
   - FastAPI + SQLAlchemy + SQLite/PostgreSQL
   - 53 张数据表、115 个 API、58 个 Pydantic Schema
   - 已生成的架构说明：`docs/backend_database_architecture.md`

2. **真实账号体系已就绪**
   - `backend/app/models.py`：`Account` 表含 `username`、`password_hash`、`owner_id`、`role`
   - `LoginPage.tsx` 已实现 login / register / campus 三种真实登录模式
   - `loginWithCredentials`、`register` 已接入后端真实接口

3. **生产部署钩子已预埋**
   - `docker-compose.yml`：PostgreSQL + 后端 + 前端 Nginx 多阶段构建
   - `nginx.conf`：反向代理、gzip、安全响应头、HTTPS 注释模板
   - `.env.example`：已预留 `DATABASE_URL`、`APP_SECRET`、`OPENAI_API_KEY`、`AUTH_REQUIRED`

4. **演示入口已有门控**
   - 前端：`import.meta.env.DEV` 控制，生产 `vite build` 自动隐藏
   - 后端：`AUTH_REQUIRED=true` 时 `/api/auth/demo-login`、`/api/school/demo-login` 返回 403
   - 已写入 `MEMORY.md` 作为长期约定

---

## 三、仍存在的"演示/模拟"痕迹（必须清理项）

### P0：赛前必须清理

| # | 问题 | 位置 | 影响 | 清理动作 |
|---|---|---|---|---|
| 1 | 登录页仍有"演示账号一键进入"按钮 | `src/pages/LoginPage.tsx:100-108, 346-380` | 生产环境虽隐藏，但开发截图/视频仍显 Demo 感 | 将演示入口从登录页移除，改为仅在 URL 参数 `?demo=1` 或本地 `.env` 显式开启时通过独立入口进入 |
| 2 | 演示登录文案「已进入演示模式」 | `LoginPage.tsx:105` | 强化 Demo 心智 | 改为「已登录」或直接跳转，不提示「演示」 |
| 3 | 演示账号 `U-2408**` 硬编码在前端 | `LoginPage.tsx:102` | 看起来像模拟账号 | 改为可配置环境变量，且仅开发环境可用 |
| 4 | `README.md` / `index.html` 可能仍含"演示"字样 | 待检查 | 给评委留下 Demo 印象 | 全局搜索 "演示""Demo""demo"，删除或替换为产品化描述 |
| 5 | 能力画像/知识库/校园活动数据为预置种子数据 | 数据库种子脚本 | 评委质疑"是否真实" | 增加"首次使用引导"，说明系统预置学习素材；用户操作后产生真实个人数据 |
| 6 | AI 训练模块默认走规则引擎降级 | `.env` 未配置 LLM 时 | 回答看起来机械/模拟 | 接入真实 LLM（最低成本国产模型），或移除 LLM 入口直到配置完成 |

### P1：赛后持续优化

| # | 问题 | 位置 | 改进方向 |
|---|---|---|---|
| 7 | 无每日使用闭环 | 首页缺少任务/提醒 | 增加"今日学习"任务卡片 + 连续打卡 |
| 8 | 校方活动发布后学生端参与链路未完全闭合 | `SchoolActivityPage` / `activities` 路由 | 发布 → 学生报名/签到 → 公示参与名单 |
| 9 | 学习集市 UGC 缺少审核 | `AdminAuditPage` | 先发后审改为先审后发 |
| 10 | 无 PWA/离线能力 | 缺少 manifest | 添加 PWA，可安装到手机桌面 |

---

## 四、分阶段可执行方案

### 阶段 1：去演示化与真实登录（赛前 1–2 天，P0）

**目标**：让系统打开就是真实产品，而非 Demo。

#### 任务 1.1 移除登录页演示入口（默认隐藏）

- **文件**：`src/pages/LoginPage.tsx`
- **改动**：
  - 删除 `showDemo = import.meta.env.DEV`
  - 删除"演示账号一键进入"和"校方发布端入口"两个按钮
  - 保留真实登录（账号密码 / 注册 / 校园账号）三种模式
  - 演示入口改为通过 URL 参数 `?demo=1` 显式开启，且仅在 `import.meta.env.DEV` 下生效
- **代码示例**：
  ```ts
  const searchParams = new URLSearchParams(window.location.search);
  const demoEnabled = import.meta.env.DEV && searchParams.get('demo') === '1';
  ```
- **验收标准**：
  - 开发环境默认访问 `/login` 不显示演示入口
  - `/login?demo=1` 才显示演示入口
  - 生产构建产物中无演示入口相关 DOM

#### 任务 1.2 演示账号不再硬编码

- **文件**：`src/pages/LoginPage.tsx`、`src/store/useAppStore.ts`
- **改动**：
  - `handleDemoLogin` 改为读取环境变量 `import.meta.env.VITE_DEMO_OWNER_ID`
  - 默认值仅在开发环境提供，生产环境为空
- **代码示例**：
  ```ts
  const demoOwnerId = import.meta.env.VITE_DEMO_OWNER_ID || '';
  const handleDemoLogin = async () => {
    if (!demoOwnerId) return;
    await login(demoOwnerId);
  };
  ```
- **验收标准**：
  - `.env.example` 新增 `VITE_DEMO_OWNER_ID=U-2408**`
  - 生产环境未配置时，演示入口即使被强制打开也无法登录

#### 任务 1.3 后端演示登录强制门控

- **文件**：`backend/app/routers/auth.py`、`backend/app/v3_routes.py`
- **改动**：
  - 确认 `AUTH_REQUIRED=true` 时 `/api/auth/demo-login`、`/api/school/demo-login` 返回 403
  - 已在 `MEMORY.md` 中约定，此处补一个显式测试用例
- **验收标准**：
  - 运行 `pytest backend/tests` 时，演示登录在 `AUTH_REQUIRED=true` 下返回 403

#### 任务 1.4 全局去 Demo 文案

- **文件**：`README.md`、`index.html`、`src/pages/*` 等
- **改动**：
  - 全局搜索 `"演示"`、`"Demo"`、`"demo模式"`、`"一键进入"`
  - 替换为：「欢迎使用」「登录」「进入系统」等中性文案
  - 保留"启智杯参赛作品"可在 about/foot 中说明，但不放在核心流程
- **验收标准**：
  - 登录页、首页、能力画像、知识库等主要页面无"演示"字样
  - README 标题为产品名，不强调 Demo

---

### 阶段 2：UI 商业简洁化（赛前 2–3 天，P0）

**目标**：像成熟校园 App（学习通、钉钉教育版）一样简洁、清晰、易用。

#### 任务 2.1 建立最小设计系统

- **文件**：`tailwind.config.js` 或新增 `src/styles/design-system.ts`
- **内容**：
  - 主色：保留 `indigo-600` 作为品牌色
  - 语义色：成功绿、警告黄、错误红、信息蓝
  - 圆角：卡片 `rounded-2xl`，按钮 `rounded-xl`，输入框 `rounded-xl`
  - 间距：以 4/8/12/16/24/32 为基准
  - 阴影：仅保留 `shadow-sm`，删除大面积 glow/玻璃拟态
- **验收标准**：
  - 全站组件颜色来自设计系统，无一次性硬编码色值

#### 任务 2.2 移除剩余装饰元素

- **文件**：`src/pages/HomePage.tsx`、`src/components/ui/*`
- **改动**：
  - 删除径向渐变、粒子动画、网格背景、发光阴影、emoji
  - 删除"玻璃拟态"（`glass`、`glass-dark`）类的使用，改为实色面
  - 图标使用 Lucide，不使用 emoji
- **验收标准**：
  - 视觉检查：页面无炫光、无动画背景、无 emoji

#### 任务 2.3 首页降密度

- **文件**：`src/pages/HomePage.tsx`
- **改动**：
  - 一屏内最多 2 个视觉焦点：能力画像 + 今日任务/知识库入口
  - 快捷入口（我的宠物/成长榜等）收到二级页或底部导航
  - 增加留白，使用 `gap-6` / `p-6` 以上间距
- **验收标准**：
  - 首页首屏无 8+ 图标堆叠
  - 用户进入 3 秒内能识别"今天该做什么"

#### 任务 2.4 统一表单与按钮

- **文件**：`src/components/ui/Button.tsx`、`src/components/ui/Input.tsx`
- **改动**：
  - 统一按钮高度：`h-11`（主要）、`h-9`（次要）
  - 统一输入框高度：`h-11`
  - 统一错误提示样式：红色背景 + 图标
- **验收标准**：
  - 所有表单页面按钮/输入框尺寸一致

---

### 阶段 3：联网部署与数据持久化（赛前 1–2 天，P0）

**目标**：评委打开的是一个真实网址，不是 `localhost`。

#### 任务 3.1 完成生产环境配置模板

- **文件**：`.env.example`、`docker-compose.yml`
- **改动**：
  - `.env.example` 提供完整生产配置：
    ```env
    DATABASE_URL=postgresql+psycopg2://fraud_pet:ChangeMeInProduction@postgres:5432/fraud_pet
    AUTH_REQUIRED=true
    APP_SECRET=<64位随机字符串>
    VITE_API_BASE_URL=https://your-domain.com/api
    OPENAI_API_KEY=sk-...
    OPENAI_BASE_URL=https://api.openai.com/v1
    OPENAI_MODEL=gpt-4o-mini
    ```
  - `docker-compose.yml` 已具备，补充说明：
    - 如何生成 `APP_SECRET`
    - 如何配置 HTTPS（Cloudflare / Let's Encrypt）

#### 任务 3.2 部署操作手册

- **文件**：新增 `docs/deployment_guide.md`
- **内容**：
  - 购买云服务器（阿里云/腾讯云/华为云学生机）
  - 安装 Docker + Docker Compose
  - 克隆代码、配置 `.env`、运行 `docker compose up --build -d`
  - 配置 Nginx / HTTPS
  - 初始化数据库（首次运行 `alembic upgrade head` + 种子数据）
  - 验证：`https://your-domain.com` 可注册、登录、使用
- **验收标准**：
  - 按手册能在新服务器 30 分钟内完成部署

#### 任务 3.3 数据持久化与备份

- **文件**：`docker-compose.yml`
- **改动**：
  - PostgreSQL 使用命名卷 `postgres-data`
  - 增加每日自动备份脚本（可选，可后续实现）
- **验收标准**：
  - 容器重启后数据不丢失

---

### 阶段 4：降低使用门槛（赛前 1 天，P0）

**目标**：任何人打开网页就能用，无需预先知道演示账号。

#### 任务 4.1 默认模式为登录，注册流程简化

- **文件**：`src/pages/LoginPage.tsx`
- **改动**：
  - 默认 `mode='login'`（已满足）
  - 注册时只需账号 + 密码 + 确认密码，昵称可选
  - 校园账号模式说明"用于学校统一认证"
- **验收标准**：
  - 新用户 30 秒内完成注册并进入首页

#### 任务 4.2 首次使用引导

- **文件**：新增 `src/components/onboarding/FirstTimeGuide.tsx`
- **改动**：
  - 新用户首次登录后，弹出 3 步引导：
    1. "这是你的能力画像，完成测评可解锁"
    2. "知识库涵盖 11 个主题，点击即可学习"
    3. "每日训练帮助你持续成长"
  - 引导可跳过
- **验收标准**：
  - 新用户不迷茫，知道第一步该做什么

#### 任务 4.3 游客模式（可选）

- **改动**：
  - 允许不登录浏览知识库首页
  - 测评、训练、宠物成长等需要登录后使用
- **验收标准**：
  - 用户未注册也能看到产品价值

---

### 阶段 5：真实 AI 与每日使用闭环（赛后 1–2 周，P1）

**目标**：用户愿意每天打开 5 分钟。

#### 任务 5.1 接入真实 LLM

- **文件**：`.env`、`backend/app/services/llm_client.py`（如存在）
- **改动**：
  - 配置国产低成本模型：
    - 通义千问 `qwen-turbo`
    - DeepSeek `deepseek-chat`
    - 智谱 `glm-4-flash`
  - 未配置 LLM 时，AI 训练入口显示"暂未开放"而非返回机械回答
- **验收标准**：
  - 情景对话回答自然、有教育意义

#### 任务 5.2 每日一练 + 打卡

- **文件**：`src/pages/HomePage.tsx`、`backend/app/models.py`
- **改动**：
  - 首页"今日任务"卡片
  - 连续打卡天数显示
  - 完成后奖励盾能/宠物成长值
- **验收标准**：
  - 用户每天有明确目标

#### 任务 5.3 校方活动闭环

- **文件**：`src/pages/SchoolActivityPage.tsx`、`src/pages/ActivitiesPage.tsx`
- **改动**：
  - 校方发布活动 → 学生端可见
  - 学生"报名"→"签到"→"获得盾能"
  - 活动结束后导出参与名单
- **验收标准**：
  - 活动从发布到参与全链路可跑通

#### 任务 5.4 内容审核

- **文件**：`src/pages/AdminAuditPage.tsx`
- **改动**：
  - 学习集市发布内容先审后发
  - 管理员可一键通过/拒绝
- **验收标准**：
  - 无未经审核的 UGC 上线

---

### 阶段 6：客户端扩展（赛后，P2）

#### 任务 6.1 PWA

- **文件**：新增 `public/manifest.json`、`src/service-worker.ts`
- **改动**：
  - 添加 manifest：名称、图标、主题色、启动方式
  - 注册 Service Worker，缓存静态资源
  - 离线可查看知识库
- **验收标准**：
  - Chrome 提示"安装到桌面"
  - 离线可访问知识库

#### 任务 6.2 微信小程序 / Flutter（视反馈）

- 微信小程序：用 Taro/Uni-app 复用业务逻辑
- Flutter：成本较高，建议赛后视用户反馈再决定

---

## 五、赛前最低完成清单（启智杯截止前必须）

- [ ] 登录页默认不显示演示入口（开发环境通过 `?demo=1` 开启）
- [ ] 演示账号从代码中移除，改为环境变量配置
- [ ] `README.md`、`index.html`、核心页面无"演示""Demo"字样
- [ ] 后端 `AUTH_REQUIRED=true` 时拒绝演示登录，并有单元测试
- [ ] 登录页 UI 扁平、简洁、无装饰动画
- [ ] 首页信息密度降低，首屏焦点为能力画像 + 今日任务/知识库
- [ ] 全站建立最小设计系统（颜色、圆角、间距、阴影）
- [ ] 部署到云服务器，可通过域名/HTTPS 访问
- [ ] 生产环境使用 PostgreSQL，数据持久化
- [ ] `.env.example` 提供完整生产配置模板
- [ ] 准备 2 个真实测试账号（学生 + 校方），现场演示真实注册/登录
- [ ] 演示视频/答辩不再说"这是演示账号"，改为"这是已部署的真实系统"

---

## 六、对答辩演示的直接影响

### 演示话术调整

| 旧话术 | 新话术 |
|---|---|
| "这是我们的演示账号，一键进入" | "这是已部署在云端的真实系统，我用普通学生账号登录" |
| "数据是本地模拟的" | "数据保存在 PostgreSQL 数据库，支持多用户真实使用" |
| "这里是 Demo 界面" | "这是产品的主界面" |
| "后续可以接入真实 AI" | "系统已预留 LLM 配置，可接入真实模型" |

### 演示流程建议

1. 打开公网地址（如 `https://zhaxingxueji.example.com`）
2. 现场注册一个新账号（展示真实注册）
3. 登录后完成一次测评（产生真实数据）
4. 展示能力画像和知识库来源
5. 校方端发布一个活动（展示真实数据流动）
6. 学生端看到活动并参与

---

## 七、下一步建议执行顺序

建议按以下顺序落地，风险最低、观感提升最快：

1. **先做登录页去演示化**（影响最大，评委第一眼看到）
2. **再做 UI 简洁化收尾**（设计系统 + 首页降密度）
3. **同步准备云部署**（PostgreSQL + docker-compose + HTTPS）
4. **赛前接入真实 LLM**（最低成本国产模型即可）
5. **赛后补每日闭环 + PWA**

---

## 八、附录：关键文件与命令速查

### 关键文件

| 用途 | 文件 |
|---|---|
| 后端架构说明 | `docs/backend_database_architecture.md` |
| 登录页 | `src/pages/LoginPage.tsx` |
| 全局状态 | `src/store/useAppStore.ts` |
| 后端认证 | `backend/app/routers/auth.py` |
| 校方演示登录 | `backend/app/v3_routes.py` |
| 部署编排 | `docker-compose.yml` |
| 反向代理 | `nginx.conf` |
| 环境变量模板 | `.env.example` |

### 启动命令（本地开发）

```bash
# 后端
DATABASE_URL=sqlite:///./data/demo_corrected.sqlite3 \
  C:/Users/33719/.workbuddy/binaries/python/envs/fraud_demo/Scripts/uvicorn.exe \
  app.main:app --port 8011 --host 0.0.0.0

# 前端
cd fraud-pet-demo
unset CODEBUDDY_SESSION_ID
C:/Users/33719/.workbuddy/binaries/node/versions/22.22.2/node.exe \
  ./node_modules/vite/bin/vite.js --config vite.demo.config.ts
```

### 生产部署命令

```bash
# 服务器端
cp .env.example .env
# 编辑 .env：设置 DATABASE_URL、APP_SECRET、OPENAI_API_KEY、VITE_API_BASE_URL
docker compose up --build -d
# 首次初始化数据库
docker exec fraud-pet-backend alembic upgrade head
```

---

*文档生成时间：2026-08-26*  
*版本：v1.0（基于当前代码现状与导师反馈）*
