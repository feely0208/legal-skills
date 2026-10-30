#!/usr/bin/env python3
"""答辩状 Markdown 报告生成器。"""

import json
import os
import argparse
from datetime import datetime


def position_emoji(position):
    """答辩态度对应的emoji"""
    if position == "驳回":
        return "❌"
    elif position == "认可":
        return "✅"
    elif position == "部分认可":
        return "⚠️"
    elif position == "认可但需澄清":
        return "🔵"
    else:
        return "➖"


def fact_emoji(position):
    """事实回应态度对应的emoji"""
    if position == "属实":
        return "✅"
    elif position == "不属实":
        return "❌"
    elif position == "部分属实":
        return "⚠️"
    else:
        return "➖"


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
    """生成 Markdown 答辩状"""
    title = data.get("title", "民事答辩状")
    case_number = data.get("case_number", "—")
    court = data.get("court", "—")
    case_brief = data.get("case_brief", "—")
    respondent_role = data.get("respondent_role", "defendant")
    role_label = "被告" if respondent_role == "defendant" else "原告"
    respondent = data.get("respondent", {})
    counterparty = data.get("counterparty", {})
    agent = data.get("agent", {})
    submission_date = data.get("submission_date",
                               datetime.now().strftime("%Y年%m月%d日"))
    claims_response = data.get("claims_response", [])
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
    lines.append(f"| 案号 | {case_number} |")
    lines.append(f"| 审理法院 | {court} |")
    lines.append(f"| 案由 | {case_brief} |")
    lines.append(f"| 答辩人 | {respondent.get('name', '—')}（{role_label}） |")
    lines.append(f"| 被答辩人 | {counterparty.get('name', '—')} |")
    lines.append(f"| 提交日期 | {submission_date} |")
    lines.append("")

    # 当事人信息
    lines.append("## 一、当事人信息")
    lines.append("")

    resp_label = f"答辩人（{role_label}）"
    lines.append(format_party_md(respondent, resp_label))

    counterparty_label = "被答辩人"
    if respondent_role == "defendant":
        counterparty_label = "被答辩人（原告）"
    else:
        counterparty_label = "被答辩人（被告）"
    lines.append(format_party_md(counterparty, counterparty_label))

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

    # 引言
    lines.append(f'答辩人因被答辩人诉答辩人{case_brief}一案（案号：{case_number}），现提出答辩意见如下：')
    lines.append("")
    lines.append("---")
    lines.append("")

    # 二、答辩请求
    lines.append("## 二、答辩请求")
    lines.append("")

    for item in claims_response:
        idx = item.get("id", "")
        claim = item.get("plaintiff_claim", "")
        position = item.get("defense_position", "")
        detail = item.get("defense_detail", "")
        reason = item.get("defense_reason", "")

        emoji = position_emoji(position)
        lines.append(f"### {idx}. {claim}")
        lines.append("")
        lines.append(f'**答辩态度**：{emoji} **{position}**')
        lines.append("")

        if detail:
            lines.append(detail)
            lines.append("")

        if reason:
            lines.append("**答辩理由**：")
            lines.append("")
            lines.append(reason)
            lines.append("")

        lines.append("---")
        lines.append("")

    # 三、事实与理由
    lines.append("## 三、事实与理由")
    lines.append("")

    # （一）对原告所述事实的回应
    response_items = facts.get("response_to_plaintiff_facts", [])
    if response_items:
        lines.append("### （一）对被答辩人所述事实的回应")
        lines.append("")

        for i, item in enumerate(response_items, 1):
            allegation = item.get("plaintiff_allegation", "")
            position = item.get("respondent_position", "")
            response = item.get("respondent_response", "")

            emoji = fact_emoji(position)
            lines.append(f"**{i}. 关于「{allegation}」**")
            lines.append("")
            lines.append(f'> {emoji} 答辩人认为：**{position}**')
            lines.append("")

            if response:
                lines.append(response)
                lines.append("")

        lines.append("---")
        lines.append("")

    # （二）本案基本事实
    respondent_facts = facts.get("respondent_facts", "")
    if respondent_facts:
        lines.append("### （二）本案基本事实")
        lines.append("")
        lines.append(respondent_facts)
        lines.append("")
        lines.append("---")
        lines.append("")

    # （三）法律适用意见
    legal_basis = facts.get("legal_basis", [])
    if legal_basis:
        lines.append("### （三）法律适用意见")
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

    # （四）对原告证据体系的评价
    evidence_assessment = facts.get("evidence_assessment", "")
    if evidence_assessment:
        lines.append("### （四）对被答辩人证据体系的意见")
        lines.append("")
        lines.append(evidence_assessment)
        lines.append("")
        lines.append("---")
        lines.append("")

    # （五）程序性抗辩
    procedural = facts.get("procedural_defenses", [])
    if procedural:
        active_defenses = [d for d in procedural if d.get("applicable")]
        if active_defenses:
            lines.append("### （五）程序性抗辩")
            lines.append("")
            for d in active_defenses:
                lines.append(f'- ❌ **{d.get("type", "")}**：{d.get("note", "")}')
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

    lines.append("**综上所述，恳请人民法院查明事实，依法公正裁判。**")
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

    lines.append(f"答辩人（签名/盖章）：  ")
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
    parser = argparse.ArgumentParser(description='答辩状 Markdown 报告生成器')
    parser.add_argument('--input', '-i', required=True, help='答辩状JSON文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出Markdown文件路径')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    path = generate_md(data, args.output)
    print(f"Markdown答辩状已生成: {path}")
    return 0


if __name__ == '__main__':
    exit(main())
