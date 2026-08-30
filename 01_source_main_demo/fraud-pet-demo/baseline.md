# 基线报告 — 2026-07-22

## 0. 项目信息

| 项目 | 值 |
|------|-----|
| 项目名称 | 防诈智研 |
| 版本 | V1.0（开发执行版） |
| 技术栈 | React 19, Vite 8, TypeScript 6, React Router, Zustand, Tailwind CSS, ECharts; FastAPI, SQLAlchemy 2, Pydantic 2, SQLite |
| main.py 行数 | 1771 行 |
| 后端路由 | 46 条 |

## 1. 后端测试基线

```
platform win32 -- Python 3.11.9, pytest-9.1.1
4 tests: 4 passed ✅ (已全部通过)
```

| 测试 | 状态 | 备注 |
|------|------|------|
| test_demo_login_assessment_and_pet_claim_flow | ✅ PASS | accuracy 修正为 1.0（D 是 assess-q1 的正确答案） |
| test_training_submission_awards_growth_then_blocks_duplicate_task | ✅ PASS | |
| test_risk_analyze_scores_high_risk_and_awards_small_growth | ✅ PASS | |
| test_ranking_is_sorted_and_privacy_safe | ✅ PASS | |

## 2. 前端测试基线

```
vitest v4.1.9 — 1 test file: src/api/client.test.ts (1 test passed)
```

## 3. 前端 lint 基线

```
oxlint — 2 warnings:
1. src/pages/HomePage.tsx:4 — 'AlertTriangle' imported but never used
2. src/pages/SettlementPage.tsx:22 — useEffect deps 'answers' changes every render
```

## 4. 前端 TypeScript 编译基线

```
tsc -b: 0 errors ✅ (已全部修复)
npm run build: ✅ passes (日期: 2026-07-22)
```

## 5. 后端语法验证

```
Python ast.parse(main.py): OK
create_app() loaded: OK — 46 routes registered
```

## 6. 现有数据表

| 表名 | 用途 |
|------|------|
| accounts | 用户账号 |
| users | 用户状态 |
| pets | 守护宠 |
| pet_pool | 宠物类型池 |
| growth_rules | 成长规则 |
| training_tasks | 训练任务 |
| training_questions | 训练题目 |
| training_records | 训练记录 |
| suspicious_checks | 可疑文字分析 |
| fraud_cases | 诈骗案例 |
| knowledge_items | 反诈知识库 |
| assessment_results | 测评结果（五维画像） |
| task_packages | AI任务包 |
| task_package_items | 任务包条目 |
| scenario_training_sessions | 情景训练会话 |
| retrain_tasks | 错题复训 |
| ai_call_logs | AI调用日志 |

## 7. 按方案需新增但当前缺失的内容

| 类别 | 缺失项 |
|------|--------|
| 配置 | .env.example (前后端) |
| 数据库 | Alembic迁移框架; assessment_sessions/assessment_answers/question_metadata/ability_snapshots/ability_events 等新表 |
| 后端结构 | api/v1/ router分离; services/目录; schemas/目录; rules/拆分; ai/目录 |
| 前端结构 | store拆分(useLearningStore/useScenarioStore); features/目录; api拆分 |
| 测试 | 按领域测试文件; 场景路径测试; 风险测试集 |
| 部署 | Dockerfile; docker-compose; 一键脚本 |
| 文档 | CHANGELOG; docs/architecture; docs/api; docs/prompts; docs/testing |

## 8. 方案明确暂缓的功能（当前存在但需隐藏/不继续开发）

| 功能 | 处理 |
|------|------|
| CounselorDashboardPage | 方案§1.3暂缓"复杂管理端"；路由保留但导航隐藏 |
| ClassMeetingPage | 同上 |
| CaseLibraryPage | 同上 |
| AdminAuditPage | 同上 |
| RankingPage | 方案§1.2"导航隐藏"，路由保留 |

## 9. 基线结论

- 核心功能（登录、测评、训练、宠物、知识库、风险分析）可用
- ✅ 12个TS编译错误已全部修复，构建正常
- 1个后端测试失败（seed数据变化导致accuracy值不匹配）
- ✅ 已创建 backend/.env.example 和 frontend/.env.example
- ✅ 已创建 backend/scripts/reset_demo.py（演示数据重置脚本）
- ✅ 已添加 Feature Flag：VITE_ENABLE_EVIDENCE_CENTER
- ✅ 导航已隐藏暂缓功能（案例库、辅导员看板、人工审核、成长榜）
- 需进入阶段1核心闭环开发

## 10. 阶段0完成记录

| 任务 | 状态 | 说明 |
|------|------|------|
| 阶段0.1: 运行基线并生成 baseline.md | ✅ 完成 | 基线报告已更新 |
| 阶段0.2: 新增 .env.example 与统一配置 | ✅ 完成 | 后端和前端各一份 |
| 阶段0.3: 数据备份与 reset_demo 脚本 | ✅ 完成 | backend/scripts/reset_demo.py |
| 阶段0.4: Feature Flag 控制 | ✅ 完成 | VITE_ENABLE_EVIDENCE_CENTER + 导航隐藏 |
| 修复 TS 编译错误 | ✅ 完成 | 12→0 错误 |
