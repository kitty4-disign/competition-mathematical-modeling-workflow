# MathHub 上游组件通知

本目录包含从 [AI-Dog-Creater/MathHub](https://github.com/AI-Dog-Creater/MathHub) **原样复制**的有限上游组件，源修订为 [`7ac101d2abb3769f6d3bc020e87a67cb6c539263`](https://github.com/AI-Dog-Creater/MathHub/tree/7ac101d2abb3769f6d3bc020e87a67cb6c539263)。

> Required Notice: Copyright 2026 AI-Dog-Creater.

## 许可证与使用边界

上游组件受 [PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0) 约束；完整许可证文本位于 [`upstream/LICENSE.txt`](./upstream/LICENSE.txt)。该许可证允许非商业用途下的使用、修改和分发，但要求向接收者提供许可证或其 URL，以及上述 Required Notice。它**不授予商业用途、再许可或转让权利**。

本技能包的其他原创内容不改变上游组件的许可证。使用、修改、分发或将本技能包用于任何可能具有商业目的的场景前，应由使用者核验自身用途和分发方式是否满足上游许可证与其他适用权利要求。

## 已纳入内容

| 类别 | 上游路径 | 用途 | 状态 |
|---|---|---|---|
| 原文工作流 | `upstream/src/skills/*/SKILL.md` | 数模任务拆解、数据、建模、预测、仿真、验证、可视化和论文生产的上游原文。 | 原样保留，按需阅读。 |
| 原始格式模板 | `upstream/src/skills/write-*/references/*.md` | MCM、HiMCM 与中文数模论文的上游格式和数据源表。 | 原样保留，仅在赛事/题型匹配并已核验当届规则时参考。 |
| 提示描述 | `upstream/src/skills/*/agents/openai.yaml` | 上游技能的调用提示描述。 | 原样保留；不代表当前环境支持其上游工具。 |
| 代码 | `upstream/python-approval.ts` | 对 Python 入口、文件哈希、参数和超时建立一次性审批令牌的 Node.js/TypeScript 实现。 | 原样保留；不会自动执行。 |

## 排除内容

未纳入 MathHub 的完整 React/Node 应用、`agent-runtime.ts`、文档导出器、`mcp-client.ts`、应用依赖、MCP 配置、媒体资产、竞赛封面、环境变量、外部 API 集成和 `nature-skills-main` 研究包。`src/skills/write-himcm-paper/16226.docx` 也被排除，因为其上游权属/来源无法在本次审计中确认。

## 使用规则

1. 先读取当前技能的主工作流和赛事画像；上游原文是补充资源，不覆盖当前技能的证据、审计、安全或竞赛规则要求。
2. 读取对应上游组件前，检查其适用比赛、页数、字体、引用、队号和文件格式要求是否仍由本届官方规则支持。
3. 不要执行上游代码、提示中提到的工具或外部服务，除非当前环境已经具备相应能力，且已完成工具预检与用户授权。
4. 若再分发本目录的任何上游文件，必须一并提供本 `NOTICE.md` 与 `upstream/LICENSE.txt`，并保留上述版权通知。
