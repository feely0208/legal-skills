#!/usr/bin/env python3
"""起诉状 Markdown 报告生成器。"""

import json
import os
import argparse
from datetime import datetime


def format_party_md(party, label):
    """格式化当事人信息为Markdown"""
    if not party:
        return ""

    lines = []
    lines.append(f"**{label}**：")
    lines.append("")

    if party.get("type") == "company":
        lines.append(f"- 名称：{party.get('name', '—')}")
        if party.get("credit_code"):
            lines.append(f"- 统一社会信用代码：{party['credit_code']}")
        if party.get("address"):
            lines.append(f"- 住所地：{party['address']}")
        if party.get("legal_rep"):
            lines.append(f"- 法定代表人：{party['legal_rep']}")
        if party.get("phone"):
            lines.append(f"- 联系电话：{party['phone']}")
    else:
        lines.append(f"- 姓名：{party.get('name', '—')}")
        if party.get("gender"):
            lines.append(f"- 性别：{party['gender']}")
        if party.get("birth_date"):
            lines.append(f"- 出生日期：{party['birth_date']}")
        if party.get("ethnicity"):
            lines.append(f"- 民族：{party['ethnicity']}")
        if party.get("occupation"):
            lines.append(f"- 职业：{party['occupation']}")
        if party.get("address"):
            lines.append(f"- 住址：{party['address']}")
        if party.get("id_number"):
            lines.append(f"- 身份证号码：{party['id_number']}")
        if party.get("phone"):
            lines.append(f"- 联系电话：{party['phone']}")

    lines.append("")
    return "\n".join(lines)


def generate_md(data, output_path):
    """生成 Markdown 起诉状"""
    title = data.get("title", "民事起诉状")
    court = data.get("court", "—")
    case_brief = data.get("case_brief", "—")
    plaintiff = data.get("plaintiff", {})
    defendant = data.get("defendant", {})
    agent = data.get("agent", {})
    submission_date = data.get("submission_date",
                               datetime.now().strftime("%Y年%m月%d日"))
    claims = data.get("claims", [])
    facts = data.get("facts_and_reasons", {})

    lines = []

    # 标题
    lines.append(f"# {title}")
    lines.append("")

    # 基本信息
    lines.append("## 基本信息")
    lines.append("")
    lines.append(f"| 项目 | 内容 |")
    lines.append(f"|------|------|")
    lines.append(f"| 案由 | {case_brief} |")
    lines.append(f"| 原告 | {plaintiff.get('name', '—')} |")
    lines.append(f"| 被告 | {defendant.get('name', '—')} |")
    lines.append(f"| 管辖法院 | {court} |")
    lines.append(f"| 提交日期 | {submission_date} |")
    lines.append("")

    # 当事人信息
    lines.append("## 一、当事人信息")
    lines.append("")

    lines.append(format_party_md(plaintiff, "原告"))
    lines.append(format_party_md(defendant, "被告"))

    # 代理人
    if agent.get("name"):
        lines.append("**委托代理人**：")
        lines.append("")
        agent_parts = [agent.get("name", "")]
        if agent.get("law_firm"):
            agent_parts.append(agent["law_firm"])
        if agent.get("license_no"):
            agent_parts.append(f'执业证号：{agent["license_no"]}')
        if agent.get("phone"):
            agent_parts.append(f'联系电话：{agent["phone"]}')
        lines.append(f'- {"，".join(agent_parts)}')
        lines.append("")

    lines.append(f'**案由**：{case_brief}')
    lines.append("")

    lines.append("---")
    lines.append("")

    # 二、诉讼请求
    lines.append("## 二、诉讼请求")
    lines.append("")

    for item in claims:
        idx = item.get("id", "")
        claim = item.get("claim", "")
        calc = item.get("calculation_method", "")
        legal_basis = item.get("legal_basis", "")

        lines.append(f"### {idx}. {claim}")
        lines.append("")

        if calc:
            lines.append(f'> 计算方式：{calc}')
            lines.append("")

        if legal_basis:
            lines.append(f'> 法律依据：**{legal_basis}**')
            lines.append("")

        lines.append("---")
        lines.append("")

    # 三、事实与理由
    lines.append("## 三、事实与理由")
    lines.append("")

    # （一）案件基本事实
    case_facts = facts.get("case_facts", "")
    if case_facts:
        lines.append("### （一）案件基本事实")
        lines.append("")
        lines.append(case_facts)
        lines.append("")
        lines.append("---")
        lines.append("")

    # （二）被告违约/侵权的事实
    defendant_breach = facts.get("defendant_breach", "")
    if defendant_breach:
        lines.append("### （二）被告违约/侵权的事实")
        lines.append("")
        lines.append(defendant_breach)
        lines.append("")
        lines.append("---")
        lines.append("")

    # （三）原告遭受的损失
    plaintiff_loss = facts.get("plaintiff_loss", "")
    if plaintiff_loss:
        lines.append("### （三）原告遭受的损失")
        lines.append("")
        lines.append(plaintiff_loss)
        lines.append("")
        lines.append("---")
        lines.append("")

    # （四）法律依据
    legal_basis = facts.get("legal_basis", [])
    if legal_basis:
        lines.append("### （四）法律依据")
        lines.append("")

        for i, item in enumerate(legal_basis, 1):
            law = item.get("law", "")
            application = item.get("application", "")
            lines.append(f"**{i}. {law}**")
            lines.append("")
            lines.append(f'> {application}')
            lines.append("")

        lines.append("---")
        lines.append("")

    # （五）证据和证据来源
    evidence_list = facts.get("evidence_list", [])
    if evidence_list:
        lines.append("### （五）证据和证据来源")
        lines.append("")

        lines.append("| 序号 | 证据名称 | 证据来源 | 证明目的 |")
        lines.append("|------|---------|---------|---------|")
        for item in evidence_list:
            eid = item.get("id", "")
            name = item.get("name", "")
            source = item.get("source", "")
            proves = item.get("proves", "")
            lines.append(f"| {eid} | {name} | {source} | {proves} |")
        lines.append("")

    # 管辖依据
    jurisdiction = data.get("jurisdiction_basis", "")
    if jurisdiction:
        lines.append("### （六）管辖依据")
        lines.append("")
        lines.append(jurisdiction)
        lines.append("")
        lines.append("---")
        lines.append("")

    # 诉讼时效
    sol = data.get("statute_of_limitations", {})
    if sol:
        status = sol.get("status", "未届满")
        lines.append("### （七）诉讼时效说明")
        lines.append("")
        lines.append(f"- **状态**：{status}")
        if sol.get("expiry_date"):
            lines.append(f"- **届满日期**：{sol['expiry_date']}")
        if sol.get("note"):
            lines.append(f"- **说明**：{sol['note']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # 四、结论
    lines.append("## 四、结论")
    lines.append("")

    conclusion = data.get("conclusion", "")
    if conclusion:
        lines.append(conclusion)
        lines.append("")

    lines.append("**综上所述，恳请贵院依法查明事实，支持原告的全部诉讼请求。**")
    lines.append("")

    lines.append(f"此致  ")
    lines.append(f"**{court}**")
    lines.append("")

    # 附件
    appendices = data.get("appendices", [])
    if appendices:
        lines.append("### 附：")
        lines.append("")
        for item in appendices:
            lines.append(f"- {item}")
        lines.append("")

    lines.append(f"原告（签名/盖章）：  ")
    if agent.get("name"):
        lines.append(f"委托代理人（签名）：  ")
    lines.append(f"日期：  ")
    lines.append("")

    lines.append("---")
    lines.append(f'*本文件由AI法律文书系统生成，生成时间：{datetime.now().strftime("%Y年%m月%d日 %H:%M")}，仅供律师参考，不构成正式法律意见。*')

    content = '\n'.join(lines)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return output_path


def main():
    parser = argparse.ArgumentParser(description='起诉状 Markdown 报告生成器')
    parser.add_argument('--input', '-i', required=True, help='起诉状JSON文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出Markdown文件路径')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    path = generate_md(data, args.output)
    print(f"Markdown起诉状已生成: {path}")
    return 0


if __name__ == '__main__':
    exit(main())
