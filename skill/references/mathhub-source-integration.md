# MathHub 上游源码、原文与模板接入指南

## 使用前必读

本参考用于需要查阅本技能包中随附的 MathHub 上游代码、原文工作流或赛事格式模板时。先阅读 [`../third_party/mathhub/NOTICE.md`](../third_party/mathhub/NOTICE.md) 和 [`../third_party/mathhub/upstream/LICENSE.txt`](../third_party/mathhub/upstream/LICENSE.txt)，并确认用途与分发满足 **PolyForm Noncommercial 1.0.0** 的限制。

上游组件位于 `third_party/mathhub/upstream/`，按原路径保留。它们是补充资源，不替代当前技能的模型证据包、工具日志、独立验证、自然表达审阅或当届官方规则。上游格式与当前赛事规则冲突时，以官方规则为准。

## 原文工作流路由

| 当前任务 | 先使用的当前资源 | 可补充读取的 MathHub 上游原文 |
|---|---|---|
| 多问赛题拆解、依赖、交付物 | `modular-task-routing.md` | `src/skills/frame-contest-problem/SKILL.md` |
| 数据质量与预处理 | `deliverables.md`、`tool-enhanced-execution.md` | `src/skills/audit-modeling-data/SKILL.md`、`explore-modeling-data/SKILL.md` |
| 模型选择、方程和参数 | `model-selection-atlas.md`、模型证据包 | `src/skills/design-mathematical-model/SKILL.md` |
| 优化、预测或不确定性 | `verification-and-repair.md`、`simulation-uncertainty-experiments.md` | `solve-optimization-model/SKILL.md`、`forecast-time-series/SKILL.md`、`simulate-uncertainty/SKILL.md` |
| 稳健性与图表 | 图表/附录模板、证据包 | `validate-model-robustness/SKILL.md`、`visualize-model-results/SKILL.md` |
| 指定比赛论文格式 | 当前赛事画像与提交清单 | `write-mcm-paper/`、`write-himcm-paper/` 或 `write-chinese-modeling-paper/` 下的原文和 `references/` 格式文件。 |

每次最多读取完成当前子问题所需的 1–3 个上游资源。不得因为上游原文可用而跳过本技能的前置门槛，也不得把其示例性题型规则扩展到不匹配的赛事。

## 格式模板使用纪律

上游 `write-mcm-paper`、`write-himcm-paper` 与 `write-chinese-modeling-paper` 原文及其 `references/*.md` 只在用户明确要求相应赛事或格式时读取。使用前，逐项核验纸张、页边距、匿名方式、页数、首页、引用、队号、字体、附录、提交文件和当届规则；未被官方文件确认的格式不能写入最终稿。

上游 `agents/openai.yaml` 是原始提示描述，不是当前环境的可执行接口。不要将其解释为当前拥有同名命令、模型、导出器或工具权限。

## 上游 Python 审批代码

`third_party/mathhub/upstream/python-approval.ts` 提供一个**上游原始 TypeScript 源文件**：它将入口点、文件路径/哈希、参数和超时组成规范化清单，签发短时一次性令牌，并在执行前校验令牌、清单哈希和过期状态。

本技能包不自动编译、安装或执行该文件。若用户在另一个 Node.js/TypeScript 项目中明确需要采用它，应先完成以下检查：

1. 由人工审阅源代码、Node 版本与 `crypto` 依赖，并确认运行环境隔离、网络和子进程限制。
2. 将批准清单绑定到已审阅的项目文件与输入版本；任何入口、文件、哈希、参数或超时变化都必须重新批准。
3. 将用户授权、令牌生命周期、运行日志和输出工件记录在现有 `tool-evidence-log.md` 中。
4. 在小型非敏感样例上测试；不要把令牌或密钥写入日志、论文、仓库或第三方服务。

## 原样组件与原创扩展的区分

`third_party/mathhub/upstream/` 下文件为上游原样内容，并受其许可证控制；本目录以外的工作流、模板和参考文件为本技能包已有或新增内容。修改上游文件时，应在同目录添加变更说明、保留来源路径与 Required Notice，并继续提供上游许可证文本。
