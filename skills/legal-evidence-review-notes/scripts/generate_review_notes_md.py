#!/usr/bin/env python3
"""阅卷笔录 Markdown 报告生成器。"""

import json
import os
import argparse
from datetime import datetime


def generate_md(data, output_path):
    """生成 Markdown 阅卷笔录"""
    title = data.get("title", "阅卷笔录")
    summary = data.get("summary", {})

    lines = []

    # 标题
    lines.append(f"# 阅卷笔录")
    lines.append("")
    lines.append(f"## {title}")
    lines.append("")
    lines.append("> **【内部工作文件 · 注意保密】**")
    lines.append("")

    # 核心事实摘要
    facts = summary.get("core_facts", "")
    if facts:
        lines.append("## 核心事实摘要")
        lines.append("")
        lines.append(facts)
        lines.append("")

    lines.append("---")
    lines.append("")

    # 一、案件基本信息
    lines.append("## 一、案件基本信息")
    lines.append("")
    fields = [
        ("案号", data.get("case_number", "—")),
        ("审理法院", data.get("court", "—")),
        ("案由", data.get("case_cause", "—")),
        ("审理阶段", data.get("trial_stage", "—")),
        ("审理程序", data.get("trial_procedure", "—")),
        ("开庭情况", data.get("court_hearing", "—")),
        ("原告", data.get("plaintiff_name", "—")),
        ("被告", data.get("defendant_name", "—")),
    ]
    third = data.get("third_parties", [])
    if third:
        fields.append(("第三人", "、".join(third)))

    role_label = "原告" if data.get("reviewer_role") == "plaintiff" else "被告"
    fields += [
        ("阅卷人", f'{data.get("reviewer_name", "—")}（{role_label}方代理人）'),
        ("所在律所", data.get("reviewer_firm", "—")),
        ("阅卷日期", data.get("review_date", datetime.now().strftime("%Y年%m月%d日"))),
    ]

    for label, value in fields:
        lines.append(f"| **{label}** | {value} |")
    lines.append("")

    lines.append("---")
    lines.append("")

    # 二、案卷材料概况
    lines.append("## 二、案卷材料概况")
    lines.append("")
    total = summary.get("total_documents", 0)
    cats = summary.get("document_categories", {})
    lines.append(f"案卷材料共计 **{total}** 份。")
    lines.append("")
    for cat_name, count in cats.items():
        lines.append(f"- **{cat_name}**：{count} 份")
    lines.append("")

    # 三、案件大事记
    lines.append("## 三、案件大事记")
    lines.append("")
    events = summary.get("key_events", [])
    if events:
        lines.append("| 时间 | 事件 | 来源 |")
        lines.append("|------|------|------|")
        for ev in events:
            lines.append(f'| {ev.get("date", "")} | {ev.get("event", "")} | {ev.get("source", "")} |')
    else:
        lines.append("（暂无）")
    lines.append("")

    # 争议焦点
    disputes = summary.get("dispute_focus", [])
    if disputes:
        lines.append("### 预判争议焦点")
        lines.append("")
        for d in disputes:
            lines.append(f"- {d}")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 四、当事人主张对照
    comparisons = data.get("party_claims_comparison", [])
    if comparisons:
        lines.append("## 四、当事人主张对照分析")
        lines.append("")
        lines.append("| 争议事项 | 原告主张 | 被告主张 | 相关证据 | 分析意见 |")
        lines.append("|---------|---------|---------|---------|---------|")
        for comp in comparisons:
            row = [
                comp.get("issue", ""),
                comp.get("plaintiff_claim", ""),
                comp.get("defendant_claim", ""),
                comp.get("related_evidence", ""),
                comp.get("analysis", ""),
            ]
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 五、证据体系评估
    lines.append("## 五、证据体系评估")
    lines.append("")
    ea = summary.get("evidence_assessment", {})
    if ea:
        lines.append(f'- **原告方证据强度**：{ea.get("plaintiff_evidence_strength", "—")}')
        lines.append(f'- **被告方证据强度**：{ea.get("defendant_evidence_strength", "—")}')
        lines.append("")
        gaps = ea.get("key_gaps", [])
        if gaps:
            lines.append("### 关键证据缺口")
            lines.append("")
            for g in gaps:
                lines.append(f"- ⚠️ {g}")
            lines.append("")
    lines.append("")

    # 六、法律适用分析
    lines.append("## 六、法律适用分析")
    lines.append("")
    la = summary.get("legal_analysis", {})
    if la:
        claim = la.get("claim_basis", "")
        if claim:
            lines.append(f"**请求权基础**：{claim}")
            lines.append("")

        defenses = la.get("defense_anticipated", [])
        if defenses:
            lines.append("**预期抗辩事由**：")
            lines.append("")
            for d in defenses:
                lines.append(f"- {d}")
            lines.append("")

        cases = la.get("relevant_cases", [])
        if cases:
            lines.append("**参考案例**：")
            lines.append("")
            for c in cases:
                lines.append(f"> {c}")
            lines.append("")

    lines.append("---")
    lines.append("")

    # 七、程序事项核查
    checklist = data.get("procedure_checklist", [])
    if checklist:
        lines.append("## 七、程序事项核查")
        lines.append("")
        lines.append("| 核查事项 | 状态 | 说明 |")
        lines.append("|---------|------|------|")
        for item in checklist:
            lines.append(f'| {item.get("item", "")} | {item.get("status", "")} | {item.get("note", "")} |')
        lines.append("")

    lines.append("---")
    lines.append("")

    # 八、风险评估
    lines.append("## 八、风险评估")
    lines.append("")
    ra = summary.get("risk_assessment", {})
    if ra:
        risk_labels = {
            "fact_risk": "事实认定风险",
            "legal_risk": "法律适用风险",
            "evidence_risk": "证据风险",
            "procedure_risk": "程序风险",
            "enforcement_risk": "执行风险",
        }
        for key, label in risk_labels.items():
            level = ra.get(key, "—")
            icon = "🔴" if level == "高" else "🟠" if level == "中" else "🟢"
            lines.append(f"- {icon} **{label}**：{level}")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 九、后续工作建议
    lines.append("## 九、后续工作建议")
    lines.append("")
    steps = summary.get("next_steps", [])
    if steps:
        for i, step in enumerate(steps, 1):
            lines.append(f"{i}. {step}")
    else:
        lines.append("（暂无）")
    lines.append("")

    lines.append("---")
    lines.append("")

    # 十、阅卷结论
    lines.append("## 十、阅卷结论")
    lines.append("")
    overall = summary.get("overall_conclusion", "")
    if overall:
        lines.append(overall)
        lines.append("")

    lines.append("---")
    lines.append("")

    # 签署栏
    lines.append("**阅卷人（签名）：** ________________")
    lines.append("")
    lines.append("**日期：** ______年______月______日")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f'*本文件由AI法律阅卷系统生成，为律师内部工作文件，受律师—当事人保密特权保护。*')
    lines.append(f'*生成时间：{datetime.now().strftime("%Y年%m月%d日 %H:%M")}*')

    content = '\n'.join(lines)

    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return output_path


def main():
    parser = argparse.ArgumentParser(description='阅卷笔录 Markdown 报告生成器')
    parser.add_argument('--input', '-i', required=True, help='阅卷JSON文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出Markdown文件路径')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    path = generate_md(data, args.output)
    print(f"Markdown阅卷笔录已生成: {path}")
    return 0


if __name__ == '__main__':
    exit(main())
