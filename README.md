# Competition Mathematical Modeling Workflow

这是一个面向数学建模竞赛与类似分析任务的 Manus 技能包。它将问题拆解、候选模型准入、可审计建模、验证、灵敏度分析、论文交付和工具证据日志整合为一条可复现工作流。

本版本新增了**残差自相关自动修正与回退协议**。当训练残差出现预先声明的自相关异常时，工作流不在最终测试期上调参，而是在训练期内部通过固定的滚动验证窗选择有限修正候选；候选冻结后才允许运行一次最终时间外确认。

## 仓库结构

| 路径 | 内容 |
|---|---|
| [`skill/`](skill/) | 可安装的 `competition-mathematical-modeling-workflow` 技能包。 |
| [`tests/`](tests/) | AirPassengers 真实时间序列上的端到端、残差自动修正和复现性测试工件。 |
| [`tests/airpassengers_model_evidence_pack.md`](tests/airpassengers_model_evidence_pack.md) | 实际填充的候选准入、模型规格、验证、残差修正与证据包。 |
| [`tests/residual_autocorrection_update_report.md`](tests/residual_autocorrection_update_report.md) | 自动修正流程的设计、更新与实测报告。 |

## 残差自相关自动修正

当训练残差诊断触发时，工作流按下列顺序执行：

1. 检查时间对齐、泄漏、异常、季节性与结构断点；前置审计失败时停止残差建模并升级为数据或规格修复。
2. 在最终测试期之外、以预先固定的有限候选比较 R0（无修正）、R1（低阶 AR 残差）、R2（季节残差）及必要时 R3（动态重规格）。
3. 通过内部滚动原点验证，以预设主指标和最小实用改善阈值选择候选；默认阈值为相对 R0 至少改善 2%。
4. 冻结选择后仅运行一次最终时间外确认；最终测试期的数值不得用于重新选择模型。
5. 未通过的修正必须回退到 R0，并在证据包中记录升级路径与结论限制。

> 自动修正只生成并检验候选，不保证修正有效，更不能替代对数据质量、规格错误或结构断点的处理。

## 复现测试

测试数据已随仓库保存，原始数据来源为公开的 AirPassengers CSV。[1] [2]

```bash
python3 -m pip install numpy pandas matplotlib
python3 tests/run_workflow_test.py
python3 tests/run_residual_autocorrection_test.py
```

运行后，`tests/results/` 会刷新结构化指标、预测表和图表。测试案例固定了内部验证原点与最终 1960 年时间外测试期，因此可验证“内部选择、外部确认”的纪律。

## 已验证结果摘要

在测试案例中，R1 残差 AR(1) 修正在未查看最终测试期的内部滚动验证中被选定：其平均 MAE 相对无修正基线改善 24.873%。冻结后对 1960 年执行一次确认，MAPE 从 7.839% 降至 6.152%。详情见 [`tests/residual_autocorrection_update_report.md`](tests/residual_autocorrection_update_report.md)。该结果仅验证工作流与测试案例，不构成生产预测保证。

## 安装技能

将 [`skill/`](skill/) 目录作为技能包导入或复制到 Manus 的技能目录。随后在处理建模竞赛题目、模型选型、可复现计算、验证与论文交付时触发 `competition-mathematical-modeling-workflow`。

## References

[1] [AirPassengers 原始 CSV](https://raw.githubusercontent.com/jbrownlee/Datasets/master/airline-passengers.csv)

[2] [jbrownlee/Datasets 中的 AirPassengers 文件](https://github.com/jbrownlee/Datasets/blob/master/airline-passengers.csv)
