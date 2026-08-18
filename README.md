# Competition Mathematical Modeling Workflow

这是一个面向数学建模竞赛与类似分析任务的**通用、可复现工作流与资源包**。它将问题拆解、候选模型准入、可审计建模、验证、灵敏度分析、论文交付和工具证据日志整合为一条可复现的执行链。

它**不只适用于 Manus**。核心工作流、参考规范、Markdown 模板、证据包和 Python 测试脚本均不依赖 Manus，可由个人、团队、其他 AI/Agent 框架或一般自动化环境直接阅读、采用和改造。`skill/` 目录只是把相同内容封装为 Manus 可识别的技能包，以便在 Manus 中自动路由和加载；它不是使用这些方法的前提。

当前版本在既有五阶段建模流程之上加入了**受控 Agent Loop**：使用 LLM、Agent、工具调用、多轮修复或跨会话恢复时，每一轮都必须冻结输入、提出一个可检查的候选或最小变更、运行批准的验证、独立复核并更新外部状态。该机制以 `advance`、`retry`、`rollback`、`escalate` 与 `stop` 作为显式路由，避免将“Agent 多跑几轮”误当作优化。

> 本项目追求的不是让 Agent 无限尝试，而是让每一轮都有可追溯证据、限次修复、资源边界和清晰的人工升级条件。

本版本也保留了**残差自相关自动修正与回退协议**。当训练残差出现预先声明的自相关异常时，工作流不在最终测试期上调参，而是在训练期内部通过固定的滚动验证窗选择有限修正候选；候选冻结后才允许运行一次最终时间外确认。

## 仓库结构

| 路径 | 内容 |
|---|---|
| [`skill/`](skill/) | Manus 技能包封装；其中的 Markdown 工作流、参考规范与模板同样可被其他环境直接使用。 |
| [`skill/references/agent-loop-governance.md`](skill/references/agent-loop-governance.md) | Agent Loop 的状态、阶段门禁、修复上限、无进展检测、权限与退出规则。 |
| [`skill/templates/agent-loop-state.md`](skill/templates/agent-loop-state.md) | 多轮执行与跨会话状态模板；不替代模型证据包、工具证据日志或决策日志。 |
| [`tests/`](tests/) | 不依赖 Manus 的 AirPassengers 真实时间序列端到端、残差自动修正与复现性测试工件。 |
| [`tests/airpassengers_model_evidence_pack.md`](tests/airpassengers_model_evidence_pack.md) | 实际填充的候选准入、模型规格、验证、残差修正与证据包。 |
| [`tests/residual_autocorrection_update_report.md`](tests/residual_autocorrection_update_report.md) | 自动修正流程的设计、更新与实测报告。 |

## 受控 Agent Loop

当任务涉及 Agent、外部工具、多轮修复、跨会话恢复或迭代优化时，应建立任务合同与 `agent-loop-state.md`。每次迭代只处理一个明确子问题：

```text
冻结输入与约束 → 提出一个候选或最小变更 → 执行批准检查 → 独立复核
→ 更新状态、证据包、工具日志与决策日志 → advance / retry / rollback / escalate / stop
```

阶段之间按**证据门禁**而非“已写完文本”推进。默认只允许两次执行级修复和一次实现级修复；超过上限时必须回溯到模型规格或问题定义，而不是反复更换提示词。连续两轮没有新增通过检查、失败类别相同且变更集合重复时，视为无进展，必须回退或升级人工。

| 决策 | 适用场景 | 必须动作 |
|---|---|---|
| `advance` | 当前阶段全部门禁通过。 | 冻结工件并进入下一阶段。 |
| `retry` | 存在明确、低风险、可检验的失败原因。 | 只改一个主要候选或修复层后复验。 |
| `rollback` | 新候选低于基线、违反硬约束或断开证据链。 | 恢复最近可复现基线，保留失败运行。 |
| `escalate` | 输入、规则或权限不足；风险越界；修复层级耗尽。 | 停止自动动作，明确人工需要处理的缺口。 |
| `stop` | 目标完成或达到轮数、时间、工具预算。 | 记录停止理由、未完成内容和后续人工动作。 |

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

## 使用方式：Manus 与非 Manus 环境

| 使用场景 | 建议方式 |
|---|---|
| Manus | 将 [`skill/`](skill/) 导入或复制到 Manus 的技能目录，在建模竞赛题目、选型、计算、验证和论文交付任务中触发 `competition-mathematical-modeling-workflow`。 |
| 其他 AI/Agent 框架 | 将 [`skill/SKILL.md`](skill/SKILL.md) 作为流程说明，按需加载 `references/` 与 `templates/`；把状态模板、模型证据包和审计表接入任务状态、提示词或工作流引擎。 |
| 人工团队或通用自动化 | 直接采用 `references/` 中的阶段门禁与 `templates/` 中的 Markdown 工件；使用 `tests/` 的脚本、数据和结果作为可复现实例。 |

无论使用何种平台，都应遵循相同边界：候选模型先经过数据、假设和复现性准入；模型修改不能使用最终测试期调参；外部工具、AI 生成公式或代码需保留来源、最小复现和独立检查记录。

## 安全与权限边界

先使用确定性检查、可复现计算和外部状态，再使用模型自评。只在隔离环境和非敏感样本上运行已审阅代码；不要把密钥、Cookie、个人信息、未公开赛题或原始敏感数据写入状态、日志或第三方服务。

未经用户明确授权，不进行外部写入、提交、发布、排程或权限提升。赛事规则、模型选择、关键假设、最终结论和论文提交必须保留人工判断。任何成功结论都应能回链到公式、数据、参数、实验、图表或权威来源。

## 第三方内容与许可

[`skill/third_party/mathhub/`](skill/third_party/mathhub/) 中含有从 [AI-Dog-Creater/MathHub](https://github.com/AI-Dog-Creater/MathHub) 原样复制的有限上游组件，源修订为 `7ac101d2abb3769f6d3bc020e87a67cb6c539263`。这些文件受 **PolyForm Noncommercial 1.0.0** 约束，允许非商业使用、修改与分发，但不授予商业用途、再许可或转让权利。

> **Required Notice:** Copyright 2026 AI-Dog-Creater.

若再分发 `skill/third_party/mathhub/` 中的任一上游文件，必须同时保留并提供 [`skill/third_party/mathhub/NOTICE.md`](skill/third_party/mathhub/NOTICE.md) 与 [`skill/third_party/mathhub/upstream/LICENSE.txt`](skill/third_party/mathhub/upstream/LICENSE.txt)。该第三方许可不自动适用于本仓库其他原创工作流和模板；在任何可能具有商业目的的使用或分发前，请自行核验全部适用权利与许可条件。

## 局限

本项目提供的是工作流、验证协议和模板，而不是特定赛题的标准答案、获奖承诺、模型 API、数据集或可直接部署的自动化系统。最终赛事规则、数据口径、模型适用性和提交内容必须以当届官方材料及独立复核为准。

## References

[1] [AirPassengers 原始 CSV](https://raw.githubusercontent.com/jbrownlee/Datasets/master/airline-passengers.csv)

[2] [jbrownlee/Datasets 中的 AirPassengers 文件](https://github.com/jbrownlee/Datasets/blob/master/airline-passengers.csv)
