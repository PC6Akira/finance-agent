# eval — 事实可靠性 + 红线合规评测

> **用途**：量化 agent 的事实可靠性（编造/错配）与红线合规，5 个指标见下。
> **原则**：全程**离线注入假数据**，不联网、不依赖每日变化的 akshare，保证可复现。

## 5 个指标

| 指标 | 测法 |
|---|---|
| 基线含错率 | 关 verifier 跑 B 层样本，judge 判含错比例 |
| verifier precision | A 层构造样本（报出的问题里真问题占比） |
| verifier recall | A 层构造样本（真问题里被抓住占比） |
| 净收益 | 基线含错率 − 开 verifier 含错率 |
| 红线违规率 | 确定性正则 + 扩展表 |

## 目录结构

```
eval/
├── harness.py              # 注入假工具 → 跑 run() → 收集输出 + 工具调用
├── judge.py                # LLM-as-judge 判"含错"（待建）
├── redline.py              # 红线确定性检测（待建）
├── report.py               # 汇总 5 指标（待建）
└── fixtures/
    ├── universe.json         # 6 只假基金宇宙（地面真值来源）
    ├── b_cases.jsonl         # B 层 100 条端到端样本
    └── a_cases.jsonl         # A 层构造样本（待建）
```

## 怎么跑

```bash
# 确定性自检（不调 LLM、不联网）：验证假数据注入生效
.venv/bin/python eval/harness.py --self-test

# 校验样本（不调 LLM）：看条数、分类统计、查重复 id
.venv/bin/python eval/harness.py --check-cases eval/fixtures/b_cases.jsonl

# 全量评测（judge/redline 就绪后接入，会调 DeepSeek）
.venv/bin/python eval/harness.py --cases eval/fixtures/b_cases.jsonl --out eval/results.jsonl
```
