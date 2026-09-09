# TASKS — 功能实现清单

> **用途**：按顺序记录要实现的功能，**一条条测试通过后再做下一条**。
> **状态**：`[ ]` 未开始 · `[~]` 进行中 · `[x]` 已通过测试
> **约定**：每完成一条 → commit 一次 → 在这里打勾并写一句验收结果。

---

## 全局设计约束（必须遵守）

- **工具与 loop 解耦**：所有工具独立放 `tools/` 目录，通过**工具注册表**注入 agent loop；loop 本身不 import 任何具体工具。新增工具 = 新建一个 tool 文件 + 注册一行，**不改 loop 代码**。
- **黑名单代码级硬保障**：🔴 禁止操作由 `src/guards/policy.py`（代码）在工具调用前拦截，**不依赖 markdown/提示词**，防止 LLM 幻觉绕过；`permissions.md` 仅作人类可读镜像。

---

## 阶段 0：可对话的最小骨架

### T1 项目骨架与依赖
- [x] 建立目录结构、`requirements.txt`、安装依赖
- **验收**：`python -c "import langchain, chromadb, akshare, dashscope"` 可正常导入 ✅ 通过（langchain 1.3.14 / chromadb 1.5.9 / akshare 1.18.94）

### T2 环境配置
- [x] 密钥已复制进本项目 `.env`（DeepSeek/千问/Bocha），与 AgentLearn 解耦，删除 AgentLearn 后仍可运行
- [x] 建立 `config.yaml` + 配置加载器（`src/config.py`）
- **验收**：脚本能读到 `DEEPSEEK/QWEN/BOCHA` key，且 `.env` 未被 git 追踪 ✅ 通过

### T3 最小对话
- [x] 接 DeepSeek，实现一问一答（纯 LLM，无工具）
- **验收**：命令行输入一句话，返回合理中文回复 ✅ 通过（`python -m src.chat "..."`）

### T4 Goal loop 骨架
- [x] 目标 → 分解 → 执行 → 评估 → 终止 的循环框架（`src/loop.py`）
- [x] 最大步数安全网 + 免责声明注入 + "需人决策则暂停"分支
- [x] 工具通过**注册表**注入，loop 内不写具体工具
- [x] 权限检查用 **hook 注册表**（`trigger_hooks("PreToolUse", block)`），规则独立注册
- **验收**：给定一个目标，agent 能自主循环（调用占位工具）直到汇总或触发终止条件 ✅ 通过（🔴/🟡/🟢 三种拦截均验证）

---

## 阶段 1：数据与工具

### T5 数据源：净值 / 持仓 / 季报
- [x] akshare 封装：拉取指定基金的净值、持仓、季报（`data_sources/fund.py`）
- **验收**：输入基金代码，返回结构化数据（打印可读）✅ 通过（净值/持仓/行业配置/报告公告 四类均返回 DataFrame）

### T6 数据源：访谈 / 舆情 / 公告
- [x] 舆情/公告：akshare 财经资讯接口（财联社电报、分红/人事公告，`data_sources/news.py`）
- [x] 访谈：博查 Bocha 通用搜索封装（国内免代理，`data_sources/search.py`）
- **验收**：按关键词返回相关标题 + 摘要 ✅ 通过

### T7 工具集接入
- [x] 把 T5/T6 封装成 agent 可调用的 tool（`tools/fund_tools.py` 等，独立放 `tools/`）
- [x] 通过**工具注册表**接入，不改 loop 代码（替换 mock 为真工具）
- **验收**：goal loop 能自动选择并调用正确工具 ✅ 通过（端到端：拉真实 akshare 数据并汇总）

### T8 数据库持久化（SQLite）
- [x] 建表：基金 / 净值 / 持仓 / 行业配置 / 公告 / 诊断 / 回测配置（`db/models.py`）
- [x] CRUD：upsert 落库 + 查询（`db/crud.py`，INSERT OR IGNORE 去重）
- **验收**：拉取的数据能写入并查询 ✅ 通过（幂等去重验证正常，`.db` 已忽略）

### T9 语义记忆（Chroma）
- [x] 访谈 / 舆情 / 公告写入向量库（`src/semantic_memory.py` + `src/embeddings.py`），支持语义检索
- **验收**：按意思能搜到相关记录 ✅ 通过（查询词未逐字出现，语义命中）

---

## 阶段 2：业务能力

### T10 基金对比
- [x] 多基金横向对比（业绩 / 波动 / 回撤 / 持仓重叠，`src/metrics.py` + `tools/compare_tools.py`）
- **验收**：输入 ≥2 只基金，输出对比表 ✅ 通过（真实数据 + loop 自动调用）

### T11 持仓诊断 + 风险点提示
- [x] 集中度 / 行业暴露 / 风格漂移 / 回撤 → 风险点提示（`src/diagnosis.py` + `tools/diagnose_tools.py`）
- [ ] 换手率：暂缺数据源，deferred
- **验收**：输入持仓，输出风险清单（只提示、不下结论）✅ 通过

### T12 回测编排
- [x] 回测配置 → 数据 → 策略 → 结果 → 报告 的编排框架（`src/backtest.py`，策略可插拔）
- [x] 两条示例策略：买入持有 + 定投
- **验收**：给定配置能跑通一条回测并出报告 ✅ 通过

### T13 信息汇总
- [x] 把多来源整合成一份结构化报告（`src/report.py` + `tools/report_tools.py`）
- **验收**：一个目标能产出完整汇总报告 ✅ 通过

---

## 阶段 3：工程化

### T14 日志 / 任务记录
- [x] 数据拉取失败重试（`src/retry.py`，3次/间隔2秒）+ 任务留痕（`src/logger.py` + loop 日志）
- [x] 工具调用失败兜底（不崩溃，记日志返回错误）
- **验收**：出错可追溯（日志里能查到失败原因）✅ 通过

### T15 测试
- [x] pytest 配置（`pytest.ini`）+ 6 个测试文件（loop 分支 / 提示词 / 输出合规 / metrics / diagnosis / backtest）
- **验收**：`pytest` 全绿 ✅ 20 passed

### T16 合规 / 免责声明
- [x] 统一免责声明注入 + 去重（`src/output.py::finalize`，loop/chat 双路径接入）
- **验收**：任何输出都带"不构成投资建议" ✅ 通过（去重后「不构成」仅出现 1 次）
