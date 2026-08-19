# Competition Mathematical Modeling Workflow

一个面向 MCM/ICM、CUMCM 与类似任务的证据优先建模 skill。它把赛题、数据、模型、计算、验证和论文连接成可追溯状态机，并明确阻止三类常见失败：先选算法再找问题、看完结果再定验证、用图表或措辞替代证据。

## 第一性原理

本 skill 从六条不可破坏的不变量出发：

1. 每条主张都要经过 `输入 → 规格 → 运行 → 结果 → 验证 → 结论边界`。
2. 先建立可复现基线，再用预注册证据购买额外复杂度。
3. 在看结果前冻结指标、阈值、切分、情景、种子和比较预算。
4. 只维护一个工作台账；其他工件保存专业细节，不重复承担真相。
5. 上游版本变化会让全部依赖结果、图表和主张变为 `stale`。
6. 验证失败时收缩结论、回退或停止，不用默认值和文字润色掩盖缺口。

主流程分为六个阶段：合同、题意与数据、规格与选型、实现与实验、证伪与稳健性、论文与提交。阶段推进依赖可判定的 `GateSpec`，不是“文档已经写完”。

## 安装

将与 skill 名同名的目录复制到 Codex skills 目录：

```bash
cp -R competition-mathematical-modeling-workflow "${CODEX_HOME:-$HOME/.codex}/skills/"
```

安装后的入口是：

```text
competition-mathematical-modeling-workflow/SKILL.md
```

也可在其他 Agent 或人工团队中直接读取该目录；核心协议不依赖特定模型、连接器或云服务。

## 结构

```text
competition-mathematical-modeling-workflow/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── artifact-contracts.md
│   ├── model-selection-atlas.md
│   ├── verification-and-repair.md
│   ├── residual-autocorrelation.md
│   ├── simulation-uncertainty-experiments.md
│   ├── tool-enhanced-execution.md
│   └── ...
└── assets/templates/
    ├── workflow-ledger.md
    ├── model-evidence-pack.md
    ├── tool-evidence-log.md
    └── paper-and-submission templates
```

仓库根目录的 `tests/` 是结构契约、负例和 AirPassengers 示例；`vendor/` 是仓库级第三方来源，不会随可安装 skill 递归发现。

## 关键设计变化

- 使用 `workflow-ledger.md` 统一任务、版本、GateSpec、决策、运行、结果和主张。
- 使用 `admitted / conditional / exploratory / rejected` 管理候选；硬约束、数据、验证与资源是 veto，不用主观总分决定模型。
- 按任务类型强制最低验证组合；不能用“任选三项”跳过时间切分、可行性、多种子或权重稳定性。
- 把最终测试隔离到冻结选择之后；最终结果只能确认或否定主张，不能用于重选。
- 仅在多轮修复、跨会话恢复或预算化搜索时启动 Agent Loop；一次工具调用不触发完整循环。
- 分离阶段决策与最终 outcome，避免 `stop` 同时表示成功和失败。

## 校验与测试

零依赖结构校验：

```bash
python3 tests/test_skill_contract.py
```

AirPassengers 脚本需要 NumPy、pandas 和 Matplotlib：

```bash
python3 -m pip install -r tests/requirements.txt
python3 tests/run_workflow_test.py
python3 tests/run_residual_autocorrection_test.py
```

统计案例只验证有限实现与选择纪律，不证明该 skill 对所有题型有效。仓库中的负例测试负责检查：诊断未触发时不生成修正、季节候选需要季节信号和足够历史、残差仍越界时不得接受、最终 holdout 不进入训练内选择。

## 第三方来源边界

可安装目录中的工作流、参考与模板为本仓库原创内容。仓库另在 [`vendor/mathhub/`](vendor/mathhub/) 保留 MathHub 上游原样材料，供明确的源码研究使用；它们不属于可安装 skill，并受 [`NOTICE.md`](vendor/mathhub/NOTICE.md) 与 [`upstream/LICENSE.txt`](vendor/mathhub/upstream/LICENSE.txt) 的单独许可约束。

设计来源和重写边界见 [`docs/design-provenance.md`](docs/design-provenance.md)。任何当前赛事格式、匿名、工具使用和提交规则都必须回读当届官方文件；本仓库不承诺获奖、生产可靠性或特定平台兼容性。
