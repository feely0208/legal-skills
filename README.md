# 深鲸法律技能集 · DeepWhale Legal Skills

**给中国律师和法务用的 AI 技能包。本地运行、文书可交付、引用可核验。**

32 个技能，覆盖法律检索与核验、诉讼文书、证据与阅卷、合同与非诉、家事劳动、企业合规，以及最后的排版交付。
兼容 Claude Code / Codex / Cursor / DSH 等任何支持 `SKILL.md` 的 Agent。

> 我们不做「AI 律师」，只做律师手里的工具。所有输出都是草稿，须由承办律师复核后使用。

---

## 为什么是这一套

市面上不缺法律 AI 产品，缺的是**能装进你自己的工作流、并且不替你编法条**的技能。这套技能的取舍：

| 我们做 | 我们不做 |
|---|---|
| 本地运行，案卷不出本机 | 上传到云端模型做「智能问答」 |
| 每个结论给依据（条号/条款/证据编号） | 只给一段没有出处的结论 |
| 引用核验：失效法条、越界条号、被取代的解释直接标红 | 把「没查到」说成「没问题」 |
| 输出能直接交付的 .docx / .pdf | 只给 Markdown 让你自己排版 |
| 明确标注「AI 辅助生成，需律师复核」 | 声称可以替代律师 |

## 32 个技能

### 检索与核验

| 技能 | 做什么 |
|---|---|
| `legal-cite-check` 引用核验 | 抽取全部法条/法释/案号，查失效旧法、越界条号、被取代解释 |
| `legal-research` 法律检索报告 | 按「法律—行政法规—司法解释—地方规定—案例」效力层级出报告 |
| `legal-statute-lookup` 法条速查 | 按法名/条号/关键词定位常用法条要点，离线可用 |

### 诉讼文书

| 技能 | 做什么 |
|---|---|
| `legal-complaint` 起诉状 | 民事/行政起诉状，自动判断原被告立场 |
| `legal-defense-statement` 答辩状 | 针对起诉状逐项回应，程序/实体/证据三层抗辩 |
| `legal-lawyer-letter` 律师函 | 催告、解除、侵权警告、催收，附送达与留痕 |
| `legal-appeal` 上诉状 | 读一审判决，按事实/法律/程序三类错误写上诉 |
| `legal-preservation` 财产保全申请 | 诉前/诉中保全，附担保方案与错误保全风险 |
| `legal-enforcement` 强制执行申请 | 执行申请书、财产线索表、执行策略 |

### 证据与阅卷

| 技能 | 做什么 |
|---|---|
| `legal-evidence-chain` 证据链时间线 | 材料 → 时间线 → 待证事实映射 → 缺口清单 |
| `legal-evidence-catalog` 证据目录 | 法院标准证据目录与证明目的 |
| `legal-evidence-examination` 质证意见 | 围绕证据三性逐份质证 |
| `legal-evidence-review-notes` 阅卷笔录 | 全案卷结构化梳理 |
| `legal-document-review` 阅卷辅助 | 单份材料快速分析与证据链核对 |

### 合同与非诉

| 技能 | 做什么 |
|---|---|
| `legal-contract-review` 合同审阅 | 四色标记风险 + 可直接替换的修改文本 |
| `legal-contract-drafting` 合同草拟 | 10 大类合同起草与条款补全 |
| `legal-due-diligence` 尽职调查清单 | 按交易类型出模块化清单与红旗信号 |
| `legal-opinion` 法律意见书 | 事实、依据、分析、结论、保留 |

### 可视化与推演（专有）

| 技能 | 做什么 |
|---|---|
| `legal-litigation-viz` 诉讼可视化 | 案情 JSON → 时间轴/法律关系图/证据矩阵/争点对照，单文件 HTML |
| `legal-claim-chart` 类案争点对比表 | 2–5 份判决按「争点 × 判决」拆矩阵，识别真冲突与假冲突 |
| `legal-moot-court` 庭审模拟 | 法官十问、对方最强攻击点、己方发问提纲、庭前流程表 |
| `legal-damages-calc` 损害赔偿计算器 | 人身损害/劳动/利息/违约金逐项套公式，可手算复核 |

### 律协专委（治理工具）

| 技能 | 做什么 |
|---|---|
| `bar-committee-workplan` 专委年度计划与分工 | 八项职责拆任务、季度排期、角色分工、成果指标 |
| `bar-committee-guideline` 业务操作指引编写 | 固定篇章体例 + 起草说明 + 征求意见表 |
| `bar-committee-case-review` 优秀案例征集与评选 | 五维评分表、评审意见、公示稿、回避保密 |
| `bar-committee-training` 专委培训与沙龙 | 需求→课程→讲师→执行→评估六步 |
| `bar-committee-legislative` 立法建议与征求意见 | 逐条意见表 + 建议函 + 分歧汇总 |

### 家事、劳动与合规

| 技能 | 做什么 |
|---|---|
| `legal-divorce-agreement` 离婚协议 | 子女、财产、债务、违约全套 |
| `legal-labor-arbitration` 劳动仲裁申请 | 请求计算、证据清单、开庭要点 |
| `legal-compliance-check` 用工合规体检 | 八模块缺口与整改优先级 |

### 排版与演示

| 技能 | 做什么 |
|---|---|
| `chinese-doc-formatter` 中文文书排版 | 按 GB/T 9704-2012 输出 .docx / .pdf / .txt |
| `legal-kb-presentation` 知识库演示 | 生成演示 PPT 与页面 |

## 安装

### Claude Code

```bash
git clone https://github.com/feely0208/legal-skills.git ~/legal-skills
bash ~/legal-skills/install.sh --target ~/.claude/skills
```

### OpenAI Codex

```bash
bash ~/legal-skills/install.sh --target ~/.codex/skills
```

### Cursor / 其他 Agent

```bash
bash ~/legal-skills/install.sh --target <你的技能目录>
```

### DSH（深鲸桌面）

在插件市场搜索「深鲸法律技能集」，或：

```bash
npx @deepwhale-cn/dsh-legal-skills
```

### 可选：法条全文库（1,513 部）

随包只带 29 部常用法。要查票据法、海商法这类：

```bash
# 从官网下载 deepwhale-legal-corpus-2026.10.zip（约 6MB）
cp legal-corpus-2026.10/laws-full.json.gz skills/legal-statute-lookup/data/
python3 skills/legal-statute-lookup/scripts/lookup.py --list   # 显示「全量库 1,513 部」
```

数据来自 [chinese-law-corpus](https://github.com/lttxzmj/chinese-law-corpus)（CC0）。

### 只装一个技能

```bash
cp -r skills/legal-cite-check ~/.claude/skills/
```

## 先试这一条：引用核验

```bash
python3 skills/legal-cite-check/scripts/check_citations.py 你的文书.md
```

会生成 `引用核验/` 目录：

- `citations.csv` — 逐条核验表（Excel 可开）
- `citations.md` — 带「必须处理 / 需人工核验」的报告
- `*.核验标注.md` — 在原位置标出问题引用

能查出：

- 引用已废止的《合同法》《婚姻法》《物权法》等 → 建议改引民法典对应条文；
- 条号越界（如民法典第 1300 条，民法典只有 1260 条）；
- 已被法释〔2020〕26号吸收的旧劳动争议解释；
- 条文序号因修订重排（公司法、民事诉讼法、行政处罚法）的提醒；
- 案号格式识别，并明确标注「离线无法核验」。

**它只对离线索引负责**：索引覆盖 1,513 部现行法规（chinese-law-corpus，CC0），之外的引用标「需人工核验」，不会假装通过。

## 法律档案（一次填写，所有技能共用）

```bash
mkdir -p ~/.deepwhale
cp templates/法律档案.md ~/.deepwhale/深鲸法律档案.md
```

填好角色、立场、地域、行文风格、风险偏好和升级链，所有技能都会先读它，不再反复问你。

## 目录结构

```
skills/<slug>/
  SKILL.md            # 触发条件、工作流、输出规范、质量闸门
  references/         # 检查清单、法条要点、计算口径
  fixtures/           # 验收样例（输入 + 期望结果）
  templates/          # 可填写模板（部分技能）
  scripts/            # 本地脚本（引用核验等）
templates/法律档案.md
install.sh
```

## 质量与边界

- 每个技能自带 fixtures，改技能必须先跑过样例；
- 引用核验只对索引负责，索引未收录一律标「需人工核验」；
- 不编法条、案号、金额、日期；缺失信息用【待补：xx】；
- 不做 C 端法律咨询，不承诺胜诉，不替代律师签字；
- 所有输出带「AI 辅助生成，需承办律师复核」标识。

## 许可与致谢

本项目以 **MIT License** 开源（见 [LICENSE](LICENSE)）。
设计上参考了若干公开项目的做法，逐项列在 [NOTICE.md](NOTICE.md)；未直接复制其代码。

## 免责声明

本仓库提供的是工作流、清单与辅助脚本，**不构成法律意见**，不能替代执业律师对具体案件的分析与判断。
使用者对基于本工具作出的任何决定自行承担责任。

---

<p align="right">
  <a href="https://deepwhale.org.cn"><img src="https://deepwhale.org.cn/assets/dwh-badge-121.png" alt="powered by dwh" height="20"></a>
</p>
