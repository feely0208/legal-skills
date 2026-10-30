#!/usr/bin/env python3
"""证据目录思维导图生成器。生成 .mm (FreeMind) 和 .html (交互式) 两种格式。"""

import json
import os
import argparse
from datetime import datetime

# Evidence type colors
TYPE_COLORS = {
    "书证":      "#2F5496",
    "物证":      "#DC3545",
    "视听资料":  "#FD7E14",
    "电子数据":  "#0D6EFD",
    "证人证言":  "#6F42C1",
    "鉴定意见":  "#198754",
    "勘验笔录":  "#17A2B8",
    "当事人陈述": "#6C757D",
}

ORIG_COLORS = {
    "原件":  "#198754",
    "复印件": "#FD7E14",
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
    title = data.get("title", "证据目录")
    summary = data.get("summary", {})
    evidence_items = data.get("evidence_items", [])

    lines = ['<map version="1.0.1">']
    lines.append(f'<node TEXT="{escape_xml(title)}">')

    # Case info
    lines.append('<node TEXT="📋 案件信息" COLOR="#2F5496">')
    lines.append(f'<node TEXT="案号: {data.get("case_number", "—")}"/>')
    lines.append(f'<node TEXT="法院: {data.get("court", "—")}"/>')
    lines.append(f'<node TEXT="提交人: {data.get("party_name", "—")}（{data.get("submitting_party", "—")}）"/>')
    lines.append(f'<node TEXT="提交日期: {data.get("submission_date", "—")}"/>')
    lines.append('</node>')

    # Overview
    lines.append('<node TEXT="📊 证据概况" COLOR="#333333">')
    lines.append(f'<node TEXT="证据总数: {summary.get("total_items", 0)} 项"/>')
    lines.append(f'<node TEXT="合计页数: {summary.get("total_pages", 0)} 页"/>')
    lines.append(f'<node TEXT="原件: {summary.get("original_count", 0)} 份" COLOR="{ORIG_COLORS["原件"]}"/>')
    lines.append(f'<node TEXT="复印件: {summary.get("copy_count", 0)} 份" COLOR="{ORIG_COLORS["复印件"]}"/>')
    lines.append('</node>')

    # Evidence types used
    types = summary.get("evidence_types_used", [])
    if types:
        lines.append('<node TEXT="🏷️ 证据类型" COLOR="#2F5496">')
        for t in types:
            lines.append(f'<node TEXT="{escape_xml(t)}" COLOR="{TYPE_COLORS.get(t, "#333333")}"/>')
        lines.append('</node>')

    # Main facts to prove
    facts = summary.get("main_facts", [])
    if facts:
        lines.append('<node TEXT="🎯 主要证明事项" COLOR="#DC3545">')
        for f in facts:
            lines.append(f'<node TEXT="{escape_xml(f)}"/>')
        lines.append('</node>')

    # Evidence items
    lines.append('<node TEXT="📎 证据目录" COLOR="#2F5496">')
    for item in evidence_items:
        idx = item.get("id", "")
        name = item.get("evidence_name", "")
        ev_type = item.get("evidence_type", "")
        type_color = TYPE_COLORS.get(ev_type, "#333333")
        is_orig = "原件" if item.get("is_original", False) else "复印件"
        orig_color = ORIG_COLORS.get(is_orig, "#333333")

        lines.append(f'<node TEXT="证据{idx}: {escape_xml(name)}" COLOR="{type_color}">')
        lines.append(f'<node TEXT="类型: {escape_xml(ev_type)}" COLOR="{type_color}"/>')
        lines.append(f'<node TEXT="来源: {escape_xml(item.get("evidence_source", ""))}"/>')
        lines.append(f'<node TEXT="页数: {item.get("pages", "")} | 份数: {item.get("copies", "")}"/>')
        lines.append(f'<node TEXT="{is_orig}" COLOR="{orig_color}"/>')

        purpose = item.get("proof_purpose", "")
        if purpose:
            lines.append(f'<node TEXT="证明目的" COLOR="#198754"><node TEXT="{escape_xml(purpose[:200])}"/></node>')

        remarks = item.get("remarks", "")
        if remarks:
            lines.append(f'<node TEXT="备注: {escape_xml(remarks)}"/>')

        lines.append('</node>')

    lines.append('</node>')  # end evidence items

    # Certification
    cert = data.get("certification", "")
    if cert:
        lines.append(f'<node TEXT="📝 提交人声明" COLOR="#2F5496"><node TEXT="{escape_xml(cert[:200])}"/></node>')

    lines.append('</node>')  # end root
    lines.append('</map>')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return output_path


def generate_html_mindmap(data, output_path):
    """生成独立HTML交互式思维导图"""
    title = data.get("title", "证据目录")
    summary = data.get("summary", {})
    evidence_items = data.get("evidence_items", [])
    date_str = datetime.now().strftime("%Y年%m月%d日")

    # Case info branch
    info_branch = f'''<div class="branch">
      <div class="branch-title" style="background:#2F5496;">📋 案件信息</div>
      <div class="summary-panel">
        <b>案号：</b>{escape_xml(data.get("case_number", "—"))}<br>
        <b>法院：</b>{escape_xml(data.get("court", "—"))}<br>
        <b>提交人：</b>{escape_xml(data.get("party_name", "—"))}（{escape_xml(data.get("submitting_party", "—"))}）<br>
        <b>提交日期：</b>{escape_xml(data.get("submission_date", date_str))}
      </div>
    </div>'''

    # Overview branch
    overview_branch = f'''<div class="branch">
      <div class="branch-title" style="background:#2F5496;">📊 证据概况</div>
      <div class="summary-panel">
        <b>证据总数：</b>{summary.get("total_items", 0)} 项<br>
        <b>合计页数：</b>{summary.get("total_pages", 0)} 页<br>
        <span style="color:{ORIG_COLORS["原件"]};"><b>🔴 原件：</b>{summary.get("original_count", 0)} 份</span><br>
        <span style="color:{ORIG_COLORS["复印件"]};"><b>🟠 复印件：</b>{summary.get("copy_count", 0)} 份</span>
      </div>
    </div>'''

    # Evidence types branch
    types_html = ""
    types = summary.get("evidence_types_used", [])
    if types:
        items = ''.join(
            f'<div class="leaf" style="border-left-color:{TYPE_COLORS.get(t, "#333333")};"><div class="leaf-title" style="color:{TYPE_COLORS.get(t, "#333333")};">🏷️ {escape_xml(t)}</div></div>'
            for t in types
        )
        types_html = f'''<div class="branch">
      <div class="branch-title" style="background:#2F5496;">🏷️ 证据类型</div>
      <div class="branch-items">{items}</div>
    </div>'''

    # Main facts branch
    facts_html = ""
    facts = summary.get("main_facts", [])
    if facts:
        items = ''.join(
            f'<div class="leaf" style="border-left-color:#DC3545;"><div class="leaf-title" style="color:#DC3545;">{escape_xml(f)}</div></div>'
            for f in facts
        )
        facts_html = f'''<div class="branch">
      <div class="branch-title" style="background:#DC3545;">🎯 主要证明事项</div>
      <div class="branch-items">{items}</div>
    </div>'''

    # Evidence items cards
    evidence_cards = ""
    for item in evidence_items:
        idx = item.get("id", "")
        name = item.get("evidence_name", "")
        ev_type = item.get("evidence_type", "")
        type_color = TYPE_COLORS.get(ev_type, "#333333")
        is_orig = "原件" if item.get("is_original", False) else "复印件"
        orig_color = ORIG_COLORS.get(is_orig, "#333333")

        evidence_cards += f'''<div class="leaf" style="border-left-color:{type_color};">
        <div class="leaf-title" style="color:{type_color};">证据{idx}: {escape_xml(name)}</div>
        <div class="leaf-meta">
          类型: {escape_xml(ev_type)} |
          来源: {escape_xml(item.get("evidence_source", "—"))} |
          页数: {item.get("pages", "—")} |
          份数: {item.get("copies", "—")} |
          <span style="color:{orig_color}; font-weight:bold;">{is_orig}</span>
        </div>
        <div class="leaf-detail">
          <b>证明目的：</b>{escape_xml(item.get("proof_purpose", ""))}<br>
          <b>备注：</b>{escape_xml(item.get("remarks", "无"))}
        </div>
      </div>'''

    evidence_branch = f'''<div class="branch" style="min-width:420px;">
      <div class="branch-title" style="background:#2F5496;">📎 证据目录</div>
      <div class="branch-items">{evidence_cards}</div>
    </div>'''

    # Certification
    cert_html = ""
    cert = data.get("certification", "")
    if cert:
        cert_html = f'''<div class="bottom-lines"><h3>📝 提交人声明</h3><p>{escape_xml(cert)}</p></div>'''

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
.branch {{ display: flex; flex-direction: column; align-items: center; gap: 8px; min-width: 220px; max-width: 460px; }}
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
  <h1>证据目录思维导图</h1>
  <small>{escape_xml(title)} &nbsp;|&nbsp; 生成于 {date_str}</small>
</div>
<div class="mindmap">
  <div class="tree">
    <div class="root-node">{escape_xml(title)}</div>
    <div class="connector"></div>
    <div class="branches">
      {info_branch}
      {overview_branch}
      {types_html}
      {facts_html}
      {evidence_branch}
    </div>
    {cert_html}
  </div>
</div>
<div class="footer">双击证据卡片展开详情 &nbsp;|&nbsp; AI法律证据系统生成 &nbsp;|&nbsp; 仅供律师参考</div>
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
    parser = argparse.ArgumentParser(description='证据目录思维导图生成器')
    parser.add_argument('--input', '-i', required=True, help='证据目录JSON文件路径')
    parser.add_argument('--output-dir', '-o', required=True, help='输出目录路径')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    os.makedirs(args.output_dir, exist_ok=True)

    # Generate .mm file
    mm_path = os.path.join(args.output_dir, '证据目录思维导图.mm')
    generate_freemind(data, mm_path)
    print(f"FreeMind思维导图: {mm_path}")

    # Generate .html file
    html_path = os.path.join(args.output_dir, '证据目录思维导图.html')
    generate_html_mindmap(data, html_path)
    print(f"HTML思维导图: {html_path}")

    return 0


if __name__ == '__main__':
    exit(main())
