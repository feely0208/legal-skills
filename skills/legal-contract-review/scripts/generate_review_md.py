#!/usr/bin/env python3
"""合同审阅 Markdown 报告生成器。"""

import json
import os
import argparse
from datetime import datetime


COLOR_ICONS = {
    "red":    "🔴",
    "orange": "🟠",
    "blue":   "🔵",
    "green":  "🟢",
}

CATEGORY_LABELS = {
    "red":    "漏洞/缺陷",
    "orange": "风险提醒",
    "green":  "修改建议",
}


def generate_md(data, output_path):
    """生成 Markdown 审阅报告"""
    title = data.get("title", "合同审阅报告")
    contract_type = data.get("contract_type", "—")
    client = data.get("client_name", "—")
    review_date = data.get("review_date", datetime.now().strftime("%Y-%m-%d"))
    reviewer = data.get("reviewer", "—")
    summary = data.get("summary", {})
    findings = data.get("findings", [])

    lines = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f'**合同类型**：{contract_type} | **委托人**：{client} | **审阅日期**：{review_date} | **审阅人**：{reviewer}')
    lines.append("")
    lines.append("---")
    lines.append("")

    # 摘要
    lines.append("## 一、审阅摘要")
    lines.append("")
    overall = summary.get("overall_risk", "—")
    signability = summary.get("signability", "—")
    total = summary.get("total_issues", 0)
    rc = summary.get("red_count", 0)
    oc = summary.get("orange_count", 0)
    gc = summary.get("green_count", 0)

    risk_emoji = "🔴" if overall == "高" else "🟠" if overall == "中" else "🟢"
    lines.append(f"| 项目 | 内容 |")
    lines.append(f"|------|------|")
    lines.append(f"| 整体风险等级 | {risk_emoji} **{overall}** |")
    lines.append(f"| 签约可行性 | {signability} |")
    lines.append(f"| 发现问题总数 | {total} 项（🔴 {rc} 项漏洞 + 🟠 {oc} 项风险 + 🟢 {gc} 项建议）|")
    lines.append("")

    brief = summary.get("brief", "")
    if brief:
        lines.append(f"**整体评估**：{brief}")
        lines.append("")

    # 谈判底线
    bl = summary.get("bottom_lines", [])
    if bl:
        lines.append("### 谈判底线（必须坚持）")
        lines.append("")
        for b in bl:
            lines.append(f"- 🔴 **{b}**")
        lines.append("")

    ng = summary.get("negotiable", [])
    if ng:
        lines.append("### 可协商条款")
        lines.append("")
        for n in ng:
            lines.append(f"- 🟠 {n}")
        lines.append("")

    mr = summary.get("max_risk", "")
    if mr:
        lines.append(f"**最不利风险敞口**：{mr}")
        lines.append("")

    lt = summary.get("litigation_trend", "")
    if lt:
        lines.append(f"**类案裁判趋势**：{lt}")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 风险汇总表
    lines.append("## 二、风险汇总表")
    lines.append("")
    lines.append("| 序号 | 类别 | 涉及条款 | 问题概述 | 风险等级 | 紧急程度 |")
    lines.append("|------|------|---------|---------|---------|---------|")
    for f in findings:
        cat_icon = COLOR_ICONS.get(f.get("category", "green"), "🟢")
        lines.append(f'| {f.get("id", "")} | {cat_icon} {CATEGORY_LABELS.get(f.get("category", ""), "")} | {f.get("clause", "")} | {f.get("title", "")} | {f.get("risk_level", "")} | {f.get("urgency", "")} |')
    lines.append("")

    lines.append("---")
    lines.append("")

    # 逐条审阅意见
    lines.append("## 三、逐条审阅意见")
    lines.append("")

    lines.append("> **颜色图例**：🔴 漏洞/缺陷 | 🟠 风险提醒 | 🔵 法律依据 | 🟢 修改建议")
    lines.append("")

    for f in findings:
        idx = f.get("id", "")
        cat = f.get("category", "green")
        icon = COLOR_ICONS.get(cat, "🟢")
        label = CATEGORY_LABELS.get(cat, "")

        lines.append(f"### {icon} 第{idx}条：{f.get('title', '')} 【{label}】")
        lines.append("")

        lines.append(f'**涉及条款**：{f.get("clause", "—")}')
        lines.append("")

        orig = f.get("original_text", "")
        if orig:
            lines.append(f'**原条款内容**：')
            lines.append("")
            lines.append(f'> {orig}')
            lines.append("")

        desc = f.get("description", "")
        if desc:
            lines.append(f'**问题分析**：')
            lines.append("")
            lines.append(desc)
            lines.append("")

        legal = f.get("legal_basis", "")
        if legal:
            lines.append(f'**🔵 法律依据**：')
            lines.append("")
            for line in legal.split("\n"):
                line = line.strip()
                if line:
                    lines.append(f'> {line}')
            lines.append("")

        case_ref = f.get("case_reference", "")
        if case_ref:
            lines.append(f'**🔵 参考案例**：')
            lines.append("")
            for line in case_ref.split("\n"):
                line = line.strip()
                if line:
                    lines.append(f'> {line}')
            lines.append("")

        suggestion = f.get("suggestion", "")
        if suggestion:
            lines.append(f'**🟢 修改建议**：')
            lines.append("")
            lines.append(suggestion)
            lines.append("")

        revised = f.get("revised_text", "")
        if revised:
            lines.append(f'**🟢 建议修改后文本**：')
            lines.append("")
            for line in revised.split("\n"):
                line = line.strip()
                if line:
                    lines.append(f'> {line}')
            lines.append("")

        lines.append(f'**风险等级**：{f.get("risk_level", "—")}　|　**紧急程度**：{f.get("urgency", "—")}')
        lines.append("")
        lines.append("---")
        lines.append("")

    # 页脚
    lines.append("")
    lines.append("---")
    lines.append(f'*本报告由AI法律审阅系统生成，生成时间：{datetime.now().strftime("%Y年%m月%d日 %H:%M")}，仅供律师参考，不构成正式法律意见。*')

    content = '\n'.join(lines)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return output_path


def main():
    parser = argparse.ArgumentParser(description='合同审阅 Markdown 报告生成器')
    parser.add_argument('--input', '-i', required=True, help='审阅JSON文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出Markdown文件路径')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    path = generate_md(data, args.output)
    print(f"Markdown报告已生成: {path}")
    return 0


if __name__ == '__main__':
    exit(main())
