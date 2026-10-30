# 致谢与参考来源

本项目的技能、清单与脚本由温州深鲸智能科技有限公司编写，以 MIT License 发布。
在设计与方法论上参考了以下公开项目；**未直接复制其代码或大段文本**，如后续引入将在此逐项列明文件与来源。

| 项目 | 许可证 | 参考了什么 |
|---|---|---|
| [anthropics/claude-for-legal](https://github.com/anthropics/claude-for-legal) | Apache-2.0 | 实践档案（practice profile）先行的冷启动思路、输出分级与人工闸门、按执业领域组织技能的结构 |
| [attorneynate/legal-skills](https://github.com/attorneynate/legal-skills) | MIT | 引用核验拆成「引的文不存在」与「文存在但没这么说」两类问题的思路；自测样例 + CI 校验的做法 |
| [Golden2002/legal-research-skill](https://github.com/Golden2002/legal-research-skill) | MIT | 法源效力层级、新旧法时效、引用格式三类校验的框架 |
| [evolsb/claude-legal-skill](https://github.com/evolsb/claude-legal-skill) | MIT | 合同审阅前的完整性检查（空白字段、缺失附件、签署状态）与立场感知审阅 |
| [zh-xx/legal-assistant-skills](https://github.com/zh-xx/legal-assistant-skills) | Apache-2.0 | 批注式合同审查（不改原文）与分层审查模型 |
| [anthropics/skills](https://github.com/anthropics/skills) | Apache-2.0 | SKILL.md 的目录与描述规范 |

## 数据来源

- 法条元数据（名称、别名、条文总数、失效关系）由本项目整理，核对日期 2026-10，正式引用以国家法律法规数据库（flk.npc.gov.cn）为准。
- 未引入 CUAD、LegalBench 等第三方数据集；如后续引入，将在对应技能目录单独标注其许可证（CUAD 为 CC BY 4.0）。

## 商标与名称

「深鲸」「DeepWhale」为温州深鲸智能科技有限公司的名称与标识。MIT 许可覆盖代码与文档，不授予商标使用权。
