# 技术栈与存储方案

## 已确认技术栈

- 语言：Python 3.14
- 框架：LangChain 1.3.x
- LLM：DeepSeek
- Embedding：千问 DashScope（text-embedding-v3，默认 1024 维）
- 资讯/舆情/公告：**akshare 财经资讯接口**（东方财富新闻、财联社电报、基金公告，免费免代理）
- 通用搜索（基金经理访谈等开放式检索）：**博查 Bocha**（国内免代理，已确认）
- 基金数据源：**akshare**（免费，东方财富/天天基金）—— 已实测可用（2026-09-08 净值/持仓接口验证通过，免代理）

## 存储两层（方案 B）

| 层 | 内容 | 工具 |
|----|------|------|
| 结构化数据 | 基金、净值、持仓、季报、诊断结果、回测配置 | **SQLite**（`db/finance.db`） |
| 语义记忆 | 访谈、舆情、公告全文、诊断摘要 | **Chroma 向量库**（`chroma_db/`） |

- 两者均**免费、本地、单文件/单目录**，已被 `.gitignore` 排除，不进 git。
- SQLite 短板（多进程并发写）在单机 agent 场景不触及；将来要生产并发再迁 PostgreSQL。

## 现有密钥（在 `AgentLearn/.env`，需迁入本项目 `.env`）

- `DEEPSEEK_API_KEY` / `QWEN_API_KEY` / `BOCHA_API_KEY`（Tavily 已弃用，需代理）
