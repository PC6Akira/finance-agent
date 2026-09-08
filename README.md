# finance-agent

基金投研辅助 Agent —— 定位为**人的助手**，不代替人预测涨跌、不给买卖建议。

## 做什么（Do）
- 拉取基金季报、持仓、净值、基金经理访谈、舆情、行业公告
- 基金对比、风险点提示、持仓诊断、回测架构编排、信息汇总

## 不做什么（Don't）
- ❌ 帮助用户投资 / 给出买卖决策
- ❌ 预测未来收益率 / 判断涨跌

## 技术栈
- Python 3.14
- LangChain + Chroma（向量检索/知识库）
- DeepSeek（LLM）、千问 DashScope（Embedding）、博查 Bocha（通用搜索）
- akshare（基金数据源 + 财经资讯，免费）

## 目录结构
```
finance-agent/
├── .env / .env.example   # 环境变量（.env 已 gitignore）
├── README.md / TASKS.md  # 项目说明 / 功能实现清单
├── requirements.txt      # 依赖清单
├── memory/               # 项目记忆（定位/技术栈/决策/权限）
├── src/                  # agent 引擎（goal loop）
│   └── guards/           # 黑名单代码级硬保障（policy.py / guard.py）
├── tools/                # 工具（独立文件，注册表注入，与 loop 解耦）
├── data_sources/         # 数据源封装（akshare / Bocha）
├── db/                   # SQLite 持久化
├── prompts/              # 系统提示词（角色 + 红线）
└── config/               # 配置（config.yaml）
```
