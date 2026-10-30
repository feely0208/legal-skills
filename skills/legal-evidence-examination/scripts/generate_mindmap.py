#!/usr/bin/env python3
"""质证意见思维导图生成器。生成 .mm (FreeMind) 和 .html (交互式) 两种格式。"""

import json
import os
import argparse
from datetime import datetime

COLOR_MAP = {
    "red":    "#DC3545",
    "orange": "#FD7E14",
    "blue":   "#0D6EFD",
    "green":  "#198754",
    "purple": "#6F42C1",
}

VERDICT_COLORS = {
    "认可":    "#198754",
    "不认可":   "#DC3545",
    "无法确认": "#FD7E14",
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
    title = data.get("title", "质证意见书")
    summary = data.get("summary", {})
    evidence_items = data.get("evidence_items", [])

    lines = ['<map version="1.0.1">']
    lines.append(f'<node TEXT="{escape_xml(title)}">')

    # 案件信息
    lines.append('<node TEXT="📋 案件信息" COLOR="#2F5496">')
    lines.append(f'<node TEXT="案号: {data.get("case_number", "—")}"/>')
    lines.append(f'<node TEXT="法院: {data.get("court", "—")}"/>')
    role_label = "原告" if data.get("examiner_role") == "plaintiff" else "被告"
    lines.append(f'<node TEXT="质证人: {data.get("examiner_party", "—")}（{role_label}）"/>')
    lines.append('</node>')

    # 总体概况
    lines.append('<node TEXT="📊 总体概况" COLOR="#333333">')
    lines.append(f'<node TEXT="证据总数: {summary.get("total_evidence", 0)} 份"/>')
    lines.append(f'<node TEXT="无异议: {summary.get("no_objection_count", 0)} 份" COLOR="{COLOR_MAP["green"]}"/>')
    lines.append(f'<node TEXT="部分异议: {summary.get("partial_objection_count", 0)} 份" COLOR="{COLOR_MAP["orange"]}"/>')
    lines.append(f'<node TEXT="完全异议: {summary.get("full_objection_count", 0)} 份" COLOR="{COLOR_MAP["red"]}"/>')
    lines.append('</node>')

    # 主要问题
    issues = summary.get("main_issues", [])
    if issues:
        lines.append(f'<node TEXT="⚠️ 主要问题" COLOR="{COLOR_MAP["red"]}">')
        for issue in issues:
            lines.append(f'<node TEXT="{escape_xml(issue)}"/>')
        lines.append('</node>')

    # 关键缺陷
    weaknesses = summary.get("key_weaknesses", [])
    if weaknesses:
        lines.append(f'<node TEXT="🔍 关键缺陷" COLOR="{COLOR_MAP["orange"]}">')
        for w in weaknesses:
            lines.append(f'<node TEXT="{escape_xml(w)}"/>')
        lines.append('</node>')

    # 逐份证据
    lines.append('<node TEXT="📎 逐份质证意见" COLOR="#2F5496">')
    for item in evidence_items:
        idx = item.get("id", "")
        name = item.get("evidence_name", "")
        overall_v = item.get("overall_verdict", "")
        v_color = VERDICT_COLORS.get(overall_v, "#333333")
        lines.append(f'<node TEXT="证据{idx}: {escape_xml(name)}" COLOR="{v_color}">')

        # 三性
        a_v = item.get("authenticity_verdict", "")
        l_v = item.get("legality_verdict", "")
        r_v = item.get("relevance_verdict", "")

        lines.append(f'<node TEXT="真实性: {a_v}" COLOR="{VERDICT_COLORS.get(a_v, "#333333")}">')
        a_op = item.get("authenticity_opinion", "")[:150]
        if a_op:
            lines.append(f'<node TEXT="{escape_xml(a_op)}"/>')
        lines.append('</node>')

        lines.append(f'<node TEXT="合法性: {l_v}" COLOR="{VERDICT_COLORS.get(l_v, "#333333")}">')
        l_op = item.get("legality_opinion", "")[:150]
        if l_op:
            lines.append(f'<node TEXT="{escape_xml(l_op)}"/>')
        lines.append('</node>')

        lines.append(f'<node TEXT="关联性: {r_v}" COLOR="{VERDICT_COLORS.get(r_v, "#333333")}">')
        r_op = item.get("relevance_opinion", "")[:150]
        if r_op:
            lines.append(f'<node TEXT="{escape_xml(r_op)}"/>')
        lines.append('</node>')

        # 证明目的
        reb = item.get("purpose_rebuttal", "")[:150]
        if reb:
            lines.append(f'<node TEXT="证明目的反驳" COLOR="{COLOR_MAP["purple"]}"><node TEXT="{escape_xml(reb)}"/></node>')

        lines.append('</node>')

    lines.append('</node>')  # end 逐份质证意见

    # 结论
    conclusion = summary.get("conclusion", "")
    if conclusion:
        lines.append(f'<node TEXT="📝 结论" COLOR="#2F5496"><node TEXT="{escape_xml(conclusion[:200])}"/></node>')

    lines.append('</node>')  # end root
    lines.append('</map>')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return output_path


def generate_html_mindmap(data, output_path):
    """生成独立HTML交互式思维导图"""
    title = data.get("title", "质证意见书")
    summary = data.get("summary", {})
    evidence_items = data.get("evidence_items", [])
    date_str = datetime.now().strftime("%Y年%m月%d日")
    role_label = "原告" if data.get("examiner_role") == "plaintiff" else "被告"

    # 构建各分支HTML
    info_branch = f'''<div class="branch">
      <div class="branch-title" style="background:#2F5496;">📋 案件信息</div>
      <div class="summary-panel">
        <b>案号：</b>{escape_xml(data.get("case_number", "—"))}<br>
        <b>法院：</b>{escape_xml(data.get("court", "—"))}<br>
        <b>质证人：</b>{escape_xml(data.get("examiner_party", "—"))}（{role_label}）<br>
        <b>提交日期：</b>{escape_xml(data.get("submission_date", date_str))}
      </div>
    </div>'''

    overview_branch = f'''<div class="branch">
      <div class="branch-title" style="background:#2F5496;">📊 总体概况</div>
      <div class="summary-panel">
        <b>证据总数：</b>{summary.get("total_evidence", 0)} 份<br>
        <span style="color:{COLOR_MAP["green"]};"><b>✅ 无异议：</b>{summary.get("no_objection_count", 0)} 份</span><br>
        <span style="color:{COLOR_MAP["orange"]};"><b>⚠️ 部分异议：</b>{summary.get("partial_objection_count", 0)} 份</span><br>
        <span style="color:{COLOR_MAP["red"]};"><b>❌ 完全异议：</b>{summary.get("full_objection_count", 0)} 份</span>
      </div>
    </div>'''

    # 证据质证分支
    evidence_cards = ""
    for item in evidence_items:
        idx = item.get("id", "")
        name = item.get("evidence_name", "")
        overall_v = item.get("overall_verdict", "")
        v_color = VERDICT_COLORS.get(overall_v, "#333333")
        emoji = "✅" if overall_v == "认可" else "❌" if overall_v == "不认可" else "⚠️"

        evidence_cards += f'''<div class="leaf" style="border-left-color:{v_color};">
        <div class="leaf-title" style="color:{v_color};">{emoji} 证据{idx}: {escape_xml(name)}</div>
        <div class="leaf-meta">
          真实性: {item.get("authenticity_verdict", "—")} |
          合法性: {item.get("legality_verdict", "—")} |
          关联性: {item.get("relevance_verdict", "—")}
        </div>
        <div class="leaf-detail">
          <b>真实性意见：</b>{escape_xml(item.get("authenticity_opinion", "")[:150])}<br>
          <b>合法性意见：</b>{escape_xml(item.get("legality_opinion", "")[:150])}<br>
          <b>关联性意见：</b>{escape_xml(item.get("relevance_opinion", "")[:150])}<br>
          <b>证明目的反驳：</b>{escape_xml(item.get("purpose_rebuttal", "")[:150])}<br>
          <b>综合意见：</b>{escape_xml(item.get("overall_opinion", ""))}
        </div>
      </div>'''

    evidence_branch = f'''<div class="branch" style="min-width:380px;">
      <div class="branch-title" style="background:#2F5496;">📎 逐份质证意见</div>
      <div class="branch-items">{evidence_cards}</div>
    </div>'''

    # 问题分支
    issues_html = ""
    issues = summary.get("main_issues", [])
    if issues:
        items = ''.join(f'<div class="leaf" style="border-left-color:{COLOR_MAP["red"]};"><div class="leaf-title" style="color:{COLOR_MAP["red"]};">{escape_xml(iss)}</div></div>' for iss in issues)
        issues_html = f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["red"]};">⚠️ 主要问题</div>
      <div class="branch-items">{items}</div>
    </div>'''

    weaknesses_html = ""
    weaknesses = summary.get("key_weaknesses", [])
    if weaknesses:
        items = ''.join(f'<div class="leaf" style="border-left-color:{COLOR_MAP["orange"]};"><div class="leaf-title" style="color:{COLOR_MAP["orange"]};">{escape_xml(w)}</div></div>' for w in weaknesses)
        weaknesses_html = f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["orange"]};">🔍 关键缺陷</div>
      <div class="branch-items">{items}</div>
    </div>'''

    conclusion_html = ""
    conclusion = summary.get("conclusion", "")
    if conclusion:
        conclusion_html = f'''<div class="bottom-lines"><h3>📝 结论</h3><p>{escape_xml(conclusion[:300])}</p></div>'''

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
.branch {{ display: flex; flex-direction: column; align-items: center; gap: 8px; min-width: 220px; max-width: 400px; }}
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
.bottom-lines {{ margin-top: 30px; background: #E8EAF6; border: 1px solid #9FA8DA; border-radius: 8px; padding: 12px 20px; max-width: 600px; font-size: 13px; }}
.bottom-lines h3 {{ color: #2F5496; font-size: 14px; margin-bottom: 6px; }}
.footer {{ text-align: center; padding: 20px; color: #999; font-size: 11px; }}
.connector {{ width: 2px; height: 20px; background: #ccc; }}
@media (max-width: 768px) {{ .branches {{ flex-direction: column; align-items: center; }} }}
</style>
</head>
<body>
<div class="header">
  <h1>质证意见思维导图</h1>
  <small>{escape_xml(title)} &nbsp;|&nbsp; 生成于 {date_str}</small>
</div>
<div class="mindmap">
  <div class="tree">
    <div class="root-node">{escape_xml(title)}</div>
    <div class="connector"></div>
    <div class="branches">
      {info_branch}
      {overview_branch}
      {issues_html}
      {weaknesses_html}
      {evidence_branch}
    </div>
    {conclusion_html}
  </div>
</div>
<div class="footer">双击卡片展开详情 &nbsp;|&nbsp; AI法律质证系统生成 &nbsp;|&nbsp; 仅供律师参考</div>
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
    parser = argparse.ArgumentParser(description='质证意见思维导图生成器')
    parser.add_argument('--input', '-i', required=True, help='质证JSON文件路径')
    parser.add_argument('--output-dir', '-o', required=True, help='输出目录路径')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    os.makedirs(args.output_dir, exist_ok=True)

    # 生成 .mm 文件
    mm_path = os.path.join(args.output_dir, '质证思维导图.mm')
    generate_freemind(data, mm_path)
    print(f"FreeMind思维导图: {mm_path}")

    # 生成 .html 文件
    html_path = os.path.join(args.output_dir, '质证思维导图.html')
    generate_html_mindmap(data, html_path)
    print(f"HTML思维导图: {html_path}")

    return 0


if __name__ == '__main__':
    exit(main())
