#!/usr/bin/env python3
"""质证意见书生成器 —— 将JSON质证结果转为专业排版的Word文档(.docx)。"""

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

# 四色定义
COLORS = {
    "red":    RGBColor(0xDC, 0x35, 0x45),   # 真实性问题
    "orange": RGBColor(0xFD, 0x7E, 0x14),   # 合法性问题
    "blue":   RGBColor(0x0D, 0x6E, 0xFD),   # 法律依据
    "green":  RGBColor(0x19, 0x87, 0x54),   # 关联性意见
    "purple": RGBColor(0x6F, 0x42, 0xC1),   # 证明目的反驳
}

RESULT_LABELS = {
    "认可": "认可",
    "不认可": "不认可",
    "无法确认": "无法确认",
}


def set_cell_shading(cell, color_hex):
    """设置Word表格单元格背景色"""
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def add_run_to_para(para, text, font_name_en="Times New Roman",
                    font_name_cn="宋体", font_size=10.5,
                    bold=False, color=None):
    """向段落添加一个run，正确设置中英文字体"""
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
        run.font.name = "黑体"
        run._element.rPr.rFonts.set(qn('w:eastAsia'), "黑体")
    return h


def add_section_tag(doc, label, color):
    """添加彩色标签"""
    para = doc.add_paragraph()
    pf = para.paragraph_format
    pf.space_after = Pt(4)
    pf.space_before = Pt(8)
    r = para.add_run(f"【{label}】")
    r.font.size = Pt(10)
    r.font.bold = True
    r.font.color.rgb = color
    r.font.name = "黑体"
    r._element.rPr.rFonts.set(qn('w:eastAsia'), "黑体")
    return para


def render_verdict(verdict):
    """渲染认可/不认可/无法确认的文本，带颜色"""
    if verdict == "认可":
        return ("✓ 认可", COLORS["green"])
    elif verdict == "不认可":
        return ("✗ 不认可", COLORS["red"])
    else:
        return ("? 无法确认", COLORS["orange"])


def add_evidence_item(doc, item):
    """渲染单份证据的质证意见"""
    idx = item.get("id", "")
    ev_name = item.get("evidence_name", "")
    ev_type = item.get("evidence_type", "")

    # 证据标题
    add_para(doc, f'证据{idx}：{ev_name}', bold=True,
             font_size=13, font_cn="黑体", space_before=16, space_after=2)
    if ev_type:
        add_para(doc, f'证据类型：{ev_type}', font_size=10,
                 color=RGBColor(0x66, 0x66, 0x66), space_after=4)

    # 举证方主张的证明目的
    purpose = item.get("proof_purpose", "")
    if purpose:
        add_para(doc, "【举证方证明目的】", bold=True, font_size=10.5,
                 font_cn="黑体", space_before=4)
        add_para(doc, purpose, font_size=10.5, indent_first_line=0.74,
                 color=RGBColor(0x55, 0x55, 0x55))

    # === 三性审查 ===
    add_para(doc, "—— 三性审查 ——", font_size=10, bold=True,
             font_cn="黑体", color=RGBColor(0x2F, 0x54, 0x96), space_before=8, space_after=4)

    # 真实性
    auth_verdict, auth_color = render_verdict(item.get("authenticity_verdict", "无法确认"))
    add_para(doc, f'一、真实性：{auth_verdict}', font_size=11, bold=True,
             font_cn="黑体", color=auth_color, space_before=4)
    txt = item.get("authenticity_opinion", "")
    if txt:
        add_para(doc, txt, font_size=10.5, indent_first_line=0.74, color=COLORS["red"])
    txt = item.get("authenticity_basis", "")
    if txt:
        add_para(doc, f'法律依据：{txt}', font_size=10, color=COLORS["blue"],
                 indent_first_line=0.74, space_after=2)

    # 合法性
    leg_verdict, leg_color = render_verdict(item.get("legality_verdict", "无法确认"))
    add_para(doc, f'二、合法性：{leg_verdict}', font_size=11, bold=True,
             font_cn="黑体", color=leg_color, space_before=6)
    txt = item.get("legality_opinion", "")
    if txt:
        add_para(doc, txt, font_size=10.5, indent_first_line=0.74, color=COLORS["orange"])
    txt = item.get("legality_basis", "")
    if txt:
        add_para(doc, f'法律依据：{txt}', font_size=10, color=COLORS["blue"],
                 indent_first_line=0.74, space_after=2)

    # 关联性
    rel_verdict, rel_color = render_verdict(item.get("relevance_verdict", "无法确认"))
    add_para(doc, f'三、关联性：{rel_verdict}', font_size=11, bold=True,
             font_cn="黑体", color=rel_color, space_before=6)
    txt = item.get("relevance_opinion", "")
    if txt:
        add_para(doc, txt, font_size=10.5, indent_first_line=0.74, color=COLORS["green"])
    txt = item.get("relevance_basis", "")
    if txt:
        add_para(doc, f'法律依据：{txt}', font_size=10, color=COLORS["blue"],
                 indent_first_line=0.74, space_after=2)

    # === 证明目的反驳 ===
    add_para(doc, "—— 证明目的意见 ——", font_size=10, bold=True,
             font_cn="黑体", color=COLORS["purple"], space_before=8, space_after=4)
    txt = item.get("purpose_rebuttal", "")
    if txt:
        add_para(doc, txt, font_size=10.5, indent_first_line=0.74, color=COLORS["purple"])

    # 案例参考
    txt = item.get("case_reference", "")
    if txt:
        add_para(doc, "【参考案例】", bold=True, font_size=10.5,
                 font_cn="黑体", color=COLORS["blue"], space_before=4)
        for line in txt.split("\n"):
            line = line.strip()
            if line:
                add_para(doc, line, font_size=10, color=COLORS["blue"],
                         indent_first_line=0.74)

    # 综合意见
    txt = item.get("overall_opinion", "")
    if txt:
        add_para(doc, "【综合意见】", bold=True, font_size=10.5,
                 font_cn="黑体", space_before=4)
        add_para(doc, txt, font_size=10.5, indent_first_line=0.74, bold=True)

    # 分隔线
    add_para(doc, "—" * 50, font_size=8,
             color=RGBColor(0xCC, 0xCC, 0xCC), space_before=8)


def build_summary_table(doc, evidence_items):
    """生成证据质证汇总表"""
    add_heading_cn(doc, "证据质证汇总表", level=2)

    table = doc.add_table(rows=1, cols=8)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    headers = ["编号", "证据名称", "类型", "真实性", "合法性", "关联性", "证明目的", "综合"]
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        for p in hdr_cells[i].paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.size = Pt(8)
                r.font.bold = True
                r.font.name = "黑体"
                r._element.rPr.rFonts.set(qn('w:eastAsia'), "黑体")
        set_cell_shading(hdr_cells[i], "2F5496")
        for p in hdr_cells[i].paragraphs:
            for r in p.runs:
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for item in evidence_items:
        row = table.add_row()
        cells = row.cells
        cells[0].text = str(item.get("id", ""))
        cells[1].text = item.get("evidence_name", "")
        cells[2].text = item.get("evidence_type", "")
        cells[3].text = item.get("authenticity_verdict", "")
        cells[4].text = item.get("legality_verdict", "")
        cells[5].text = item.get("relevance_verdict", "")
        cells[6].text = item.get("purpose_verdict", "")
        cells[7].text = item.get("overall_verdict", "")

        for cell in cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(8)
                    r.font.name = "宋体"
                    r._element.rPr.rFonts.set(qn('w:eastAsia'), "宋体")

        # 各行底色
        for idx, verdict_key in [(3, "authenticity_verdict"), (4, "legality_verdict"),
                                  (5, "relevance_verdict"), (6, "purpose_verdict")]:
            v = item.get(verdict_key, "")
            if v == "不认可":
                set_cell_shading(cells[idx], "FFCCCC")
            elif v == "认可":
                set_cell_shading(cells[idx], "D4EDDA")
            elif v == "无法确认":
                set_cell_shading(cells[idx], "FFF3CD")

    widths = [Cm(1.0), Cm(3.0), Cm(1.5), Cm(1.5), Cm(1.5), Cm(1.5), Cm(1.5), Cm(1.5)]
    for row in table.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = w


def generate_report(data, output_path):
    """主函数"""
    doc = Document()

    # 页面设置 (A4)
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.54)
    sec.bottom_margin = Cm(2.54)
    sec.left_margin = Cm(3.18)
    sec.right_margin = Cm(3.18)

    # ====== 封面 ======
    for _ in range(5):
        doc.add_paragraph()

    add_para(doc, "质 证 意 见 书", bold=True, font_size=28,
             font_cn="黑体", alignment=WD_ALIGN_PARAGRAPH.CENTER,
             space_after=30)

    add_para(doc, data.get("title", "质证意见书"),
             font_size=16, font_cn="黑体",
             alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=20,
             color=RGBColor(0x33, 0x33, 0x33))

    info = [
        f'案号：{data.get("case_number", "—")}',
        f'审理法院：{data.get("court", "—")}',
        f'质证人：{data.get("examiner_party", "—")}（{"原告" if data.get("examiner_role") == "plaintiff" else "被告"}）',
        f'代理人：{data.get("examiner_name", "—")}',
        f'提交日期：{data.get("submission_date", datetime.now().strftime("%Y年%m月%d日"))}',
    ]
    for line in info:
        add_para(doc, line, font_size=13,
                 alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=6,
                 color=RGBColor(0x55, 0x55, 0x55))

    doc.add_page_break()

    # ====== 总体质证意见 ======
    s = data.get("summary", {})
    add_heading_cn(doc, "一、总体质证意见", level=1)

    total = s.get("total_evidence", 0)
    ok_count = s.get("no_objection_count", 0)
    partial_count = s.get("partial_objection_count", 0)
    full_count = s.get("full_objection_count", 0)

    add_para(doc,
             f'对方共提交证据 {total} 份。其中：无异议 {ok_count} 份，部分异议 {partial_count} 份，完全异议 {full_count} 份。',
             bold=True, font_size=11, space_after=8)

    overall = s.get("overall_assessment", "")
    if overall:
        add_para(doc, "【整体评价】", bold=True, font_size=10.5, font_cn="黑体")
        add_para(doc, overall, font_size=10.5, indent_first_line=0.74)

    # 主要问题
    issues = s.get("main_issues", [])
    if issues:
        add_para(doc, "【对方证据体系主要问题】", bold=True, font_size=10.5,
                 font_cn="黑体", color=COLORS["red"], space_before=6)
        for item in issues:
            add_para(doc, f"● {item}", font_size=10.5,
                     color=COLORS["red"], indent_first_line=0.74)

    # 关键缺陷
    weaknesses = s.get("key_weaknesses", [])
    if weaknesses:
        add_para(doc, "【对方证据关键缺陷】", bold=True, font_size=10.5,
                 font_cn="黑体", color=COLORS["orange"], space_before=6)
        for item in weaknesses:
            add_para(doc, f"● {item}", font_size=10.5,
                     color=COLORS["orange"], indent_first_line=0.74)

    # ====== 证据质证汇总表 ======
    doc.add_page_break()
    add_heading_cn(doc, "二、证据质证汇总表", level=1)
    evidence_items = data.get("evidence_items", [])
    build_summary_table(doc, evidence_items)

    # ====== 逐份质证意见 ======
    doc.add_page_break()
    add_heading_cn(doc, "三、逐份质证意见", level=1)

    # 图例
    add_para(doc, "【图例说明】", bold=True, font_size=10, font_cn="黑体")
    legend = [
        ("■ 红色 = 真实性审查意见（不认可/异议）", COLORS["red"]),
        ("■ 橙色 = 合法性审查意见（不认可/异议）", COLORS["orange"]),
        ("■ 蓝色 = 法律依据与参考案例", COLORS["blue"]),
        ("■ 绿色 = 关联性审查意见（不认可/异议）", COLORS["green"]),
        ("■ 紫色 = 对证明目的的反驳意见", COLORS["purple"]),
    ]
    for txt, c in legend:
        add_para(doc, txt, color=c, font_size=9, space_after=2)

    add_para(doc, "", font_size=6)

    for item in evidence_items:
        add_evidence_item(doc, item)

    # ====== 结论 ======
    doc.add_page_break()
    add_heading_cn(doc, "四、结论", level=1)

    conclusion = s.get("conclusion", "")
    if conclusion:
        add_para(doc, conclusion, font_size=11, indent_first_line=0.74, space_after=12)

    add_para(doc, "综上所述，恳请人民法院依法审核认定上述证据，对对方提交的存在瑕疵的证据不予采信，依法公正裁判。",
             font_size=11, indent_first_line=0.74, bold=True, space_after=12)

    add_para(doc, "此致", font_size=11, font_cn="黑体",
             alignment=WD_ALIGN_PARAGRAPH.LEFT, space_after=4)
    add_para(doc, data.get("court", "XX人民法院"), font_size=12, bold=True,
             font_cn="黑体", alignment=WD_ALIGN_PARAGRAPH.LEFT, space_after=16)

    add_para(doc, f'质证人（签名）：', font_size=11, font_cn="黑体",
             alignment=WD_ALIGN_PARAGRAPH.RIGHT)
    add_para(doc, f'代理人（签名）：', font_size=11, font_cn="黑体",
             alignment=WD_ALIGN_PARAGRAPH.RIGHT, space_after=8)
    add_para(doc, f'日期：{" " * 20}', font_size=11, font_cn="黑体",
             alignment=WD_ALIGN_PARAGRAPH.RIGHT)

    # 页脚
    add_para(doc, "", font_size=6, space_after=12)
    add_para(doc, "本文件由AI法律质证系统生成，仅供律师参考，不构成正式法律意见。建议经执业律师复核后使用。",
             font_size=8, color=RGBColor(0x99, 0x99, 0x99),
             alignment=WD_ALIGN_PARAGRAPH.CENTER)
    add_para(doc, f'生成时间：{datetime.now().strftime("%Y年%m月%d日 %H:%M")}',
             font_size=8, color=RGBColor(0x99, 0x99, 0x99),
             alignment=WD_ALIGN_PARAGRAPH.CENTER)

    # 保存
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    doc.save(output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="质证意见书生成器")
    parser.add_argument("--input", "-i", required=True, help="质证JSON文件路径")
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

    if "evidence_items" not in data:
        print("错误：JSON缺少 'evidence_items' 字段")
        return 1

    path = generate_report(data, args.output)
    print(f"质证意见书已生成：{path}")
    print(f"共 {len(data.get('evidence_items', []))} 份证据质证意见")
    return 0


if __name__ == "__main__":
    exit(main())
