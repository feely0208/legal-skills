#!/usr/bin/env python3
"""阅卷笔录思维导图生成器。生成 .mm (FreeMind) 和 .html (交互式) 两种格式。"""

import json
import os
import argparse
from datetime import datetime

COLOR_MAP = {
    "primary": "#2F5496",
    "red":     "#DC3545",
    "orange":  "#FD7E14",
    "green":   "#198754",
    "purple":  "#6F42C1",
    "blue":    "#0D6EFD",
}

RISK_COLORS = {
    "高": "#DC3545",
    "中": "#FD7E14",
    "低": "#198754",
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
    title = data.get("title", "阅卷笔录")
    summary = data.get("summary", {})

    lines = ['<map version="1.0.1">']
    lines.append(f'<node TEXT="{escape_xml(title)}">')

    # 案件信息
    role_label = "原告" if data.get("reviewer_role") == "plaintiff" else "被告"
    lines.append('<node TEXT="📋 案件信息" COLOR="#2F5496">')
    lines.append(f'<node TEXT="案号: {data.get("case_number", "—")}"/>')
    lines.append(f'<node TEXT="法院: {data.get("court", "—")}"/>')
    lines.append(f'<node TEXT="案由: {data.get("case_cause", "—")}"/>')
    lines.append(f'<node TEXT="阅卷人: {data.get("reviewer_name", "—")}（{role_label}方）"/>')
    lines.append(f'<node TEXT="阅卷日期: {data.get("review_date", "—")}"/>')
    lines.append('</node>')

    # 案卷概况
    cats = summary.get("document_categories", {})
    lines.append('<node TEXT="📊 案卷概况" COLOR="#333333">')
    lines.append(f'<node TEXT="材料总数: {summary.get("total_documents", 0)} 份"/>')
    for cat_name, count in cats.items():
        lines.append(f'<node TEXT="{escape_xml(cat_name)}: {count} 份"/>')
    lines.append('</node>')

    # 核心事实
    facts = summary.get("core_facts", "")
    if facts:
        lines.append(f'<node TEXT="📝 核心事实" COLOR="#2F5496"><node TEXT="{escape_xml(facts[:200])}"/></node>')

    # 大事记
    events = summary.get("key_events", [])
    if events:
        lines.append('<node TEXT="📅 案件大事记" COLOR="#2F5496">')
        for ev in events[:10]:
            lines.append(f'<node TEXT="{escape_xml(ev.get("date", ""))} | {escape_xml(ev.get("event", "")[:80])}"/>')
        lines.append('</node>')

    # 争议焦点
    disputes = summary.get("dispute_focus", [])
    if disputes:
        lines.append(f'<node TEXT="🎯 争议焦点" COLOR="{COLOR_MAP["red"]}">')
        for d in disputes:
            lines.append(f'<node TEXT="{escape_xml(d)}"/>')
        lines.append('</node>')

    # 证据评估
    ea = summary.get("evidence_assessment", {})
    if ea:
        lines.append('<node TEXT="🔍 证据体系评估" COLOR="#2F5496">')
        lines.append(f'<node TEXT="原告证据: {ea.get("plaintiff_evidence_strength", "—")}"/>')
        lines.append(f'<node TEXT="被告证据: {ea.get("defendant_evidence_strength", "—")}"/>')
        gaps = ea.get("key_gaps", [])
        if gaps:
            lines.append(f'<node TEXT="⚠️ 证据缺口" COLOR="{COLOR_MAP["red"]}">')
            for g in gaps:
                lines.append(f'<node TEXT="{escape_xml(g[:100])}"/>')
            lines.append('</node>')
        lines.append('</node>')

    # 法律分析
    la = summary.get("legal_analysis", {})
    if la:
        lines.append(f'<node TEXT="⚖️ 法律分析" COLOR="{COLOR_MAP["purple"]}">')
        claim = la.get("claim_basis", "")
        if claim:
            lines.append(f'<node TEXT="请求权基础: {escape_xml(claim[:120])}"/>')
        cases = la.get("relevant_cases", [])
        if cases:
            lines.append('<node TEXT="参考案例">')
            for c in cases:
                lines.append(f'<node TEXT="{escape_xml(c[:120])}"/>')
            lines.append('</node>')
        lines.append('</node>')

    # 程序核查
    checklist = data.get("procedure_checklist", [])
    if checklist:
        lines.append('<node TEXT="✅ 程序核查" COLOR="#2F5496">')
        for item in checklist:
            lines.append(f'<node TEXT="{escape_xml(item.get("item", ""))}: {escape_xml(item.get("status", ""))}"/>')
        lines.append('</node>')

    # 风险评估
    ra = summary.get("risk_assessment", {})
    if ra:
        risk_labels = {
            "fact_risk": "事实认定", "legal_risk": "法律适用",
            "evidence_risk": "证据", "procedure_risk": "程序", "enforcement_risk": "执行"
        }
        lines.append(f'<node TEXT="⚠️ 风险评估" COLOR="{COLOR_MAP["orange"]}">')
        for key, label in risk_labels.items():
            level = ra.get(key, "—")
            color = RISK_COLORS.get(level, "#333333")
            lines.append(f'<node TEXT="{label}: {level}" COLOR="{color}"/>')
        lines.append('</node>')

    # 后续工作
    steps = summary.get("next_steps", [])
    if steps:
        lines.append(f'<node TEXT="📋 后续工作" COLOR="{COLOR_MAP["green"]}">')
        for step in steps:
            lines.append(f'<node TEXT="{escape_xml(step[:120])}"/>')
        lines.append('</node>')

    # 结论
    overall = summary.get("overall_conclusion", "")
    if overall:
        lines.append(f'<node TEXT="📌 阅卷结论" COLOR="#2F5496"><node TEXT="{escape_xml(overall[:200])}"/></node>')

    lines.append('</node>')  # end root
    lines.append('</map>')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return output_path


def generate_html_mindmap(data, output_path):
    """生成独立HTML交互式思维导图"""
    title = data.get("title", "阅卷笔录")
    summary = data.get("summary", {})
    date_str = datetime.now().strftime("%Y年%m月%d日")
    role_label = "原告" if data.get("reviewer_role") == "plaintiff" else "被告"

    # --- 案件信息 ---
    info_branch = f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["primary"]};">📋 案件信息</div>
      <div class="summary-panel">
        <b>案号：</b>{escape_xml(data.get("case_number", "—"))}<br>
        <b>法院：</b>{escape_xml(data.get("court", "—"))}<br>
        <b>案由：</b>{escape_xml(data.get("case_cause", "—"))}<br>
        <b>阅卷人：</b>{escape_xml(data.get("reviewer_name", "—"))}（{role_label}方）<br>
        <b>阅卷日期：</b>{escape_xml(data.get("review_date", date_str))}
      </div>
    </div>'''

    # --- 案卷概况 ---
    cats_html = ""
    cats = summary.get("document_categories", {})
    if cats:
        cats_html = "<br>".join(f"<b>{escape_xml(k)}：</b>{v} 份" for k, v in cats.items())

    overview_branch = f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["primary"]};">📊 案卷概况</div>
      <div class="summary-panel">
        <b>材料总数：</b>{summary.get("total_documents", 0)} 份<br>
        {cats_html}
      </div>
    </div>'''

    # --- 核心事实 ---
    core_facts_html = ""
    facts = summary.get("core_facts", "")
    if facts:
        core_facts_html = f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["primary"]};">📝 核心事实</div>
      <div class="summary-panel">{escape_xml(facts[:300])}</div>
    </div>'''

    # --- 大事记 ---
    timeline_html = ""
    events = summary.get("key_events", [])
    if events:
        items = ''.join(
            f'<div class="leaf" style="border-left-color:{COLOR_MAP["primary"]};"><div class="leaf-title">{escape_xml(ev.get("date", ""))}</div><div class="leaf-meta">{escape_xml(ev.get("event", ""))}</div><div class="leaf-detail"><b>来源：</b>{escape_xml(ev.get("source", ""))}</div></div>'
            for ev in events[:15]
        )
        timeline_html = f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["primary"]};">📅 案件大事记</div>
      <div class="branch-items">{items}</div>
    </div>'''

    # --- 争议焦点 ---
    disputes_html = ""
    disputes = summary.get("dispute_focus", [])
    if disputes:
        items = ''.join(
            f'<div class="leaf" style="border-left-color:{COLOR_MAP["red"]};"><div class="leaf-title" style="color:{COLOR_MAP["red"]};">🎯 {escape_xml(d)}</div></div>'
            for d in disputes
        )
        disputes_html = f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["red"]};">🎯 争议焦点</div>
      <div class="branch-items">{items}</div>
    </div>'''

    # --- 证据评估 ---
    evidence_html = ""
    ea = summary.get("evidence_assessment", {})
    if ea:
        gaps_html = ""
        gaps = ea.get("key_gaps", [])
        if gaps:
            gap_items = ''.join(
                f'<div class="leaf" style="border-left-color:{COLOR_MAP["red"]};"><div class="leaf-title" style="color:{COLOR_MAP["red"]};">{escape_xml(g)}</div></div>'
                for g in gaps
            )
            gaps_html = f'<div class="branch-items">{gap_items}</div>'

        evidence_html = f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["primary"]};">🔍 证据体系评估</div>
      <div class="summary-panel">
        <b>原告证据：</b>{escape_xml(ea.get("plaintiff_evidence_strength", "—"))}<br>
        <b>被告证据：</b>{escape_xml(ea.get("defendant_evidence_strength", "—"))}
      </div>
      <div class="branch-title" style="background:{COLOR_MAP["red"]}; margin-top:8px; font-size:12px;">⚠️ 证据缺口</div>
      {gaps_html}
    </div>'''

    # --- 法律分析 ---
    legal_html = ""
    la = summary.get("legal_analysis", {})
    if la:
        claim = escape_xml(la.get("claim_basis", "")[:200])
        case_items = ""
        cases = la.get("relevant_cases", [])
        if cases:
            case_items = ''.join(
                f'<div class="leaf" style="border-left-color:{COLOR_MAP["purple"]};"><div class="leaf-title" style="color:{COLOR_MAP["purple"]};">{escape_xml(c)}</div></div>'
                for c in cases
            )
        legal_html = f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["purple"]};">⚖️ 法律分析</div>
      <div class="summary-panel"><b>请求权基础：</b>{claim}</div>
      <div class="branch-items">{case_items}</div>
    </div>'''

    # --- 程序核查 ---
    procedure_html = ""
    checklist = data.get("procedure_checklist", [])
    if checklist:
        items = ''.join(
            f'<div class="leaf" style="border-left-color:{COLOR_MAP["primary"]};"><div class="leaf-title">{escape_xml(item.get("item", ""))}</div><div class="leaf-meta">状态: {escape_xml(item.get("status", ""))} | {escape_xml(item.get("note", ""))}</div></div>'
            for item in checklist
        )
        procedure_html = f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["primary"]};">✅ 程序核查</div>
      <div class="branch-items">{items}</div>
    </div>'''

    # --- 风险评估 ---
    risk_html = ""
    ra = summary.get("risk_assessment", {})
    if ra:
        risk_labels = {
            "fact_risk": "事实认定", "legal_risk": "法律适用",
            "evidence_risk": "证据", "procedure_risk": "程序", "enforcement_risk": "执行"
        }
        items = ''.join(
            f'<div class="leaf" style="border-left-color:{RISK_COLORS.get(ra.get(key, ""), "#333333")};"><div class="leaf-title" style="color:{RISK_COLORS.get(ra.get(key, ""), "#333333")};">{label}: {escape_xml(ra.get(key, "—"))}</div></div>'
            for key, label in risk_labels.items()
        )
        risk_html = f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["orange"]};">⚠️ 风险评估</div>
      <div class="branch-items">{items}</div>
    </div>'''

    # --- 后续工作 ---
    steps_html = ""
    steps = summary.get("next_steps", [])
    if steps:
        items = ''.join(
            f'<div class="leaf" style="border-left-color:{COLOR_MAP["green"]};"><div class="leaf-title">{i+1}. {escape_xml(s)}</div></div>'
            for i, s in enumerate(steps)
        )
        steps_html = f'''<div class="branch">
      <div class="branch-title" style="background:{COLOR_MAP["green"]};">📋 后续工作</div>
      <div class="branch-items">{items}</div>
    </div>'''

    # --- 结论 ---
    conclusion_html = ""
    overall = summary.get("overall_conclusion", "")
    if overall:
        conclusion_html = f'''<div class="bottom-lines"><h3>📌 阅卷结论</h3><p>{escape_xml(overall[:400])}</p></div>'''

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
.root-node {{ background: #2F5496; color: white; padding: 14px 28px; border-radius: 12px; font-size: 16px; font-weight: bold; text-align: center; max-width: 500px; box-shadow: 0 4px 12px rgba(47,84,150,0.3); }}
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
  <h1>阅卷笔录思维导图</h1>
  <small>{escape_xml(title)} &nbsp;|&nbsp; 生成于 {date_str}</small>
</div>
<div class="mindmap">
  <div class="tree">
    <div class="root-node">{escape_xml(title)}</div>
    <div class="connector"></div>
    <div class="branches">
      {info_branch}
      {overview_branch}
      {core_facts_html}
      {timeline_html}
      {disputes_html}
      {evidence_html}
      {legal_html}
      {procedure_html}
      {risk_html}
      {steps_html}
    </div>
    {conclusion_html}
  </div>
</div>
<div class="footer">双击卡片展开详情 &nbsp;|&nbsp; AI法律阅卷系统生成 &nbsp;|&nbsp; 律师内部工作文件 · 注意保密</div>
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
    parser = argparse.ArgumentParser(description='阅卷笔录思维导图生成器')
    parser.add_argument('--input', '-i', required=True, help='阅卷JSON文件路径')
    parser.add_argument('--output-dir', '-o', required=True, help='输出目录路径')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    os.makedirs(args.output_dir, exist_ok=True)

    # 生成 .mm 文件
    mm_path = os.path.join(args.output_dir, '阅卷笔录思维导图.mm')
    generate_freemind(data, mm_path)
    print(f"FreeMind思维导图: {mm_path}")

    # 生成 .html 文件
    html_path = os.path.join(args.output_dir, '阅卷笔录思维导图.html')
    generate_html_mindmap(data, html_path)
    print(f"HTML思维导图: {html_path}")

    return 0


if __name__ == '__main__':
    exit(main())
