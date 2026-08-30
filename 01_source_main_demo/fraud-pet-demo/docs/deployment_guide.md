# 诈醒学集 — 生产部署操作手册

> 目标：把项目部署到一个真实公网地址，让评委/用户「打开网页、输入账号密码就能用」，数据保存在云端 PostgreSQL，重启不丢失。

---

## 一、部署架构

```
[浏览器] ──HTTPS/HTTP──> [Nginx :80] ── /api/ ──> [Backend :8000] ──> [PostgreSQL :5432]
                         (静态 dist)        (FastAPI)            (数据卷 postgres-data)
```

整套服务由 `docker-compose.yml` 编排，包含三个容器：

| 服务 | 镜像 | 作用 |
|---|---|---|
| `postgres` | postgres:15-alpine | 生产数据库，数据持久化于命名卷 `postgres-data` |
| `backend` | 本地构建（python:3.13-slim） | FastAPI + Uvicorn，监听 8000 |
| `frontend` | 本地构建（node:22-alpine → nginx:alpine） | 托管前端 `dist`，反代 `/api` 到后端 |

生产构建由根目录 `Dockerfile`（多阶段：Node 构建 → Nginx 部署）与 `backend/Dockerfile` 完成。

---

## 二、服务器准备

### 2.1 最低配置建议（学生机即可）
- 云服务器：2 vCPU / 2 GB 内存 / 40 GB 磁盘（阿里云、腾讯云、华为云轻量应用服务器均可）
- 系统：Ubuntu 22.04 LTS
- 已备案域名（如需 HTTPS；纯内网演示可跳过域名）

### 2.2 安装 Docker 与 Docker Compose
```bash
# Ubuntu
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker
docker --version        # 确认 >= 24
docker compose version  # 确认插件可用
```

---

## 三、配置环境变量

项目根目录已提供 `.env.example`，复制并按需填写：

```bash
cd fraud-pet-demo
cp .env.example .env
```

必须修改的项（其余保持默认即可）：

| 变量 | 说明 | 示例 |
|---|---|---|
| `POSTGRES_PASSWORD` | 数据库密码，**必须改强密码** | `E7kP9$qL2mZx` |
| `APP_SECRET` | 会话/JWT 签名密钥，≥32 位随机串 | 见下方生成命令 |
| `VITE_API_BASE_URL` | 前后端同域用 `/api`；跨域填 `https://your-domain.com/api` | `/api` |
| `VITE_DEMO_OWNER_ID` | **生产务必留空**，避免暴露演示账号 | `` （空） |
| `OPENAI_API_KEY` 等 | 接入真实 AI 时填；留空则 AI 走规则引擎降级 | 可选 |

生成 `APP_SECRET`：
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

> 提示：`.env` 含密钥，已在 `.gitignore` 忽略（`.env` 匹配 `*.env`），请勿提交到代码仓库。

---

## 四、启动服务

```bash
# 在含 .env 的项目根目录执行
docker compose up --build -d
```

- `--build`：首次或代码更新时重新构建镜像
- `-d`：后台运行

启动后等待约 30–60 秒（Postgres 健康检查通过、后端依赖就绪）。

---

## 五、初始化数据库（首次运行）

`docker-compose.yml` 不会自动跑迁移。首次部署需手动初始化表结构（及可选种子数据）：

```bash
# 进入后端容器执行迁移
docker exec fraud-pet-backend alembic upgrade head
```

如需填充「多主题知识库 / 任务包模板」等初始素材（让首页知识库与 AI 任务包非空），可运行后端种子脚本（如存在）：
```bash
docker exec fraud-pet-backend python seed_data.py
```
> 种子数据用于预置学习素材；用户注册后会在此基础上产生真实个人数据。这回答了「数据是否真实」——系统本身真实，预置素材仅为内容底座。

---

## 六、配置 HTTPS（推荐）

默认 `nginx.conf` 监听 80 并带安全响应头。上线公网建议启用 HTTPS：

1. 在域名解析后台将 `your-domain.com` A 记录指向服务器公网 IP。
2. 用 certbot 申请证书：
   ```bash
   sudo apt install -y certbot
   sudo certbot certonly --webroot -w /var/www/letsencrypt -d your-domain.com
   ```
   或直接使用 Cloudflare 的免费 SSL（代理模式自动签发）。
3. 将证书挂载进前端容器 `/etc/nginx/certs/`（修改 `docker-compose.yml` 增加卷映射），取消 `nginx.conf` 末尾 `server{ listen 443 ssl ... }` 注释块，并把 80 端口 server 改为 301 跳转 HTTPS。
4. 重启：`docker compose restart frontend`

---

## 七、验证部署

```bash
# 以下均假设已绑定域名；本地测试可临时改用服务器 IP
curl -s -o /dev/null -w "首页:%{http_code}\n"        https://your-domain.com/
curl -s -o /dev/null -w "API:%{http_code}\n"         https://your-domain.com/api/health
curl -s -o /dev/null -w "活动列表:%{http_code}\n"    https://your-domain.com/api/activities
```

期望：`首页:200`、`API:200`、`活动列表:200`。

浏览器打开 `https://your-domain.com/`：
1. 点击「注册」，用新账号完成注册 → 看到首页（此时为真实数据）。
2. 完成一次测评，能力画像产生真实记录。
3. 切换校方端 `/school/theme` 发布一个活动，学生端可见并参与。

---

## 八、准备演示用真实账号（赛前）

不要再用演示账号。现场用真实注册流程：
- 学生账号：网站注册页创建，账号 + 密码即可。
- 校方账号：后端 `schoolLogin` 流程创建（`/school/theme`）。

演示话术从「这是演示账号」改为「这是已部署在云端的真实系统，我用普通学生账号登录」。

---

## 九、备份与更新

### 数据备份（PostgreSQL 命名卷）
```bash
docker exec fraud-pet-postgres pg_dump -U fraud_pet fraud_pet > backup_$(date +%Y%m%d).sql
```

### 代码更新
```bash
git pull
docker compose up --build -d      # 重建镜像，数据卷不受影响
docker exec fraud-pet-backend alembic upgrade head  # 如有迁移新增
```

### 容器重启数据不丢失
`postgres-data` 为命名卷（`docker-compose.yml` 已声明），容器重建后数据库保留。

---

## 十、本地开发 vs 生产差异对照

| 维度 | 本地演示（当前沙箱） | 生产部署 |
|---|---|---|
| 前端 | `vite.demo.config.ts` → 5181，`?demo=1` 才可体验 | `docker` 构建静态站 → Nginx :80 |
| 后端 | 8011，SQLite `demo_corrected.sqlite3` | 8000，PostgreSQL |
| 登录 | 允许 `demo-login`（开发态） | `AUTH_REQUIRED=true`，拒绝 demo 登录 |
| 数据库 | 本地文件，易重置 | 云端持久化，需备份 |

---

*文档配套：`docs/backend_database_architecture.md`（后端/数据库架构）、`README.md`（本地运行说明）。*
