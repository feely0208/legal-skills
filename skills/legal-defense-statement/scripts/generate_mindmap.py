#!/usr/bin/env python3
"""答辩状思维导图生成器。生成 .mm (FreeMind) 和 .html (交互式) 两种格式。"""

import json
import os
import argparse
from datetime import datetime

COLOR_MAP = {
    "dark_blue": "#2F5496",
    "red":       "#DC3545",
    "orange":    "#FD7E14",
    "blue":      "#0D6EFD",
    "green":     "#198754",
    "purple":    "#6F42C1",
}

POSITION_COLORS = {
    "驳回":         "#DC3545",
    "部分认可":      "#FD7E14",
    "认可但需澄清":  "#0D6EFD",
    "认可":          "#198754",
}

FACT_POSITION_COLORS = {
    "属实":     "#198754",
    "不属实":   "#DC3545",
    "部分属实": "#FD7E14",
}


def escape_xml(text):
    """转义XML特殊字符"""
    if not text:
        return ""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;'))


def position_emoji(position):
    if position == "驳回":
        return "❌"
    elif position == "认可":
        return "✅"
    elif position == "部分认可":
        return "⚠️"
    elif position == "认可但需澄清":
        return "🔵"
    return "➖"


def fact_emoji(position):
    if position == "属实":
        return "✅"
    elif position == "不属实":
        return "❌"
    elif position == "部分属实":
        return "⚠️"
    return "➖"


def generate_freemind(data, output_path):
    """生成 FreeMind (.mm) 格式思维导图"""
    title = data.get("title", "民事答辩状")
    respondent_role = data.get("respondent_role", "defendant")
    role_label = "被告" if respondent_role == "defendant" else "原告"
    respondent = data.get("respondent", {})
    counterparty = data.get("counterparty", {})
    claims_response = data.get("claims_response", [])
    facts = data.get("facts_and_reasons", {})

    lines = ['<map version="1.0.1">']
    lines.append(f'<node TEXT="{escape_xml(title)}">')

    # 案件信息
    lines.append('<node TEXT="📋 案件信息" COLOR="#2F5496">')
    lines.append(f'<node TEXT="案号: {data.get("case_number", "—")}"/>')
    lines.append(f'<node TEXT="法院: {data.get("court", "—")}"/>')
    lines.append(f'<node TEXT="案由: {data.get("case_brief", "—")}"/>')
    lines.append(f'<node TEXT="答辩人: {respondent.get("name", "—")}（{role_label}）"/>')
    lines.append(f'<node TEXT="被答辩人: {counterparty.get("name", "—")}"/>')
    lines.append('</node>')

    # 答辩请求
    lines.append('<node TEXT="⚖️ 答辩请求" COLOR="#2F5496">')
    for item in claims_response:
        idx = item.get("id", "")
        claim = item.get("plaintiff_claim", "")[:80]
        position = item.get("defense_position", "")
        p_color = POSITION_COLORS.get(position, "#333333")
        emoji = position_emoji(position)
        lines.append(f'<node TEXT="{emoji}[{idx}] {escape_xml(claim)}" COLOR="{p_color}">')
        reason = item.get("defense_reason", "")[:150]
        if reason:
            lines.append(f'<node TEXT="{escape_xml(reason)}"/>')
        lines.append('</node>')
    lines.append('</node>')

    # 事实与理由
    lines.append('<node TEXT="📝 事实与理由" COLOR="#2F5496">')

    # 对原告事实的回应
    response_items = facts.get("response_to_plaintiff_facts", [])
    if response_items:
        lines.append('<node TEXT="回应被答辩人事实" COLOR="#DC3545">')
        for item in response_items:
            allegation = item.get("plaintiff_allegation", "")[:80]
            position = item.get("respondent_position", "")
            p_color = FACT_POSITION_COLORS.get(position, "#333333")
            emoji = fact_emoji(position)
            lines.append(f'<node TEXT="{emoji} {escape_xml(allegation)}" COLOR="{p_color}">')
            resp = item.get("respondent_response", "")[:120]
            if resp:
                lines.append(f'<node TEXT="{escape_xml(resp)}"/>')
            lines.append('</node>')
        lines.append('</node>')

    # 法律依据
    legal_basis = facts.get("legal_basis", [])
    if legal_basis:
        lines.append(f'<node TEXT="法律依据" COLOR="{COLOR_MAP["blue"]}">')
        for item in legal_basis:
            law = item.get("law", "")
            lines.append(f'<node TEXT="{escape_xml(law)}">')
            application = item.get("application", "")[:120]
            if application:
                lines.append(f'<node TEXT="{escape_xml(application)}"/>')
            lines.append('</node>')
        lines.append('</node>')

    # 程序性抗辩
    procedural = facts.get("procedural_defenses", [])
    active_defenses = [d for d in procedural if d.get("applicable")]
    if active_defenses:
        lines.append(f'<node TEXT="🛡️ 程序性抗辩" COLOR="{COLOR_MAP["red"]}">')
        for d in active_defenses:
            lines.append(f'<node TEXT="{escape_xml(d.get("type", ""))}"/>')
        lines.append('</node>')

    lines.append('</node>')  # end 事实与理由

    # 结论
    conclusion = data.get("conclusion", "")
    if conclusion:
        lines.append(f'<node TEXT="📌 结论" COLOR="#2F5496"><node TEXT="{escape_xml(conclusion[:200])}"/></node>')

    lines.append('</node>')  # end root
    lines.append('</map>')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return output_path


def generate_html_mindmap(data, output_path):
    """生成独立HTML交互式思维导图"""
    title = data.get("title", "民事答辩状")
    respondent_role = data.get("respondent_role", "defendant")
    role_label = "被告" if respondent_role == "defendant" else "原告"
    respondent = data.get("respondent", {})
    counterparty = data.get("counterparty", {})
    claims_response = data.get("claims_response", [])
    facts = data.get("facts_and_reasons", {})
    date_str = datetime.now().strftime("%Y年%m月%d日")

    # 案件信息分支
    info_branch = f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["dark_blue"]};">📋 案件信息</div>
      <div class="summary-panel">
        <b>案号：</b>{escape_xml(data.get("case_number", "—"))}<br>
        <b>法院：</b>{escape_xml(data.get("court", "—"))}<br>
        <b>案由：</b>{escape_xml(data.get("case_brief", "—"))}<br>
        <b>答辩人：</b>{escape_xml(respondent.get("name", "—"))}（{role_label}）<br>
        <b>被答辩人：</b>{escape_xml(counterparty.get("name", "—"))}<br>
        <b>提交日期：</b>{escape_xml(data.get("submission_date", date_str))}
      </div>
    </div>'''

    # 答辩请求分支
    claims_cards = ""
    for item in claims_response:
        idx = item.get("id", "")
        claim = item.get("plaintiff_claim", "")
        position = item.get("defense_position", "")
        p_color = POSITION_COLORS.get(position, "#333333")
        emoji = position_emoji(position)
        detail = item.get("defense_detail", "")
        reason = item.get("defense_reason", "")

        claims_cards += f'''<div class="leaf" style="border-left-color:{p_color};">
        <div class="leaf-title" style="color:{p_color};">{emoji} [{idx}] {escape_xml(claim[:100])}</div>
        <div class="leaf-meta">答辩态度：<b>{escape_xml(position)}</b></div>
        <div class="leaf-detail">
          {f"<b>答辩请求：</b>{escape_xml(detail)}<br>" if detail else ""}
          <b>答辩理由：</b>{escape_xml(reason[:200])}
        </div>
      </div>'''

    claims_branch = f'''<div class="branch" style="min-width:380px;">
      <div class="branch-title" style="background:{COLOR_MAP["dark_blue"]};">⚖️ 答辩请求</div>
      <div class="branch-items">{claims_cards}</div>
    </div>'''

    # 事实与理由分支
    facts_html = ""

    # 对原告事实的回应
    response_items = facts.get("response_to_plaintiff_facts", [])
    if response_items:
        response_cards = ""
        for item in response_items:
            allegation = item.get("plaintiff_allegation", "")
            position = item.get("respondent_position", "")
            p_color = FACT_POSITION_COLORS.get(position, "#333333")
            emoji = fact_emoji(position)
            resp = item.get("respondent_response", "")
            response_cards += f'''<div class="leaf" style="border-left-color:{p_color};">
            <div class="leaf-title" style="color:{p_color};">{emoji} {escape_xml(allegation[:100])}</div>
            <div class="leaf-meta">答辩人认为：<b>{escape_xml(position)}</b></div>
            <div class="leaf-detail">{escape_xml(resp[:200])}</div>
          </div>'''

        facts_html += f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["red"]};">📝 回应被答辩人事实</div>
      <div class="branch-items">{response_cards}</div>
    </div>'''

    # 法律依据
    legal_basis = facts.get("legal_basis", [])
    if legal_basis:
        legal_cards = ""
        for item in legal_basis:
            law = item.get("law", "")
            application = item.get("application", "")
            legal_cards += f'''<div class="leaf" style="border-left-color:{COLOR_MAP["blue"]};">
            <div class="leaf-title" style="color:{COLOR_MAP["blue"]};">📖 {escape_xml(law)}</div>
            <div class="leaf-detail">{escape_xml(application[:200])}</div>
          </div>'''

        facts_html += f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["blue"]};">📖 法律依据</div>
      <div class="branch-items">{legal_cards}</div>
    </div>'''

    # 程序性抗辩
    procedural = facts.get("procedural_defenses", [])
    active_defenses = [d for d in procedural if d.get("applicable")]
    if active_defenses:
        proc_cards = "".join(
            f'<div class="leaf" style="border-left-color:{COLOR_MAP["red"]};"><div class="leaf-title" style="color:{COLOR_MAP["red"]};">🛡️ {escape_xml(d.get("type", ""))}</div><div class="leaf-detail">{escape_xml(d.get("note", ""))}</div></div>'
            for d in active_defenses
        )
        facts_html += f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["red"]};">🛡️ 程序性抗辩</div>
      <div class="branch-items">{proc_cards}</div>
    </div>'''

    # 结论
    conclusion_html = ""
    conclusion = data.get("conclusion", "")
    if conclusion:
        conclusion_html = f'''<div class="bottom-lines"><h3>📌 结论</h3><p>{escape_xml(conclusion[:400])}</p></div>'''

    # 统计
    total_claims = len(claims_response)
    reject_count = sum(1 for c in claims_response if c.get("defense_position") == "驳回")
    partial_count = sum(1 for c in claims_response if c.get("defense_position") == "部分认可")
    accept_count = sum(1 for c in claims_response if c.get("defense_position") == "认可")

    overview_branch = f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["dark_blue"]};">📊 答辩概况</div>
      <div class="summary-panel">
        <b>原告诉讼请求：</b>{total_claims} 项<br>
        <span style="color:{COLOR_MAP["red"]};"><b>❌ 请求驳回：</b>{reject_count} 项</span><br>
        <span style="color:{COLOR_MAP["orange"]};"><b>⚠️ 部分认可：</b>{partial_count} 项</span><br>
        <span style="color:{COLOR_MAP["green"]};"><b>✅ 认可：</b>{accept_count} 项</span>
      </div>
    </div>'''

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape_xml(title)} - 思维导图</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: "Microsoft YaHei", "微软雅黑", sans-serif; background: #f0f2f5; min-height: 100vh; }}
.header {{ background: #2F5496; color: white; padding: 16px 24px; text-align: center; }}
.header h1 {{ font-size: 20px; font-weight: normal; }}
.header small {{ opacity: 0.7; font-size: 12px; }}
.mindmap {{ display: flex; justify-content: center; padding: 40px 20px; overflow-x: auto; }}
.tree {{ display: flex; flex-direction: column; align-items: center; gap: 0; }}
.root-node {{ background: #2F5496; color: white; padding: 14px 28px; border-radius: 12px; font-size: 16px; font-weight: bold; text-align: center; max-width: 420px; box-shadow: 0 4px 12px rgba(47,84,150,0.3); }}
.branches {{ display: flex; gap: 24px; margin-top: 20px; flex-wrap: wrap; justify-content: center; }}
.branch {{ display: flex; flex-direction: column; align-items: center; gap: 8px; min-width: 220px; max-width: 420px; }}
.branch-title {{ color: white; padding: 8px 16px; border-radius: 8px; font-size: 14px; font-weight: bold; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }}
.branch-items {{ display: flex; flex-direction: column; gap: 6px; width: 100%; }}
.leaf {{ background: white; border-radius: 6px; padding: 10px 14px; font-size: 13px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); border-left: 4px solid #ccc; cursor: pointer; transition: all 0.2s; }}
.leaf:hover {{ transform: translateX(4px); box-shadow: 0 2px 8px rgba(0,0,0,0.15); }}
.leaf .leaf-title {{ font-weight: bold; margin-bottom: 4px; }}
.leaf .leaf-meta {{ font-size: 11px; color: #666; }}
.leaf .leaf-detail {{ font-size: 11px; color: #888; margin-top: 4px; display: none; }}
.leaf.open .leaf-detail {{ display: block; }}
.summary-panel {{ background: white; border-radius: 8px; padding: 12px 16px; margin: 4px 0; box-shadow: 0 1px 4px rgba(0,0,0,0.08); font-size: 12px; width: 100%; }}
.summary-panel b {{ color: #2F5496; }}
.bottom-lines {{ margin-top: 30px; background: #E8EAF6; border: 1px solid #9FA8DA; border-radius: 8px; padding: 12px 20px; max-width: 650px; font-size: 13px; }}
.bottom-lines h3 {{ color: #2F5496; font-size: 14px; margin-bottom: 6px; }}
.footer {{ text-align: center; padding: 20px; color: #999; font-size: 11px; }}
.connector {{ width: 2px; height: 20px; background: #ccc; }}
@media (max-width: 768px) {{ .branches {{ flex-direction: column; align-items: center; }} }}
</style>
</head>
<body>
<div class="header">
  <h1>答辩状思维导图</h1>
  <small>{escape_xml(title)} &nbsp;|&nbsp; 生成于 {date_str}</small>
</div>
<div class="mindmap">
  <div class="tree">
    <div class="root-node">{escape_xml(title)}</div>
    <div class="connector"></div>
    <div class="branches">
      {info_branch}
      {overview_branch}
      {claims_branch}
      {facts_html}
    </div>
    {conclusion_html}
  </div>
</div>
<div class="footer">双击卡片展开详情 &nbsp;|&nbsp; AI法律文书系统生成 &nbsp;|&nbsp; 仅供律师参考</div>
<script>
document.querySelectorAll('.leaf').forEach(el => {{
  el.addEventListener('dblclick', function() {{ this.classList.toggle('open'); }});
}});
</script>
</body>
</html>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return output_path


def main():
    parser = argparse.ArgumentParser(description='答辩状思维导图生成器')
    parser.add_argument('--input', '-i', required=True, help='答辩状JSON文件路径')
    parser.add_argument('--output-dir', '-o', required=True, help='输出目录路径')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    os.makedirs(args.output_dir, exist_ok=True)

    # 生成 .mm 文件
    mm_path = os.path.join(args.output_dir, '答辩状思维导图.mm')
    generate_freemind(data, mm_path)
    print(f"FreeMind思维导图: {mm_path}")

    # 生成 .html 文件
    html_path = os.path.join(args.output_dir, '答辩状思维导图.html')
    generate_html_mindmap(data, html_path)
    print(f"HTML思维导图: {html_path}")

    return 0


if __name__ == '__main__':
    exit(main())
