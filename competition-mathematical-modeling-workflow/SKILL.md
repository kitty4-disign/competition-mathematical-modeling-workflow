---
name: competition-mathematical-modeling-workflow
description: End-to-end, evidence-first workflow for MCM/ICM, CUMCM, and similar mathematical modeling competitions. Use when Codex must frame a contest problem, audit data, compare and formalize models, implement reproducible computation, design falsifiable validation, quantify uncertainty, audit an existing model/code/paper, or produce a traceable competition paper and submission package. Also use for partial requests such as model selection, robustness review, or paper-only work when the answer must stay bounded by available evidence. Do not use for routine arithmetic, isolated theorem proofs, or software work without a modeling deliverable.
---

# 竞赛数学建模：证据优先工作流

把赛题转化为可解释、可计算、可证伪、可复现的结论。把模型、代码、工具和 Agent 输出一律视为候选；只有通过预先声明门禁的结果才能进入论文主张。

## 1. 守住六条不变量

| 不变量 | 执行要求 |
|---|---|
| 证据先于主张 | 为每条数值、比较、最优性、稳健性、因果或建议性主张建立完整链：`输入版本 → 假设/规格 → 代码/运行 → 结果工件 → 验证 → 允许的结论边界`。 |
| 基线先于复杂度 | 先建立最简单可复现基线；只有新增复杂度带来预声明、可重复且有实际意义的改善时才保留它。 |
| 验证先于结果 | 在看结果前冻结主指标、基线、阈值、切分/情景、种子、比较次数和最终测试使用规则。 |
| 单一事实源 | 用一个工作台账维护版本、决策、运行、结果和主张；不要让聊天记录或多份手工表格分别承担真相。 |
| 变更向下游失效 | 题目、规则、数据、假设、规格、代码或参数版本变化时，将依赖它的结果、验证、图表和主张标为 `stale`，重算复验后才能恢复。 |
| 失败时收缩结论 | 缺少材料性输入、验证失败、权限不足或预算耗尽时，分支分析、降级主张或停止；不得用默认值、文字润色或重复调用掩盖缺口。 |

## 2. 建立最小任务合同

先选择请求模式：`full-workflow`、`audit-existing`、`paper-only` 或 `algorithm-advice`。只交付该模式需要的工件，但始终报告范围、证据状态、局限和下一步。`paper-only` 要区分内部占位稿与可提交文本：未冻结的数字只能在内部稿中标成待核验观察，不得进入可提交摘要或结论。

对非平凡任务，复制 [`assets/templates/workflow-ledger.md`](assets/templates/workflow-ledger.md) 作为唯一工作台账；对一次性简短建议，在回复中维护同样的最小字段即可。按 [`references/artifact-contracts.md`](references/artifact-contracts.md) 分配工件职责，不重复保存同一事实。

在台账中冻结：

1. 题目、附件、数据和当届官方规则的版本或来源；
2. 子问题、目标输出、不解决范围、硬约束与资源预算；
3. 成功指标、基线、接受阈值及结论允许达到的强度；
4. 数据切分、验证情景、随机种子、最终测试和比较预算；
5. 允许的工具、读写范围、敏感数据边界和需人工确认的动作。

将可能改变硬约束、主要数值、方案排序、结论强度或提交合规的缺口标为“材料性缺口”。先询问用户；若用户暂时无法补充，只能并列运行清楚标注的情景，不得用一个“合理默认值”替代。非材料性缺口可采用最小假设，但要记录理由和影响。

为每个阶段门禁写 `GateSpec`：`判据 / 指标 / 阈值 / 数据切分或情景 / 证据 ID / 独立复核方式 / pass|fail|waived`。仅在说明豁免理由、替代证据和残余风险时使用 `waived`。

## 3. 按状态机推进

工件“已写出”不等于门禁通过。只有本阶段所有任务类型必做检查为 `pass` 或有合格 `waived` 记录时，才执行 `advance`。

| 阶段 | 最小动作 | 退出证据 | 失败路由 |
|---|---|---|---|
| 0 合同 | 冻结目标、边界、规则、预算、验证计划和版本 DAG。 | 工作台账、材料性缺口清单、GateSpec。 | 关键目标/规则不清：`escalate`；可分支的不确定性：建立情景。 |
| 1 题意与数据 | 拆分依赖子问题；审计字段、单位、缺失、异常、泄漏、时间顺序和抽样偏差。 | 需求映射、变量字典、数据质量与残余风险。 | 数据/口径错误：修复输入；无法合法取得关键输入：`escalate`。 |
| 2 规格与选型 | 建立基线和有限候选；冻结实验计划；写出题意—公式—代码映射。 | 候选状态、数学规格、预注册验证计划、失效条件。 | 目标/约束不清：回阶段 0/1；候选无数据或无法验证：降级或拒绝。 |
| 3 实现与实验 | 分离加载、清洗、建模、求解、评估和作图；从小例子与基线开始。 | 可运行代码、运行清单、状态、结果 ID、失败运行。 | 路径/依赖：执行级修复；实现偏离规格：实现级；无解/不稳：规格级。 |
| 4 证伪与稳健性 | 先尝试推翻关键主张；完成任务类型的全部必做验证，再做额外广度检查。 | 主张台账、基线差异、专属诊断、反例/边界、结论强度。 | 泄漏：回输入层；规格错误：回阶段 2；仅叙事过强：删除或降级主张。 |
| 5 论文与提交 | 只引用 `frozen` 结果；从至少一个关键主张逆向复现到原始输入。 | 同源论文、图表、附录、规则画像与合规清单。 | 数字/引用不一致：重生成；规则未核验：`escalate`；无证据主张：删除。 |

## 4. 选择最小充分模型

模型选型时读取 [`references/model-selection-atlas.md`](references/model-selection-atlas.md)，并执行以下顺序：

1. 根据预测、优化、解释、排序、机制、网络或仿真目标定义输出与损失；不要由算法名称倒推问题。
2. 建立可手算、规则式或简单统计基线。
3. 为每个候选记录状态：`admitted`、`conditional`、`exploratory` 或 `rejected`。把硬约束匹配、数据可用性、可验证性和资源上限作为否决条件；不要用无锚点总分掩盖致命缺陷。用于可提交方案的基线也必须满足全部硬约束；不可行松弛只能作诊断下界或探索性对照。
4. 只比较通过准入的候选；优先选择能回答问题的最低复杂度方案。
5. 写出集合/索引、变量域、参数来源、目标/状态方程、约束、初边值、估计/求解算法、终止规则、输出、适用范围和失效条件。
6. 用单位、边界、小例子和独立实现中的至少一种复核高风险公式；代数正确不等于建模语义正确。

## 5. 冻结验证并限制主张

实现或审计时读取 [`references/verification-and-repair.md`](references/verification-and-repair.md)。按任务类型完成其中的最低验证组合；不得用“任选若干项”绕过预测的时间切分、优化的可行性、仿真的多种子或排序的权重稳定性等专属门禁。

将最终测试集或最终确认情景封存到模型、特征、阈值和候选均冻结之后。最终确认只评估预先冻结的候选与基线；如果结果不理想，如实报告并降低结论，不得回看后重选。若要继续开发，建立新计划版本和新的未污染验证证据。

对高风险结论使用两个失效模式不同的检查，例如“求解器可行性 + 小规模枚举”或“时间外误差 + 朴素基线/残差”。若不能完成独立检查，明确将结论降级为 `exploratory`。

时间序列残差异常时，额外读取 [`references/residual-autocorrelation.md`](references/residual-autocorrelation.md)。随机仿真、尾部风险或分布结论读取 [`references/simulation-uncertainty-experiments.md`](references/simulation-uncertainty-experiments.md)。

## 6. 只在需要时运行受控 Loop

不要因为当前执行者是 Agent、使用了一次工具或进行了一次计算就启动完整 Loop。仅在多轮候选修复、跨会话恢复、显式自主迭代或需要预算化搜索时读取 [`references/agent-loop-governance.md`](references/agent-loop-governance.md)；使用 AI 生成实质性规格、代码或主张时再读取 [`references/ai-assisted-modeling.md`](references/ai-assisted-modeling.md)。

每轮只改变一个主要假设、规格或实现因素，并记录预期信息增益、验证证据和下一步唯一动作。使用：

- `advance`：当前 GateSpec 全部通过；
- `retry`：存在一个明确、低风险、可检验的失败原因；
- `rollback`：候选低于冻结基线、违反硬约束或使证据链失效；
- `escalate`：材料性输入、规则、权限或全局预算不足；
- `stop(reason)`：以 `completed`、`budget-exhausted` 或 `aborted` 结束。

另外记录最终 outcome：`completed`、`partial`、`blocked` 或 `invalidated`。outcome 描述本次请求的交付状态，不等于模型评分：能交付证据受限但有用的子集时用 `partial`；外部输入或权限使任何负责的请求工件都无法产出时用 `blocked`；工件所依赖的关键证据已明确失败、不得继续使用时用 `invalidated`。不要用 `stop` 同时表示成功和失败。

## 7. 按需加载资源

| 场景 | 读取 | 使用的模板 |
|---|---|---|
| 任意非平凡任务 | [`artifact-contracts.md`](references/artifact-contracts.md) | [`workflow-ledger.md`](assets/templates/workflow-ledger.md) |
| 模型候选与数学规格 | [`model-selection-atlas.md`](references/model-selection-atlas.md) | [`model-evidence-pack.md`](assets/templates/model-evidence-pack.md) |
| 工具、检索、代码或求解器 | [`tool-enhanced-execution.md`](references/tool-enhanced-execution.md) | [`tool-evidence-log.md`](assets/templates/tool-evidence-log.md) |
| 团队并行与交付依赖 | [`team-and-artifact-orchestration.md`](references/team-and-artifact-orchestration.md) | 工作台账中的负责人和依赖字段 |
| 论文、摘要、图表与提交 | [`paper-prose-integrity.md`](references/paper-prose-integrity.md) | [`competition-profile.md`](assets/templates/competition-profile.md)、[`contest-paper-outline.md`](assets/templates/contest-paper-outline.md)、[`abstract-and-results-template.md`](assets/templates/abstract-and-results-template.md)、[`figure-table-and-appendix-template.md`](assets/templates/figure-table-and-appendix-template.md)、[`submission-compliance-template.md`](assets/templates/submission-compliance-template.md) |

需要外部事实、当前赛事规则、代码执行或连接器时，先读取工具规范，记录来源、日期、输入版本、权限、原始状态和独立检查。不得伪造“已查询”“已运行”“最优”或“已验证”。任何影响结论的外部写入、上传、提交、发布、排程或权限提升，都要遵守当前环境的授权与安全规则。

## 8. 交付可审计结果

按请求模式交付，不强行生成完整论文。最终回答至少列出：

1. 当前 outcome 与完成范围；
2. 冻结的关键输入、模型和结果版本；
3. 通过、失败与豁免的 GateSpec；
4. 可支持的核心主张及其证据 ID；
5. 未解决风险、已失效工件和不能推出的结论；
6. 下一步唯一动作，或任务完成的停止理由。
