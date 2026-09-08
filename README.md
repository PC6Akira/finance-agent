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
- DeepSeek（LLM）、千问 DashScope（Embedding）、Tavily（联网搜索）
- akshare（基金数据源，免费）

## 目录结构（规划中）
```
finance-agent/
├── .env.example      # 环境变量模板（复制为 .env）
├── README.md
├── CLAUDE.md         # 项目约定/红线/架构
├── db/               # 数据库 schema 与持久化
├── data_sources/     # 数据源封装（净值/持仓/季报/舆情/公告）
├── tools/            # Agent 工具集
├── prompts/          # 系统提示词 / 角色与红线
└── ...
```
