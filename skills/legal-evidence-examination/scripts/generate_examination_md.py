#!/usr/bin/env python3
"""质证意见 Markdown 报告生成器。"""

import json
import os
import argparse
from datetime import datetime


def verdict_emoji(verdict):
    if verdict == "认可":
        return "✅"
    elif verdict == "不认可":
        return "❌"
    else:
        return "⚠️"


def generate_md(data, output_path):
    """生成 Markdown 质证意见书"""
    title = data.get("title", "质证意见书")
    case_number = data.get("case_number", "—")
    court = data.get("court", "—")
    examiner_party = data.get("examiner_party", "—")
    examiner_role = data.get("examiner_role", "plaintiff")
    role_label = "原告" if examiner_role == "plaintiff" else "被告"
    examiner_name = data.get("examiner_name", "—")
    submission_date = data.get("submission_date", datetime.now().strftime("%Y年%m月%d日"))
    summary = data.get("summary", {})
    evidence_items = data.get("evidence_items", [])

    lines = []
    lines.append(f"# 质证意见书")
    lines.append("")
    lines.append(f"## {title}")
    lines.append("")
    lines.append(f"| 项目 | 内容 |")
    lines.append(f"|------|------|")
    lines.append(f"| 案号 | {case_number} |")
    lines.append(f"| 审理法院 | {court} |")
    lines.append(f"| 质证人 | {examiner_party}（{role_label}） |")
    lines.append(f"| 代理人 | {examiner_name} |")
    lines.append(f"| 提交日期 | {submission_date} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 总体质证意见
    lines.append("## 一、总体质证意见")
    lines.append("")

    total = summary.get("total_evidence", 0)
    ok_count = summary.get("no_objection_count", 0)
    partial_count = summary.get("partial_objection_count", 0)
    full_count = summary.get("full_objection_count", 0)

    lines.append(f"对方共提交证据 **{total}** 份。")
    lines.append("")
    lines.append(f"| 意见类型 | 数量 |")
    lines.append(f"|---------|------|")
    lines.append(f"| ✅ 无异议 | {ok_count} 份 |")
    lines.append(f"| ⚠️ 部分异议 | {partial_count} 份 |")
    lines.append(f"| ❌ 完全异议 | {full_count} 份 |")
    lines.append("")

    overall = summary.get("overall_assessment", "")
    if overall:
        lines.append(f"**整体评价**：{overall}")
        lines.append("")

    issues = summary.get("main_issues", [])
    if issues:
        lines.append("### 对方证据体系主要问题")
        lines.append("")
        for item in issues:
            lines.append(f"- ❌ {item}")
        lines.append("")

    weaknesses = summary.get("key_weaknesses", [])
    if weaknesses:
        lines.append("### 对方证据关键缺陷")
        lines.append("")
        for item in weaknesses:
            lines.append(f"- ⚠️ {item}")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 证据质证汇总表
    lines.append("## 二、证据质证汇总表")
    lines.append("")
    lines.append("| 编号 | 证据名称 | 类型 | 真实性 | 合法性 | 关联性 | 证明目的 | 综合 |")
    lines.append("|------|---------|------|--------|--------|--------|---------|------|")

    for item in evidence_items:
        a = f'{verdict_emoji(item.get("authenticity_verdict", ""))} {item.get("authenticity_verdict", "")}'
        l = f'{verdict_emoji(item.get("legality_verdict", ""))} {item.get("legality_verdict", "")}'
        r = f'{verdict_emoji(item.get("relevance_verdict", ""))} {item.get("relevance_verdict", "")}'
        p = f'{verdict_emoji(item.get("purpose_verdict", ""))} {item.get("purpose_verdict", "")}'
        o = f'{verdict_emoji(item.get("overall_verdict", ""))} {item.get("overall_verdict", "")}'
        lines.append(f'| {item.get("id", "")} | {item.get("evidence_name", "")} | {item.get("evidence_type", "")} | {a} | {l} | {r} | {p} | {o} |')
    lines.append("")

    lines.append("---")
    lines.append("")

    # 逐份质证意见
    lines.append("## 三、逐份质证意见")
    lines.append("")
    lines.append("> **图例**：❌ 不认可 | ⚠️ 无法确认 | ✅ 认可")
    lines.append("")

    for item in evidence_items:
        idx = item.get("id", "")
        lines.append(f"### 证据{idx}：{item.get('evidence_name', '')}")
        lines.append("")
        lines.append(f'**证据类型**：{item.get("evidence_type", "—")}')
        lines.append("")

        purpose = item.get("proof_purpose", "")
        if purpose:
            lines.append(f'**举证方证明目的**：')
            lines.append("")
            lines.append(f'> {purpose}')
            lines.append("")

        # 三性审查
        lines.append("#### 一、真实性审查")
        v = verdict_emoji(item.get("authenticity_verdict", ""))
        lines.append(f'**{v} {item.get("authenticity_verdict", "无法确认")}**')
        txt = item.get("authenticity_opinion", "")
        if txt:
            lines.append("")
            lines.append(txt)
        txt = item.get("authenticity_basis", "")
        if txt:
            lines.append("")
            lines.append(f'**法律依据**：{txt}')
        lines.append("")

        lines.append("#### 二、合法性审查")
        v = verdict_emoji(item.get("legality_verdict", ""))
        lines.append(f'**{v} {item.get("legality_verdict", "无法确认")}**')
        txt = item.get("legality_opinion", "")
        if txt:
            lines.append("")
            lines.append(txt)
        txt = item.get("legality_basis", "")
        if txt:
            lines.append("")
            lines.append(f'**法律依据**：{txt}')
        lines.append("")

        lines.append("#### 三、关联性审查")
        v = verdict_emoji(item.get("relevance_verdict", ""))
        lines.append(f'**{v} {item.get("relevance_verdict", "无法确认")}**')
        txt = item.get("relevance_opinion", "")
        if txt:
            lines.append("")
            lines.append(txt)
        txt = item.get("relevance_basis", "")
        if txt:
            lines.append("")
            lines.append(f'**法律依据**：{txt}')
        lines.append("")

        lines.append("#### 四、对证明目的的意见")
        txt = item.get("purpose_rebuttal", "")
        if txt:
            lines.append("")
            lines.append(txt)
        lines.append("")

        txt = item.get("case_reference", "")
        if txt:
            lines.append("**参考案例**：")
            lines.append("")
            for line in txt.split("\n"):
                line = line.strip()
                if line:
                    lines.append(f'> {line}')
            lines.append("")

        txt = item.get("overall_opinion", "")
        if txt:
            lines.append(f'**综合意见**：**{txt}**')
        lines.append("")
        lines.append("---")
        lines.append("")

    # 结论
    lines.append("## 四、结论")
    lines.append("")
    conclusion = summary.get("conclusion", "")
    if conclusion:
        lines.append(conclusion)
        lines.append("")

    lines.append("**综上所述，恳请人民法院依法审核认定上述证据，对对方提交的存在瑕疵的证据不予采信，依法公正裁判。**")
    lines.append("")
    lines.append(f"此致<br>{court}")
    lines.append("")
    lines.append(f"质证人（签名）：  ")
    lines.append(f"代理人（签名）：  ")
    lines.append(f"日期：  ")
    lines.append("")

    lines.append("---")
    lines.append(f'*本文件由AI法律质证系统生成，生成时间：{datetime.now().strftime("%Y年%m月%d日 %H:%M")}，仅供律师参考，不构成正式法律意见。*')

    content = '\n'.join(lines)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return output_path


def main():
    parser = argparse.ArgumentParser(description='质证意见 Markdown 报告生成器')
    parser.add_argument('--input', '-i', required=True, help='质证JSON文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出Markdown文件路径')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    path = generate_md(data, args.output)
    print(f"Markdown报告已生成: {path}")
    return 0


if __name__ == '__main__':
    exit(main())
