#!/usr/bin/env python3
"""合同审阅思维导图生成器。生成 .mm (FreeMind) 和 .html (交互式) 两种格式。"""

import json
import os
import argparse
from datetime import datetime

COLOR_MAP = {
    "red":    "#DC3545",
    "orange": "#FD7E14",
    "blue":   "#0D6EFD",
    "green":  "#198754",
}

CATEGORY_LABELS = {
    "red":    "漏洞/缺陷",
    "orange": "风险提醒",
    "green":  "修改建议",
}


def generate_freemind(data, output_path):
    """生成 FreeMind (.mm) 格式思维导图"""
    title = data.get("title", "合同审阅报告")
    summary = data.get("summary", {})
    findings = data.get("findings", [])

    # 按类别分组
    groups = {"red": [], "orange": [], "green": []}
    for f in findings:
        cat = f.get("category", "green")
        if cat in groups:
            groups[cat].append(f)

    lines = ['<map version="1.0.1">']
    lines.append(f'<node TEXT="{escape_xml(title)}">')
    lines.append(f'<node TEXT="📋 综合评估" COLOR="#333333">')
    lines.append(f'<node TEXT="整体风险: {summary.get("overall_risk", "—")}" COLOR="{COLOR_MAP["red"] if summary.get("overall_risk") == "高" else COLOR_MAP["orange"] if summary.get("overall_risk") == "中" else COLOR_MAP["green"]}"/>')
    lines.append(f'<node TEXT="签约可行性: {summary.get("signability", "—")}"/>')
    lines.append(f'<node TEXT="共发现问题: {summary.get("total_issues", 0)} 项"/>')
    lines.append(f'<node TEXT="最不利风险敞口" COLOR="{COLOR_MAP["red"]}"><node TEXT="{escape_xml(summary.get("max_risk", "—"))}"/></node>')
    lines.append('</node>')

    for cat, cat_label in [("red", "漏洞/缺陷"), ("orange", "风险提醒"), ("green", "修改建议")]:
        items = groups[cat]
        if not items:
            continue
        color = COLOR_MAP[cat]
        emoji = '\U0001F534' if cat == "red" else '\U0001F7E0' if cat == "orange" else '\U0001F7E2'
        lines.append(f'<node TEXT="{emoji} {cat_label} ({len(items)}项)" COLOR="{color}">')
        for item in items:
            xml_text = escape_xml('第{item["id"]}条: {item["title"]}'.format(item=item))
            lines.append(f'<node TEXT="{xml_text}" COLOR="{color}">')
            lines.append(f'<node TEXT="风险等级: {item.get("risk_level", "—")} | 紧急程度: {item.get("urgency", "—")}"/>')
            lines.append(f'<node TEXT="{escape_xml(item.get("description", "")[:120])}"/>')
            lines.append('</node>')
        lines.append('</node>')

    # 谈判底线
    bottom_lines = summary.get("bottom_lines", [])
    if bottom_lines:
        lines.append(f'<node TEXT="⚡ 谈判底线" COLOR="{COLOR_MAP["red"]}">')
        for bl in bottom_lines:
            lines.append(f'<node TEXT="{escape_xml(bl)}"/>')
        lines.append('</node>')

    lines.append('</node>')
    lines.append('</map>')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return output_path


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


def generate_html_mindmap(data, output_path):
    """生成独立HTML交互式思维导图"""
    title = data.get("title", "合同审阅报告")
    summary = data.get("summary", {})
    findings = data.get("findings", [])

    groups = {"red": [], "orange": [], "green": []}
    for f in findings:
        cat = f.get("category", "green")
        if cat in groups:
            groups[cat].append(f)

    # 构建树形数据（嵌套HTML）
    tree_html = build_tree_html(title, summary, groups)
    date_str = datetime.now().strftime("%Y年%m月%d日")

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
.branch {{ display: flex; flex-direction: column; align-items: center; gap: 8px; min-width: 220px; max-width: 360px; }}
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
.bottom-lines {{ margin-top: 30px; background: #FFF3CD; border: 1px solid #FFC107; border-radius: 8px; padding: 12px 20px; max-width: 600px; font-size: 13px; }}
.bottom-lines h3 {{ color: #DC3545; font-size: 14px; margin-bottom: 6px; }}
.bottom-lines li {{ margin: 4px 0; }}
.footer {{ text-align: center; padding: 20px; color: #999; font-size: 11px; }}
.connector {{ width: 2px; height: 20px; background: #ccc; }}
@media (max-width: 768px) {{ .branches {{ flex-direction: column; align-items: center; }} }}
</style>
</head>
<body>
<div class="header">
  <h1>合同审阅思维导图</h1>
  <small>{escape_xml(title)} &nbsp;|&nbsp; 生成于 {date_str}</small>
</div>
<div class="mindmap">
  <div class="tree">
    <div class="root-node">{escape_xml(title)}</div>
    <div class="connector"></div>
    <div class="branches">
      {build_summary_branch(summary)}
      {build_category_branch("red", "漏洞/缺陷", groups["red"])}
      {build_category_branch("orange", "风险提醒", groups["orange"])}
      {build_category_branch("green", "修改建议", groups["green"])}
    </div>
    {build_bottom_lines(summary)}
  </div>
</div>
<div class="footer">双击卡片展开详情 &nbsp;|&nbsp; AI法律审阅系统生成 &nbsp;|&nbsp; 仅供律师参考</div>
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


def build_summary_branch(summary):
    """构建综合评估分支HTML"""
    overall = summary.get("overall_risk", "—")
    risk_color = COLOR_MAP["red"] if overall == "高" else COLOR_MAP["orange"] if overall == "中" else COLOR_MAP["green"]
    return f'''<div class="branch">
      <div class="branch-title" style="background:#2F5496;">📋 综合评估</div>
      <div class="summary-panel">
        <b>整体风险：</b><span style="color:{risk_color};font-weight:bold;">{overall}</span><br>
        <b>签约可行性：</b>{summary.get("signability", "—")}<br>
        <b>共发现问题：</b>{summary.get("total_issues", 0)} 项<br>
        <b>最不利风险敞口：</b><span style="color:{COLOR_MAP["red"]}">{escape_xml(summary.get("max_risk", "—"))}</span>
      </div>
    </div>'''


def build_category_branch(cat, label, items):
    """构建分类分支HTML"""
    if not items:
        return ""
    color = COLOR_MAP[cat]
    items_html = ""
    for item in items:
        items_html += f'''<div class="leaf" style="border-left-color:{color};">
        <div class="leaf-title" style="color:{color};">第{item["id"]}条: {escape_xml(item["title"])}</div>
        <div class="leaf-meta">风险: {item.get("risk_level", "—")} | 紧急: {item.get("urgency", "—")} | {item.get("clause", "")}</div>
        <div class="leaf-detail">{escape_xml(item.get("description", "")[:200])}<br><br><b>修改建议：</b>{escape_xml(item.get("suggestion", "")[:200])}</div>
      </div>'''
    emoji = "🔴" if cat == "red" else "🟠" if cat == "orange" else "🟢"
    return f'''<div class="branch">
      <div class="branch-title" style="background:{color};">{emoji} {label} ({len(items)}项)</div>
      <div class="branch-items">{items_html}</div>
    </div>'''


def build_bottom_lines(summary):
    """构建谈判底线HTML"""
    bl = summary.get("bottom_lines", [])
    if not bl:
        return ""
    items = '\n'.join(f'<li>{escape_xml(b)}</li>' for b in bl)
    return f'<div class="bottom-lines"><h3>谈判底线（必须坚持）</h3><ul>{items}</ul></div>'


def build_tree_html(title, summary, groups):
    """构建树形HTML（用于嵌入其他页面的简化版本）"""
    # 此函数保留以备将来使用
    return ""


def main():
    parser = argparse.ArgumentParser(description='合同审阅思维导图生成器')
    parser.add_argument('--input', '-i', required=True, help='审阅JSON文件路径')
    parser.add_argument('--output-dir', '-o', required=True, help='输出目录路径')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    os.makedirs(args.output_dir, exist_ok=True)

    # 生成 .mm 文件
    mm_path = os.path.join(args.output_dir, '审阅思维导图.mm')
    generate_freemind(data, mm_path)
    print(f"FreeMind思维导图: {mm_path}")

    # 生成 .html 文件
    html_path = os.path.join(args.output_dir, '审阅思维导图.html')
    generate_html_mindmap(data, html_path)
    print(f"HTML思维导图: {html_path}")

    return 0


if __name__ == '__main__':
    exit(main())
