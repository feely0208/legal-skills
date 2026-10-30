#!/usr/bin/env python3
"""阅卷笔录生成器 —— 将JSON阅卷结果转为专业排版的Word文档(.docx)。"""

import json
import argparse
import os
from datetime import datetime

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

# 配色
COLORS = {
    "primary":   RGBColor(0x2F, 0x54, 0x96),  # 深蓝 - 标题/表头
    "red":       RGBColor(0xDC, 0x35, 0x45),  # 红色 - 高风险
    "orange":    RGBColor(0xFD, 0x7E, 0x14),  # 橙色 - 中风险
    "green":     RGBColor(0x19, 0x87, 0x54),  # 绿色 - 低风险/认可
    "purple":    RGBColor(0x6F, 0x42, 0xC1),  # 紫色 - 法律分析
    "gray":      RGBColor(0x66, 0x66, 0x66),  # 灰色 - 辅助文字
    "light_gray": RGBColor(0x99, 0x99, 0x99),
    "dark":      RGBColor(0x33, 0x33, 0x33),
}

RISK_COLORS = {
    "高": COLORS["red"],
    "中": COLORS["orange"],
    "低": COLORS["green"],
}


def set_cell_shading(cell, color_hex):
    """设置Word表格单元格背景色"""
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def add_run_to_para(para, text, font_name_en="Times New Roman",
                    font_name_cn="宋体", font_size=10.5,
                    bold=False, color=None):
    """向段落添加一个run"""
    run = para.add_run(text)
    run.font.size = Pt(font_size)
    run.font.name = font_name_en
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name_cn)
    run.bold = bold
    if color:
        run.font.color.rgb = color
    return run


def add_para(doc, text, color=None, bold=False, font_size=10.5,
             font_cn="宋体", font_en="Times New Roman",
             alignment=None, space_after=6, space_before=0,
             indent_first_line=None):
    """添加段落"""
    para = doc.add_paragraph()
    if alignment is not None:
        para.alignment = alignment
    pf = para.paragraph_format
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(space_before)
    if indent_first_line:
        pf.first_line_indent = Cm(indent_first_line)
    add_run_to_para(para, text, font_name_en=font_en, font_name_cn=font_cn,
                    font_size=font_size, bold=bold, color=color)
    return para


def add_heading_cn(doc, text, level=1):
    """添加中文标题（黑体）"""
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.name = "Times New Roman"
        run._element.rPr.rFonts.set(qn('w:eastAsia'), "黑体")
    return h


def add_section_divider(doc):
    """添加分节线"""
    add_para(doc, "—" * 60, font_size=8, color=COLORS["light_gray"],
             space_before=4, space_after=4)


def build_case_info_section(doc, data):
    """一、案件基本信息"""
    add_heading_cn(doc, "一、案件基本信息", level=1)

    info_table = doc.add_table(rows=0, cols=2)
    info_table.style = "Table Grid"

    fields = [
        ("案号", data.get("case_number", "—")),
        ("审理法院", data.get("court", "—")),
        ("案由", data.get("case_cause", "—")),
        ("审理阶段", data.get("trial_stage", "—")),
        ("审理程序", data.get("trial_procedure", "—")),
        ("开庭情况", data.get("court_hearing", "—")),
        ("原告", data.get("plaintiff_name", "—")),
        ("被告", data.get("defendant_name", "—")),
    ]

    third = data.get("third_parties", [])
    if third:
        fields.append(("第三人", "、".join(third)))

    fields += [
        ("阅卷人", data.get("reviewer_name", "—")),
        ("所在律所", data.get("reviewer_firm", "—")),
        ("阅卷日期", data.get("review_date", datetime.now().strftime("%Y年%m月%d日"))),
    ]

    for label, value in fields:
        row = info_table.add_row()
        c0, c1 = row.cells
        c0.text = ""
        c1.text = ""
        p0 = c0.paragraphs[0]
        r0 = p0.add_run(label)
        r0.font.size = Pt(10.5)
        r0.font.bold = True
        r0.font.name = "Times New Roman"
        r0._element.rPr.rFonts.set(qn('w:eastAsia'), "黑体")
        p0.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        set_cell_shading(c0, "E8ECF2")
        c0.width = Cm(3.5)

        p1 = c1.paragraphs[0]
        r1 = p1.add_run(value)
        r1.font.size = Pt(10.5)
        r1.font.name = "Times New Roman"
        r1._element.rPr.rFonts.set(qn('w:eastAsia'), "宋体")

    add_para(doc, "", font_size=4)


def build_document_list(doc, summary):
    """二、案卷材料清单"""
    add_heading_cn(doc, "二、案卷材料概况", level=1)

    total = summary.get("total_documents", 0)
    cats = summary.get("document_categories", {})

    add_para(doc, f"案卷材料共计 {total} 份，分类如下：", bold=True, font_size=11, space_after=6)

    for cat_name, count in cats.items():
        add_para(doc, f"● {cat_name}：{count} 份", font_size=10.5, indent_first_line=0.74)

    add_para(doc, "", font_size=4)


def build_timeline_section(doc, summary):
    """三、案件大事记"""
    add_heading_cn(doc, "三、案件大事记", level=1)

    events = summary.get("key_events", [])
    if not events:
        add_para(doc, "（暂无）", font_size=10.5, color=COLORS["gray"])
        return

    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    headers = ["时间", "事件", "来源"]
    hdr = table.rows[0]
    for i, h in enumerate(headers):
        hdr.cells[i].text = ""
        p = hdr.cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.name = "Times New Roman"
        r._element.rPr.rFonts.set(qn('w:eastAsia'), "黑体")
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        set_cell_shading(hdr.cells[i], "2F5496")

    for ev in events:
        row = table.add_row()
        cells = row.cells
        for i, key in enumerate(["date", "event", "source"]):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            r = p.add_run(str(ev.get(key, "")))
            r.font.size = Pt(9)
            r.font.name = "Times New Roman"
            r._element.rPr.rFonts.set(qn('w:eastAsia'), "宋体")
            if i == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    col_widths = [Cm(3.0), Cm(9.0), Cm(4.0)]
    for row in table.rows:
        for i, w in enumerate(col_widths):
            row.cells[i].width = w

    add_para(doc, "", font_size=4)


def build_claims_comparison(doc, data):
    """四、当事人主张对照"""
    comparisons = data.get("party_claims_comparison", [])
    if not comparisons:
        return

    add_heading_cn(doc, "四、当事人主张对照分析", level=1)

    table = doc.add_table(rows=1, cols=5)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    headers = ["争议事项", "原告主张", "被告主张", "相关证据", "分析意见"]
    hdr = table.rows[0]
    for i, h in enumerate(headers):
        hdr.cells[i].text = ""
        p = hdr.cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.size = Pt(8)
        r.font.bold = True
        r.font.name = "Times New Roman"
        r._element.rPr.rFonts.set(qn('w:eastAsia'), "黑体")
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        set_cell_shading(hdr.cells[i], "2F5496")

    for comp in comparisons:
        row = table.add_row()
        for i, key in enumerate(["issue", "plaintiff_claim", "defendant_claim", "related_evidence", "analysis"]):
            row.cells[i].text = ""
            p = row.cells[i].paragraphs[0]
            r = p.add_run(comp.get(key, ""))
            r.font.size = Pt(8)
            r.font.name = "Times New Roman"
            r._element.rPr.rFonts.set(qn('w:eastAsia'), "宋体")

    col_widths = [Cm(2.5), Cm(3.5), Cm(3.5), Cm(3.0), Cm(3.5)]
    for row in table.rows:
        for i, w in enumerate(col_widths):
            row.cells[i].width = w

    add_para(doc, "", font_size=4)


def build_evidence_assessment(doc, summary):
    """五、证据体系评估"""
    add_heading_cn(doc, "五、证据体系评估", level=1)

    ea = summary.get("evidence_assessment", {})
    if not ea:
        return

    add_para(doc, "【己方证据强度】", bold=True, font_size=11, font_cn="黑体", color=COLORS["primary"])
    add_para(doc, f'原告方证据：{ea.get("plaintiff_evidence_strength", "—")}', font_size=10.5, indent_first_line=0.74)
    add_para(doc, f'被告方证据：{ea.get("defendant_evidence_strength", "—")}', font_size=10.5, indent_first_line=0.74)

    gaps = ea.get("key_gaps", [])
    if gaps:
        add_para(doc, "【关键证据缺口】", bold=True, font_size=11, font_cn="黑体",
                 color=COLORS["red"], space_before=6)
        for g in gaps:
            add_para(doc, f"⚠ {g}", font_size=10.5, indent_first_line=0.74, color=COLORS["red"])

    add_para(doc, "", font_size=4)


def build_legal_analysis(doc, summary):
    """六、法律适用分析"""
    add_heading_cn(doc, "六、法律适用分析", level=1)

    la = summary.get("legal_analysis", {})
    if not la:
        return

    items = [
        ("请求权基础", la.get("claim_basis", "")),
        ("预期抗辩", la.get("defense_anticipated", [])),
        ("参考案例", la.get("relevant_cases", [])),
    ]

    for label, content in items:
        if content:
            add_para(doc, f"【{label}】", bold=True, font_size=11, font_cn="黑体",
                     color=COLORS["purple"], space_before=4)
            if isinstance(content, list):
                for item in content:
                    add_para(doc, f"● {item}", font_size=10.5, indent_first_line=0.74,
                             color=COLORS["purple"])
            else:
                add_para(doc, str(content), font_size=10.5, indent_first_line=0.74,
                         color=COLORS["purple"])

    add_para(doc, "", font_size=4)


def build_procedure_checklist(doc, data):
    """七、程序事项核查"""
    checklist = data.get("procedure_checklist", [])
    if not checklist:
        return

    add_heading_cn(doc, "七、程序事项核查", level=1)

    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    headers = ["核查事项", "状态", "说明"]
    hdr = table.rows[0]
    for i, h in enumerate(headers):
        hdr.cells[i].text = ""
        p = hdr.cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.name = "Times New Roman"
        r._element.rPr.rFonts.set(qn('w:eastAsia'), "黑体")
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        set_cell_shading(hdr.cells[i], "2F5496")

    for item in checklist:
        row = table.add_row()
        for i, key in enumerate(["item", "status", "note"]):
            row.cells[i].text = ""
            p = row.cells[i].paragraphs[0]
            val = item.get(key, "")
            r = p.add_run(val)
            r.font.size = Pt(9)
            r.font.name = "Times New Roman"
            r._element.rPr.rFonts.set(qn('w:eastAsia'), "宋体")
            if i == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    col_widths = [Cm(3.0), Cm(5.0), Cm(8.0)]
    for row in table.rows:
        for i, w in enumerate(col_widths):
            row.cells[i].width = w

    add_para(doc, "", font_size=4)


def build_risk_assessment(doc, summary):
    """八、风险评估"""
    add_heading_cn(doc, "八、风险评估", level=1)

    ra = summary.get("risk_assessment", {})
    if not ra:
        return

    risk_labels = {
        "fact_risk": "事实认定风险",
        "legal_risk": "法律适用风险",
        "evidence_risk": "证据风险",
        "procedure_risk": "程序风险",
        "enforcement_risk": "执行风险",
    }

    for key, label in risk_labels.items():
        level = ra.get(key, "—")
        color = RISK_COLORS.get(level, COLORS["dark"])
        add_para(doc, f"{label}：{level}", font_size=11, bold=True, font_cn="黑体",
                 color=color, indent_first_line=0.74, space_before=2)

    add_para(doc, "", font_size=4)


def build_next_steps(doc, summary):
    """九、后续工作建议"""
    add_heading_cn(doc, "九、后续工作建议", level=1)

    steps = summary.get("next_steps", [])
    if not steps:
        add_para(doc, "（暂无）", font_size=10.5, color=COLORS["gray"])
        return

    for i, step in enumerate(steps, 1):
        add_para(doc, f"{i}. {step}", font_size=10.5, indent_first_line=0.74, space_after=4)

    add_para(doc, "", font_size=4)


def build_core_facts(doc, summary):
    """核心事实摘要"""
    add_heading_cn(doc, "核心事实摘要", level=2)

    facts = summary.get("core_facts", "")
    if facts:
        add_para(doc, facts, font_size=10.5, indent_first_line=0.74, space_after=8)


def build_dispute_focus(doc, summary):
    """争议焦点"""
    disputes = summary.get("dispute_focus", [])
    if disputes:
        add_para(doc, "【预判争议焦点】", bold=True, font_size=11, font_cn="黑体",
                 color=COLORS["primary"], space_before=6)
        for d in disputes:
            add_para(doc, f"● {d}", font_size=10.5, indent_first_line=0.74)


def build_conclusion(doc, summary):
    """阅卷结论"""
    overall = summary.get("overall_conclusion", "")
    if overall:
        add_heading_cn(doc, "十、阅卷结论", level=1)
        add_para(doc, overall, font_size=11, indent_first_line=0.74, bold=True)


def generate_report(data, output_path):
    """主函数 —— 生成阅卷笔录"""
    doc = Document()

    # 页面设置 (A4纵向)
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.54)
    sec.bottom_margin = Cm(2.54)
    sec.left_margin = Cm(2.54)
    sec.right_margin = Cm(2.54)

    summary = data.get("summary", {})

    # ====== 封面 ======
    for _ in range(4):
        doc.add_paragraph()

    add_para(doc, "阅 卷 笔 录", bold=True, font_size=28,
             font_cn="黑体", alignment=WD_ALIGN_PARAGRAPH.CENTER,
             space_after=24)

    add_para(doc, data.get("title", "阅卷笔录"),
             font_size=15, font_cn="黑体",
             alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=16,
             color=COLORS["dark"])

    role_label = "原告" if data.get("reviewer_role") == "plaintiff" else "被告"
    info = [
        f'案号：{data.get("case_number", "—")}',
        f'审理法院：{data.get("court", "—")}',
        f'案由：{data.get("case_cause", "—")}',
        f'阅卷人：{data.get("reviewer_name", "—")}（{role_label}方代理人）',
        f'所在律所：{data.get("reviewer_firm", "—")}',
        f'阅卷日期：{data.get("review_date", datetime.now().strftime("%Y年%m月%d日"))}',
    ]
    for line in info:
        add_para(doc, line, font_size=12,
                 alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=4,
                 color=COLORS["gray"])

    add_para(doc, "", font_size=10)
    add_para(doc, "【内部工作文件 · 注意保密】", font_size=10,
             font_cn="黑体", bold=True,
             alignment=WD_ALIGN_PARAGRAPH.CENTER,
             color=COLORS["red"], space_after=8)

    doc.add_page_break()

    # ====== 核心事实摘要 ======
    build_core_facts(doc, summary)

    # ====== 一、案件基本信息 ======
    build_case_info_section(doc, data)

    # ====== 二、案卷材料概况 ======
    build_document_list(doc, summary)

    # ====== 三、案件大事记 ======
    doc.add_page_break()
    build_timeline_section(doc, summary)

    # ====== 争议焦点 ======
    build_dispute_focus(doc, summary)

    # ====== 四、当事人主张对照 ======
    doc.add_page_break()
    build_claims_comparison(doc, data)

    # ====== 五、证据体系评估 ======
    build_evidence_assessment(doc, summary)

    # ====== 六、法律适用分析 ======
    build_legal_analysis(doc, summary)

    # ====== 七、程序事项核查 ======
    build_procedure_checklist(doc, data)

    # ====== 八、风险评估 ======
    build_risk_assessment(doc, summary)

    # ====== 九、后续工作建议 ======
    build_next_steps(doc, summary)

    # ====== 十、阅卷结论 ======
    build_conclusion(doc, summary)

    # ====== 签署栏 ======
    add_para(doc, "", font_size=8, space_after=12)
    add_para(doc, "阅卷人（签名）：", font_size=11, font_cn="黑体",
             alignment=WD_ALIGN_PARAGRAPH.RIGHT)
    add_para(doc, f'日期：{" " * 24}', font_size=11, font_cn="黑体",
             alignment=WD_ALIGN_PARAGRAPH.RIGHT, space_after=8)

    # ====== 页脚 ======
    add_para(doc, "", font_size=6, space_after=12)
    add_para(doc, "本文件由AI法律阅卷系统生成，为律师内部工作文件，受律师—当事人保密特权保护。建议经执业律师复核后使用。",
             font_size=8, color=COLORS["light_gray"],
             alignment=WD_ALIGN_PARAGRAPH.CENTER)
    add_para(doc, f'生成时间：{datetime.now().strftime("%Y年%m月%d日 %H:%M")}',
             font_size=8, color=COLORS["light_gray"],
             alignment=WD_ALIGN_PARAGRAPH.CENTER)

    # 保存
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    doc.save(output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="阅卷笔录生成器")
    parser.add_argument("--input", "-i", required=True, help="阅卷JSON文件路径")
    parser.add_argument("--output", "-o", required=True, help="输出Word文档路径(.docx)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"错误：找不到输入文件 —— {args.input}")
        return 1

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSON解析错误：{e}")
        print("提示：请检查JSON字符串值中是否含有未转义的中文引号。")
        print("解决方案：将JSON值内部的中文双引号替换为「」或『』。")
        return 1

    path = generate_report(data, args.output)
    print(f"阅卷笔录已生成：{path}")
    print(f"共 {len(data.get('procedure_checklist', []))} 项程序核查事项")
    return 0


if __name__ == "__main__":
    exit(main())
