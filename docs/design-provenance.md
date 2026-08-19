# 设计来源与整合边界

可安装目录 `competition-mathematical-modeling-workflow/` 中的工作流与模板为独立撰写，不包含第三方项目源码、模型权重或原文技能包。本 GitHub 仓库另在 `vendor/mathhub/` 保存一组 MathHub 上游原样文件；该目录不属于可安装 skill，并单独受其中的 `NOTICE.md` 与 `upstream/LICENSE.txt` 约束。下表说明原创 skill 吸收并重新组织的高层设计原则，不改变 vendor 文件的权利边界。

| 来源 | 吸收的高层原则 | 在本 Skill 中的落点 |
|---|---|---|
| MM-Agent | 将建模任务拆为问题分析、数学建模、计算求解和报告 | `SKILL.md` 的五阶段主流程 |
| OR-LLM-Agent 论文 | 将数学规格、代码实现和调试分层；反复代码修复失败后回溯模型规格 | `verification-and-repair.md` 的分层修复协议 |
| math-skills | 将数学过程产出为持久化文档；先做结构检查，再做语义审计，形成最小补丁并复验 | 证据矩阵、四层审计、审计输出与决策日志 |
| MCM/CUMCM 资料仓库 | 把模型、算法、论文结构和提交要件作为相互关联的交付物 | 论文模板、交付物模板、团队依赖图 |
| Wolfram Cloud MCP 文档 | 将计算能力用于可复核的精确/符号计算 | 工具增强规范中的计算核验与独立代入要求 |
| Exa MCP 文档 | 将检索能力用于发现、读取和带来源的研究输出 | 工具增强规范中的来源等级、URL 与日期记录要求 |
| E2B MCP 项目状态 | 不依赖已弃用或未维护的执行工具 | 受控执行优先与降级原则 |
| 长三角高校数学建模竞赛公开通知与 LaTeX 模板 | 摘要、问题分析、假设、符号、建模、评价、附录的论文交付逻辑 | 赛事画像、长三角风格论文草稿与合规模板 |
| 全国大学生数学建模竞赛 2026 格式规范 | 匿名、引用、支撑材料、代码与论文一致性检查 | 提交、匿名与引用终检模板 |
| 数学建模老哥公开视频《2026 数学建模国赛 AI 工作流全攻略》（BV15BgP6FEN9，第 1 分集） | 人先读题、候选方案比较、最小复现调试、工具权限最小化、AI 输出审计 | `references/ai-assisted-modeling.md` 与工具证据日志 AI/Agent 附录；不采纳其中赛事规则、产品能力、价格或获奖保证性表述 |
| 数学建模老哥公开视频《模型检验精讲课程》（BV16JgV6AEiE，第 2 分集） | 基准与参数范围、局部/全局灵敏度的取舍、步长/采样收敛检查、结果报告 | `references/verification-and-repair.md` 的灵敏度分析协议；仅采用通过章节—字幕一致性抽样的内容，不将软件名称或获奖表述作为事实 |
| 数学建模老哥公开视频《数学建模算法极限速成课》（BV1E5z4BKEnF） | 任务类型化、数据适配、预先定义诊断、AI/示例代码人工复核 | `references/model-selection-atlas.md` 的“候选生成与准入门禁”；不将具体算法清单、代码包或营销性主张直接当作推荐 |

## 外部资源

- MM-Agent：<https://github.com/usail-hkust/LLM-MM-Agent>
- OR-LLM-Agent：<https://arxiv.org/html/2503.10009v2>
- math-skills：<https://github.com/panpanc/math-skills>
- Mathematical Contest in Modeling 资料：<https://github.com/tinoryj/Mathematical-Contest-in-Modeling>
- Wolfram Cloud MCP：<https://www.wolfram.com/artificial-intelligence/mcp/cloud/>
- Exa MCP：<https://exa.ai/docs/reference/exa-mcp>
- E2B MCP 项目状态：<https://github.com/e2b-dev/mcp-server>
- 长三角高校数学建模竞赛公开通知：<https://m.saikr.com/YRDMCM26>
- 长三角高校数学建模竞赛公开 LaTeX 模板：<https://www.overleaf.com/latex/templates/2024-nian-di-si-jie-chang-san-jiao-gao-xiao-shu-xue-jian-mo-jing-sai-latex-mo-ban/rbghdtqjqvyh>
- 全国大学生数学建模竞赛 2026 论文格式规范：<https://www.mcm.edu.cn/html_cn/node/4cd596519c9eb9fbd866398f6df0caa3.html>
- 数学建模老哥公开视频（用户提供）：<https://www.bilibili.com/video/BV15BgP6FEN9>；整合依据为该公开视频第 1 分集的带时间戳 AI 字幕，获取于 2026-08-17。
- 数学建模老哥模型检验课程（用户提供账号内视频）：<https://www.bilibili.com/video/BV16JgV6AEiE?p=2>；整合依据为第 2 分集“灵敏度分析”的主题一致、带时间戳 AI 字幕，获取于 2026-08-17。
- 数学建模老哥算法课程（用户提供账号内视频）：<https://www.bilibili.com/video/BV1E5z4BKEnF>；整合依据为主题一致、带时间戳 AI 字幕，获取于 2026-08-17。

使用者如需运行外部项目，应自行获取原项目、审阅其当前许可证，并遵守数据、模型服务和竞赛规则。
