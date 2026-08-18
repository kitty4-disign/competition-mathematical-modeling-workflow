---
name: competition-mathematical-modeling-workflow
description: Competition-grade mathematical modeling workflow for MCM/ICM, CUMCM, and similar contests. Use when given a modeling problem statement, data, or partial solution and asked to frame the problem, select and formalize models, implement reproducible computation, validate results, or produce a competition paper and submission checklist. Do not use for routine arithmetic, isolated proof questions, or general software development without a modeling deliverable.
---

# 竞赛数学建模工作流

将真实题目转化为**可解释、可计算、可验证、可复现**的方案。把模型或 Agent 生成的内容视为待检验的候选，不把它当作结论。

本 Skill 提供独立的通用工作流，参考端到端数学建模 Agent 的“分析—建模—计算—报告”分段思路，但**不包含**其源码、数据、模型密钥或运行环境。若另行使用外部 Agent，先审阅其许可证、依赖与数据处理方式。

## 启动与输入检查

收集题目、数据/字段说明、竞赛规则、交付格式、时间限制和已有成果。先从 `templates/competition-profile.md` 建立当届赛事画像；只使用已由官方文件核验的格式、匿名、页数、附件和提交规则。然后明确写出问题背景、决策对象、子问题、数据来源与口径、目标、硬/软约束、评价标准和可验证基线。

信息缺失但不阻塞时，采用最少的合理假设并集中列入“假设与局限”；信息会改变模型选择时，先索取信息，不要隐式猜测。建立 `decision_log`，记录模型选择、参数口径和被排除的替代方案。若计划使用 LLM、Agent 或生成式工具，先读取 `references/ai-assisted-modeling.md`，建立“任务合同”，并将 AI 输出视为待验证候选。

开始任一阶段时，读取 `references/deliverables.md` 并建立相应交付物。每个关键子问题从 `templates/model-evidence-pack.md` 复制一份“模型证据包”，并在选型、实现、验证和论文写作时持续更新。多问题赛题、工作流切换或结果需要进入论文时，读取 `references/modular-task-routing.md`，从 `templates/task-method-result-map.md` 建立“需求—方法—结果—验证—图表/正文”映射；随机仿真或风险分布任务先读取 `references/simulation-uncertainty-experiments.md`。若当前会话存在合适的已启用工具/连接器，先阅读 `references/tool-enhanced-execution.md`，完成工具预检，并从 `templates/tool-evidence-log.md` 建立工具证据日志；没有合格工具时使用其降级方案。若使用 LLM、Agent 或生成式工具，按 `references/ai-assisted-modeling.md` 记录任务合同、权限边界、输出工件、人工审查与独立检查。按任务加载专项参考：模型选择时读取 `references/model-selection-atlas.md`；实现、验证或出现异常结果时读取 `references/verification-and-repair.md`；团队协作、排期或论文串联时读取 `references/team-and-artifact-orchestration.md`。撰写论文前，先读取 `references/paper-prose-integrity.md`，完成“主张—证据—自然表达”审阅；若赛事画像为长三角杯式中文论文，再读取 `templates/yangtze-delta-paper-draft.md`；其他赛事读取 `templates/contest-paper-outline.md`。摘要使用 `templates/abstract-and-results-template.md`，图表和附录使用 `templates/figure-table-and-appendix-template.md`，导出前使用 `templates/submission-compliance-template.md`。

## 顺序工作流

### 1. 题意拆解与数据审计

将题目拆为相互依赖的子任务，并为每项指定输入、输出、方法候选和验收标准。将自然语言限制转为可检查的约束；区分题设条件、数据支持的假设和为简化而设的假设。

先完成数据审计和最低成本的探索性分析。检查字段类型、范围、缺失、重复、异常、泄漏、量纲、时间顺序和抽样偏差。需要外部事实、标准、统计或文献时，先按 `tool-enhanced-execution.md` 执行来源检索并记录 URL、日期和使用位置；不得用编造数据、无法追溯的外部数字或未说明的插补支撑关键结论。

**通过门槛：** 形成问题定义、变量字典、数据质量说明、假设清单和子任务路线图。

### 2. 生成并选择模型

为每个关键子任务提出至少两个合理候选，除非题目结构已经唯一限定模型。先完成 `references/model-selection-atlas.md` 的六维分类，并在 `templates/model-evidence-pack.md` 填写候选准入门禁（目标、数据、可检验假设、复现与审计）；门禁不通过的候选不得进入比较表。随后完成候选比较表和“题意—公式”映射，再用解释性、数据需求、约束匹配、计算成本、可验证性和竞赛叙事完整性比较，而不是只选最复杂的方案。

| 问题信号 | 首选方向 | 必须验证 |
|---|---|---|
| 资源分配、选址、排班、路径、离散决策 | LP/MILP、约束规划、网络流或启发式 | 可行性、整数性、基线差异、求解间隙 |
| 连续演化、机制关系、传播或控制 | ODE、差分方程、状态空间或控制 | 单位/量纲、初值、稳定性、参数敏感性 |
| 时间序列预测或预警 | 基线预测、回归、状态空间或机器学习 | 严格时间切分、误差指标、滚动验证、泄漏检查 |
| 节点关系、连通性或扩散 | 图模型、网络流、中心性或传播模型 | 网络构造依据、连通性、扰动情景 |
| 多指标排序或方案优选 | 透明的多准则决策模型 | 指标方向、标准化、权重来源、权重敏感性 |
| 个体互动导致宏观现象 | 仿真或主体建模 | 随机种子、多次运行、校准、情景区间 |

把选定方案写成可审计的数学规格：集合/索引、变量、参数、目标函数、约束、初值与边界、估计方法、求解器/算法、输出和适用条件。将每一项公式映射到题意或数据字段。对高风险公式先用合法变量域、单位和小例子完成检查；若使用符号/计算工具，按工具增强规范记录调用及独立代入验证。

**通过门槛：** 形成候选比较表、模型规格和“为何适用/何时失效”的解释。

### 3. 计算实现与实验设计

将数据加载、清洗、建模、求解、评估和作图分离。固定随机种子，记录包版本、参数、输入文件版本和运行时间。为每个核心模块加入小规模或极端情形测试；先复现基线，再增加复杂模型。若包含随机仿真，按 `references/simulation-uncertainty-experiments.md` 记录随机机制、种子策略、收敛诊断、重复运行与风险指标。

只报告可重复计算得到的数字。遇到无解、未收敛、数值不稳或求解器超时，应诊断并记录状态；松弛或近似方法必须明确标注，不得把失败输出包装成最优结果。若修复无效，按 `references/verification-and-repair.md` 的“执行级→实现级→规格级→问题级”协议升级；重复代码修补不能替代对数学规格的复核。

**通过门槛：** 交付可运行代码、环境说明、实验配置、结果表和图的生成路径；对影响结论的代码、求解或外部工具调用，工具证据日志中必须有输入版本、输出工件、状态和独立检查。

### 4. 验证、稳健性与反例检查

预测任务使用独立验证或时间外测试，并在训练残差按预先声明的诊断出现自相关异常时，执行 `references/verification-and-repair.md` 的残差自相关自动修正与回退协议：先完成对齐/泄漏/断点审计，在训练期内部滚动验证有限修正候选，冻结选择后才运行一次最终时间外确认。优化任务检查可行性、约束违反和基线差异；机制模型检查量纲、边界、极端情景和已知规律；仿真任务按 `references/simulation-uncertainty-experiments.md` 报告重复运行、收敛、分布/尾部风险与不确定性来源。先建立证据矩阵，再按 `references/verification-and-repair.md` 完成四层审计。

至少完成以下四项中的三项，并解释不能完成的项目：基线比较、灵敏度分析、替代模型比较、边界/极端情景测试、误差/残差检查、外推风险检查。若进行灵敏度分析，必须在 `templates/model-evidence-pack.md` 记录基准点、参数范围/分布、局部或全局方法、步长或采样收敛检查及结论边界；不得把局部排序写成全局重要性。优先报告模型失败条件和结果稳定区间。

**通过门槛：** 每个关键结论都能追溯到公式、数据、参数、实验或图表；关键局限不被隐藏。

### 5. 论文与提交

把论文写成可独立理解的论证，而不是代码说明书。先说明问题、假设和符号，再按“目的—输入与假设—模型—求解—证据—解释—局限”叙述每个子任务。完成 `templates/task-method-result-map.md`，确认每项题目要求都映射到方法、已冻结结果、验证和正文/图表位置。采用 `references/team-and-artifact-orchestration.md` 中的交付物依赖图和图表审阅协议；每张图表必须有编号、单位、来源/生成口径和一句支持论点的解读。

完成前执行终检：检查是否回答所有问题、符号是否首次定义、表图和正文数字是否一致、约束是否满足、引用是否可追溯、结论是否超过证据范围、附件是否可复现；核对 `templates/task-method-result-map.md`，确保摘要与结论只引用已冻结结果；按 `references/paper-prose-integrity.md` 完成主张回链、推断强度、模板化表述和局限呈现复核。

**通过门槛：** 依据赛事画像选择的论文模板完成结构；摘要、图表、附录与支撑材料均可回链到模型证据包；按 `references/paper-prose-integrity.md` 完成自然表达与证据完整性审阅；使用 `templates/submission-compliance-template.md` 完成格式、匿名、引用和文件一致性终检。

## 必须遵守的质量规则

- 优先简单、可解释且可验证的模型；只有在验证改善时才增加复杂度。
- 明确区分“题设事实”“数据观察”“模型假设”“计算结果”和“解释性推断”。
- 不虚构文献、数据、求解状态、精度或真实世界效果。
- 不使用测试集反复调参；不将相关性直接写成因果关系。
- 对外部工具或 Agent 产生的公式、代码和引用逐项检查后再使用；先由人工完成题意与约束初稿，再以任务合同要求 AI 给出可比较候选。对 AI 生成代码采用最小复现和复验循环，对高风险结论采用两个失效模式不同的检查，详见 `references/tool-enhanced-execution.md` 与 `references/ai-assisted-modeling.md`。
- 在交付中保留局限、误差来源、适用范围和改进方向。

## 常见请求的路由

**从零开始做题：** 执行全部五阶段，并在每个门槛处复核。  
**已有模型或代码：** 先审计问题定义、数据口径、约束和验证，不要直接润色论文。  
**只需论文：** 先索要模型规格、实验记录和结果；证据缺失时写明所需验证，不编造。  
**只需算法建议：** 交付候选比较表、模型规格草案、数据需求和验证计划，而不是无依据地指定唯一算法。

## 交付标准

最终交付至少包含：问题与假设摘要、变量与数据字典、模型规格、方法选择依据、可复现计算说明、验证证据、结果解释、局限性、论文/提交清单。为每个数值结论提供生成来源或复算步骤。
