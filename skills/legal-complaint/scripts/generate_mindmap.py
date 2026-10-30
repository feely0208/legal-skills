#!/usr/bin/env python3
"""起诉状思维导图生成器。生成 .mm (FreeMind) 和 .html (交互式) 两种格式。"""

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


def generate_freemind(data, output_path):
    """生成 FreeMind (.mm) 格式思维导图"""
    title = data.get("title", "民事起诉状")
    plaintiff = data.get("plaintiff", {})
    defendant = data.get("defendant", {})
    claims = data.get("claims", [])
    facts = data.get("facts_and_reasons", {})

    lines = ['<map version="1.0.1">']
    lines.append(f'<node TEXT="{escape_xml(title)}">')

    # 案件信息
    lines.append('<node TEXT="📋 案件信息" COLOR="#2F5496">')
    lines.append(f'<node TEXT="案由: {escape_xml(data.get("case_brief", "—"))}"/>')
    lines.append(f'<node TEXT="法院: {escape_xml(data.get("court", "—"))}"/>')
    lines.append(f'<node TEXT="原告: {escape_xml(plaintiff.get("name", "—"))}"/>')
    lines.append(f'<node TEXT="被告: {escape_xml(defendant.get("name", "—"))}"/>')
    lines.append(f'<node TEXT="提交日期: {escape_xml(data.get("submission_date", "—"))}"/>')

    # 诉讼时效
    sol = data.get("statute_of_limitations", {})
    if sol:
        sol_status = sol.get("status", "未届满")
        sol_color = "#DC3545" if sol_status == "已届满" else "#198754"
        lines.append(f'<node TEXT="⚠ 诉讼时效: {escape_xml(sol_status)}" COLOR="{sol_color}"/>')

    lines.append('</node>')

    # 诉讼请求
    lines.append('<node TEXT="⚖️ 诉讼请求" COLOR="#2F5496">')
    for item in claims:
        idx = item.get("id", "")
        claim = item.get("claim", "")[:100]
        legal_basis = item.get("legal_basis", "")
        lines.append(f'<node TEXT="[{idx}] {escape_xml(claim)}" COLOR="{COLOR_MAP["dark_blue"]}">')
        calc = item.get("calculation_method", "")
        if calc:
            lines.append(f'<node TEXT="计算: {escape_xml(calc)}"/>')
        if legal_basis:
            lines.append(f'<node TEXT="依据: {escape_xml(legal_basis)}"/>')
        lines.append('</node>')
    lines.append('</node>')

    # 事实与理由
    lines.append('<node TEXT="📝 事实与理由" COLOR="#2F5496">')

    # 案件基本事实
    case_facts = facts.get("case_facts", "")
    if case_facts:
        # 取前150字符作为摘要
        summary = case_facts[:150].replace('\n', ' ').strip()
        lines.append(f'<node TEXT="案件基本事实" COLOR="{COLOR_MAP["green"]}">')
        lines.append(f'<node TEXT="{escape_xml(summary)}"/>')
        lines.append('</node>')

    # 被告违约/侵权
    defendant_breach = facts.get("defendant_breach", "")
    if defendant_breach:
        lines.append(f'<node TEXT="被告违约/侵权" COLOR="{COLOR_MAP["red"]}">')
        lines.append(f'<node TEXT="{escape_xml(defendant_breach[:150])}"/>')
        lines.append('</node>')

    # 原告损失
    plaintiff_loss = facts.get("plaintiff_loss", "")
    if plaintiff_loss:
        lines.append(f'<node TEXT="原告损失" COLOR="{COLOR_MAP["orange"]}">')
        lines.append(f'<node TEXT="{escape_xml(plaintiff_loss[:150])}"/>')
        lines.append('</node>')

    # 法律依据
    legal_basis = facts.get("legal_basis", [])
    if legal_basis:
        lines.append(f'<node TEXT="法律依据" COLOR="{COLOR_MAP["blue"]}">')
        for item in legal_basis:
            law = item.get("law", "")
            lines.append(f'<node TEXT="{escape_xml(law)}">')
            application = item.get("application", "")[:150]
            if application:
                lines.append(f'<node TEXT="{escape_xml(application)}"/>')
            lines.append('</node>')
        lines.append('</node>')

    # 证据清单
    evidence_list = facts.get("evidence_list", [])
    if evidence_list:
        lines.append(f'<node TEXT="证据清单 ({len(evidence_list)}份)" COLOR="{COLOR_MAP["purple"]}">')
        for item in evidence_list:
            name = item.get("name", "")[:80]
            proves = item.get("proves", "")[:80]
            lines.append(f'<node TEXT="{escape_xml(name)}">')
            lines.append(f'<node TEXT="{escape_xml(proves)}"/>')
            lines.append('</node>')
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
    title = data.get("title", "民事起诉状")
    plaintiff = data.get("plaintiff", {})
    defendant = data.get("defendant", {})
    claims = data.get("claims", [])
    facts = data.get("facts_and_reasons", {})
    date_str = datetime.now().strftime("%Y年%m月%d日")

    # 案件信息分支
    sol_html = ""
    sol = data.get("statute_of_limitations", {})
    if sol:
        sol_status = sol.get("status", "未届满")
        sol_color = "#DC3545" if sol_status == "已届满" else "#198754"
        sol_html = f'<br><span style="color:{sol_color};"><b>⚠ 诉讼时效：</b>{escape_xml(sol_status)}</span>'

    info_branch = f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["dark_blue"]};">📋 案件信息</div>
      <div class="summary-panel">
        <b>案由：</b>{escape_xml(data.get("case_brief", "—"))}<br>
        <b>法院：</b>{escape_xml(data.get("court", "—"))}<br>
        <b>原告：</b>{escape_xml(plaintiff.get("name", "—"))}<br>
        <b>被告：</b>{escape_xml(defendant.get("name", "—"))}<br>
        <b>提交日期：</b>{escape_xml(data.get("submission_date", date_str))}
        {sol_html}
      </div>
    </div>'''

    # 诉讼请求分支
    claims_cards = ""
    for item in claims:
        idx = item.get("id", "")
        claim = item.get("claim", "")
        calc = item.get("calculation_method", "")
        legal_basis = item.get("legal_basis", "")

        claims_cards += f'''<div class="leaf" style="border-left-color:{COLOR_MAP["dark_blue"]};">
        <div class="leaf-title" style="color:{COLOR_MAP["dark_blue"]};">[{idx}] {escape_xml(claim[:100])}</div>
        <div class="leaf-detail">
          {f"计算方式：{escape_xml(calc)}<br>" if calc else ""}
          {f"法律依据：<b>{escape_xml(legal_basis)}</b>" if legal_basis else ""}
        </div>
      </div>'''

    claims_branch = f'''<div class="branch" style="min-width:380px;">
      <div class="branch-title" style="background:{COLOR_MAP["dark_blue"]};">⚖️ 诉讼请求（{len(claims)}项）</div>
      <div class="branch-items">{claims_cards}</div>
    </div>'''

    # 事实与理由分支
    facts_html = ""

    # 案件基本事实
    case_facts = facts.get("case_facts", "")
    if case_facts:
        facts_html += f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["green"]};">📝 案件基本事实</div>
      <div class="summary-panel">{escape_xml(case_facts[:300])}</div>
    </div>'''

    # 被告违约/侵权
    defendant_breach = facts.get("defendant_breach", "")
    if defendant_breach:
        facts_html += f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["red"]};">⚠️ 被告违约/侵权</div>
      <div class="summary-panel">{escape_xml(defendant_breach[:300])}</div>
    </div>'''

    # 原告损失
    plaintiff_loss = facts.get("plaintiff_loss", "")
    if plaintiff_loss:
        facts_html += f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["orange"]};">💸 原告损失</div>
      <div class="summary-panel">{escape_xml(plaintiff_loss[:300])}</div>
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

    # 证据清单
    evidence_list = facts.get("evidence_list", [])
    if evidence_list:
        evidence_cards = ""
        for item in evidence_list:
            name = item.get("name", "")
            source = item.get("source", "")
            proves = item.get("proves", "")
            evidence_cards += f'''<div class="leaf" style="border-left-color:{COLOR_MAP["purple"]};">
            <div class="leaf-title" style="color:{COLOR_MAP["purple"]};">📎 {escape_xml(name)}</div>
            <div class="leaf-meta">来源：{escape_xml(source)}</div>
            <div class="leaf-detail">证明目的：{escape_xml(proves)}</div>
          </div>'''

        facts_html += f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["purple"]};">📎 证据清单（{len(evidence_list)}份）</div>
      <div class="branch-items">{evidence_cards}</div>
    </div>'''

    # 结论
    conclusion_html = ""
    conclusion = data.get("conclusion", "")
    if conclusion:
        conclusion_html = f'''<div class="bottom-lines"><h3>📌 结论</h3><p>{escape_xml(conclusion[:400])}</p></div>'''

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
.summary-panel {{ background: white; border-radius: 8px; padding: 12px 16px; margin: 4px 0; box-shadow: 0 1px 4px rgba(0,0,0,0.08); font-size: 12px; width: 100%; max-height: 300px; overflow-y: auto; }}
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
  <h1>起诉状思维导图</h1>
  <small>{escape_xml(title)} &nbsp;|&nbsp; 生成于 {date_str}</small>
</div>
<div class="mindmap">
  <div class="tree">
    <div class="root-node">{escape_xml(title)}</div>
    <div class="connector"></div>
    <div class="branches">
      {info_branch}
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
    parser = argparse.ArgumentParser(description='起诉状思维导图生成器')
    parser.add_argument('--input', '-i', required=True, help='起诉状JSON文件路径')
    parser.add_argument('--output-dir', '-o', required=True, help='输出目录路径')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    os.makedirs(args.output_dir, exist_ok=True)

    # 生成 .mm 文件
    mm_path = os.path.join(args.output_dir, '起诉状思维导图.mm')
    generate_freemind(data, mm_path)
    print(f"FreeMind思维导图: {mm_path}")

    # 生成 .html 文件
    html_path = os.path.join(args.output_dir, '起诉状思维导图.html')
    generate_html_mindmap(data, html_path)
    print(f"HTML思维导图: {html_path}")

    return 0


if __name__ == '__main__':
    exit(main())
