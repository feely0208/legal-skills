#!/usr/bin/env python3
"""证据目录Markdown生成器 —— 将JSON证据目录转为Markdown格式(.md)。"""

import json
import argparse
import os
from datetime import datetime


def generate_markdown(data, output_path):
    """生成Markdown格式证据目录"""
    evidence_items = data.get("evidence_items", [])
    summary = data.get("summary", {})
    date_str = datetime.now().strftime("%Y年%m月%d日")

    lines = []

    # Title
    lines.append(f"# {data.get('title', '证据目录')}")
    lines.append("")

    # Case info
    lines.append("## 案件信息")
    lines.append("")
    lines.append(f"| 项目 | 内容 |")
    lines.append(f"|------|------|")
    lines.append(f"| 案号 | {data.get('case_number', '—')} |")
    lines.append(f"| 审理法院 | {data.get('court', '—')} |")
    lines.append(f"| 提交人 | {data.get('party_name', '—')}（{data.get('submitting_party', '—')}） |")
    if data.get("agent_name"):
        lines.append(f"| 代理人 | {data.get('agent_name', '')} |")
    lines.append(f"| 提交日期 | {data.get('submission_date', date_str)} |")
    if data.get("contact_phone"):
        lines.append(f"| 联系电话 | {data.get('contact_phone', '')} |")
    lines.append("")

    # Evidence overview
    lines.append("## 证据概况")
    lines.append("")
    lines.append(f"- **证据总数**：{summary.get('total_items', 0)} 项")
    lines.append(f"- **合计页数**：{summary.get('total_pages', 0)} 页")
    lines.append(f"- **原件**：{summary.get('original_count', 0)} 份　|　**复印件**：{summary.get('copy_count', 0)} 份")
    types = summary.get("evidence_types_used", [])
    if types:
        lines.append(f"- **证据类型**：{'、'.join(types)}")

    facts = summary.get("main_facts", [])
    if facts:
        lines.append("")
        lines.append("### 主要证明事项")
        lines.append("")
        for f in facts:
            lines.append(f"- {f}")

    notes = summary.get("notes", "")
    if notes:
        lines.append("")
        lines.append(f"> {notes}")
    lines.append("")

    # Evidence catalog table
    lines.append("## 证据目录")
    lines.append("")
    lines.append("| 序号 | 证据名称 | 证据类型 | 证据来源 | 页数 | 份数 | 原件/复印件 | 证明对象/证明目的 | 备注 |")
    lines.append("|------|---------|---------|---------|------|------|-----------|----------------|------|")

    for item in evidence_items:
        is_orig = "原件" if item.get("is_original", False) else "复印件"
        row = [
            str(item.get("id", "")),
            item.get("evidence_name", ""),
            item.get("evidence_type", ""),
            item.get("evidence_source", ""),
            str(item.get("pages", "")),
            str(item.get("copies", "")),
            is_orig,
            item.get("proof_purpose", "").replace("\n", "<br>"),
            item.get("remarks", ""),
        ]
        lines.append("| " + " | ".join(row) + " |")

    lines.append("")

    # Evidence details (one section per item)
    lines.append("---")
    lines.append("")
    lines.append("## 逐项证据详情")
    lines.append("")

    for item in evidence_items:
        idx = item.get("id", "")
        name = item.get("evidence_name", "")
        is_orig = "原件" if item.get("is_original", False) else "复印件"

        lines.append(f"### 证据{idx}：{name}")
        lines.append("")
        lines.append(f"| 属性 | 内容 |")
        lines.append(f"|------|------|")
        lines.append(f"| 证据类型 | {item.get('evidence_type', '—')} |")
        lines.append(f"| 证据来源 | {item.get('evidence_source', '—')} |")
        lines.append(f"| 页数 | {item.get('pages', '—')} |")
        lines.append(f"| 份数 | {item.get('copies', '—')} |")
        lines.append(f"| 原件/复印件 | {is_orig} |")
        lines.append(f"| 证明目的 | {item.get('proof_purpose', '—')} |")
        remarks = item.get("remarks", "")
        if remarks:
            lines.append(f"| 备注 | {remarks} |")
        lines.append("")

    # Certification
    lines.append("---")
    lines.append("")
    lines.append("## 提交人声明")
    lines.append("")
    cert = data.get("certification", "以上证据材料经本人核对，复印件与原件一致。")
    lines.append(f"> {cert}")
    lines.append("")
    lines.append("**提交人（签名/盖章）：** ________________")
    lines.append("")
    if data.get("agent_name"):
        lines.append("**代理人（签名）：** ________________")
        lines.append("")
    lines.append("**提交日期：** ______年______月______日")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(f"*本文件由AI法律证据系统生成，仅供律师参考。建议经执业律师复核后使用。*")
    lines.append(f"*生成时间：{date_str}*")

    content = "\n".join(lines)

    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


def main():
    parser = argparse.ArgumentParser(description="证据目录Markdown生成器")
    parser.add_argument("--input", "-i", required=True, help="证据目录JSON文件路径")
    parser.add_argument("--output", "-o", required=True, help="输出Markdown文件路径(.md)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"错误：找不到输入文件 —— {args.input}")
        return 1

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSON解析错误：{e}")
        return 1

    path = generate_markdown(data, args.output)
    print(f"Markdown证据目录已生成：{path}")
    return 0


if __name__ == "__main__":
    exit(main())
