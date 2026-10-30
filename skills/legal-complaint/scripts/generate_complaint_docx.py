#!/usr/bin/env python3
"""起诉状生成器 —— 将JSON起诉状结果转为专业排版的Word文档(.docx)。"""

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

# 色彩定义
COLORS = {
    "dark_blue": RGBColor(0x2F, 0x54, 0x96),
    "red":       RGBColor(0xDC, 0x35, 0x45),
    "green":     RGBColor(0x19, 0x87, 0x54),
    "orange":    RGBColor(0xFD, 0x7E, 0x14),
    "blue":      RGBColor(0x0D, 0x6E, 0xFD),
    "gray":      RGBColor(0x66, 0x66, 0x66),
    "light_gray":RGBColor(0x99, 0x99, 0x99),
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


def format_party_info(data, party_type):
    """格式化当事人信息"""
    party = data.get(party_type, {})
    if not party:
        return ""

    lines = []
    if party.get("type") == "company":
        lines.append(party.get("name", ""))
        if party.get("credit_code"):
            lines.append(f'统一社会信用代码：{party["credit_code"]}')
        if party.get("address"):
            lines.append(f'住所地：{party["address"]}')
        if party.get("legal_rep"):
            lines.append(f'法定代表人：{party["legal_rep"]}，职务：{party.get("title", "")}')
        if party.get("phone"):
            lines.append(f'联系电话：{party["phone"]}')
    else:
        info_parts = [party.get("name", "")]
        if party.get("gender"):
            info_parts.append(party["gender"])
        if party.get("birth_date"):
            info_parts.append(f'{party["birth_date"]}出生')
        if party.get("ethnicity"):
            info_parts.append(party["ethnicity"])
        lines.append("，".join(info_parts))
        if party.get("id_number"):
            lines.append(f'身份证号码：{party["id_number"]}')
        if party.get("occupation"):
            lines.append(f'职业：{party["occupation"]}')
        if party.get("address"):
            lines.append(f'住址：{party["address"]}')
        if party.get("phone"):
            lines.append(f'联系电话：{party["phone"]}')
    return "\n".join(lines)


def build_claims_table(doc, claims):
    """生成诉讼请求汇总表"""
    add_heading_cn(doc, "诉讼请求汇总", level=2)

    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    headers = ["序号", "诉讼请求", "法律依据"]
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        for p in hdr_cells[i].paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.size = Pt(9)
                r.font.bold = True
                r.font.name = "黑体"
                r._element.rPr.rFonts.set(qn('w:eastAsia'), "黑体")
        set_cell_shading(hdr_cells[i], "2F5496")
        for p in hdr_cells[i].paragraphs:
            for r in p.runs:
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for item in claims:
        row = table.add_row()
        cells = row.cells
        cells[0].text = str(item.get("id", ""))
        cells[1].text = item.get("claim", "")
        cells[2].text = item.get("legal_basis", "")

        for cell in cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(8)
                    r.font.name = "宋体"
                    r._element.rPr.rFonts.set(qn('w:eastAsia'), "宋体")

    widths = [Cm(1.0), Cm(6.0), Cm(5.0)]
    for row in table.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = w


def build_evidence_table(doc, evidence_list):
    """生成证据清单表"""
    add_heading_cn(doc, "证据清单", level=2)

    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    headers = ["序号", "证据名称", "证据来源", "证明目的"]
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        for p in hdr_cells[i].paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.size = Pt(9)
                r.font.bold = True
                r.font.name = "黑体"
                r._element.rPr.rFonts.set(qn('w:eastAsia'), "黑体")
        set_cell_shading(hdr_cells[i], "198754")
        for p in hdr_cells[i].paragraphs:
            for r in p.runs:
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for item in evidence_list:
        row = table.add_row()
        cells = row.cells
        cells[0].text = str(item.get("id", ""))
        cells[1].text = item.get("name", "")
        cells[2].text = item.get("source", "")
        cells[3].text = item.get("proves", "")

        for cell in cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(8)
                    r.font.name = "宋体"
                    r._element.rPr.rFonts.set(qn('w:eastAsia'), "宋体")

    widths = [Cm(1.0), Cm(3.5), Cm(3.0), Cm(4.5)]
    for row in table.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = w


def generate_report(data, output_path):
    """主函数：生成起诉状Word文档"""
    doc = Document()

    # 页面设置 (A4)
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.54)
    sec.bottom_margin = Cm(2.54)
    sec.left_margin = Cm(3.18)
    sec.right_margin = Cm(3.18)

    plaintiff_role = data.get("plaintiff_role", "plaintiff")
    plaintiff = data.get("plaintiff", {})
    defendant = data.get("defendant", {})
    agent = data.get("agent", {})
    claims = data.get("claims", [])
    facts = data.get("facts_and_reasons", {})

    # ====== 封面 ======
    for _ in range(6):
        doc.add_paragraph()

    # 标题
    title = data.get("title", "民事起诉状")
    if "反诉" in title:
        main_title = "民 事 反 诉 状"
    elif "行政" in title:
        main_title = "行 政 起 诉 状"
    elif "民事" in title:
        main_title = "民 事 起 诉 状"
    else:
        main_title = title

    add_para(doc, main_title, bold=True, font_size=28,
             font_cn="黑体", alignment=WD_ALIGN_PARAGRAPH.CENTER,
             space_after=30)

    add_para(doc, title, font_size=16, font_cn="黑体",
             alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=20,
             color=RGBColor(0x33, 0x33, 0x33))

    info = [
        f'案由：{data.get("case_brief", "—")}',
        f'原告：{plaintiff.get("name", "—")}',
        f'被告：{defendant.get("name", "—")}',
        f'管辖法院：{data.get("court", "—")}',
        f'提交日期：{data.get("submission_date", datetime.now().strftime("%Y年%m月%d日"))}',
    ]
    for line in info:
        add_para(doc, line, font_size=13,
                 alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=6,
                 color=RGBColor(0x55, 0x55, 0x55))

    doc.add_page_break()

    # ====== 正文开始 ======

    # 一、当事人信息
    add_heading_cn(doc, "一、当事人信息", level=1)

    add_para(doc, "原告：", bold=True, font_size=11, font_cn="黑体",
             space_before=8)
    plaintiff_info = format_party_info(data, "plaintiff")
    add_para(doc, plaintiff_info, font_size=11, indent_first_line=0.74,
             space_after=4)

    add_para(doc, "", font_size=4)

    add_para(doc, "被告：", bold=True, font_size=11, font_cn="黑体",
             space_before=4)
    defendant_info = format_party_info(data, "defendant")
    add_para(doc, defendant_info, font_size=11, indent_first_line=0.74,
             space_after=4)

    # 代理人
    if agent.get("name"):
        add_para(doc, "", font_size=4)
        add_para(doc, "委托代理人：", bold=True, font_size=11, font_cn="黑体")
        agent_parts = [agent.get("name", "")]
        if agent.get("law_firm"):
            agent_parts.append(agent["law_firm"])
        if agent.get("license_no"):
            agent_parts.append(f'执业证号：{agent["license_no"]}')
        if agent.get("phone"):
            agent_parts.append(f'联系电话：{agent["phone"]}')
        add_para(doc, "，".join(agent_parts), font_size=11,
                 indent_first_line=0.74)

    add_para(doc, "", font_size=4, space_after=8)

    case_brief = data.get("case_brief", "—")
    add_para(doc, f'案由：{case_brief}', font_size=11, indent_first_line=0.74,
             space_after=4, bold=True)

    # ====== 二、诉讼请求 ======
    doc.add_page_break()
    add_heading_cn(doc, "二、诉讼请求", level=1)

    for item in claims:
        idx = item.get("id", "")
        claim = item.get("claim", "")
        calc = item.get("calculation_method", "")
        legal_basis = item.get("legal_basis", "")

        add_para(doc, f'{idx}. {claim}', bold=True, font_size=11,
                 font_cn="黑体", space_before=6, space_after=2)

        if calc:
            add_para(doc, f'（计算方式：{calc}）', font_size=10,
                     color=COLORS["gray"], indent_first_line=0.74, space_after=4)

        add_para(doc, "", font_size=2, space_after=8)

    # 诉讼费用一般最后一项后另起说明
    add_para(doc, f'以上诉讼请求共计{len(claims)}项。', font_size=10,
             color=COLORS["gray"], indent_first_line=0.74, space_after=8)

    # ====== 三、事实与理由 ======
    doc.add_page_break()
    add_heading_cn(doc, "三、事实与理由", level=1)

    # （一）案件基本事实
    case_facts = facts.get("case_facts", "")
    if case_facts:
        add_para(doc, "（一）案件基本事实", bold=True, font_size=13,
                 font_cn="黑体", space_before=8, space_after=8)

        for line in case_facts.split("\n"):
            line = line.strip()
            if line:
                add_para(doc, line, font_size=10.5, indent_first_line=0.74,
                         space_after=4)

    # （二）被告违约/侵权的事实
    defendant_breach = facts.get("defendant_breach", "")
    if defendant_breach:
        add_para(doc, "（二）被告违约/侵权的事实", bold=True, font_size=13,
                 font_cn="黑体", space_before=12, space_after=6)
        add_para(doc, defendant_breach, font_size=10.5, indent_first_line=0.74,
                 color=RGBColor(0x33, 0x33, 0x33), space_after=6)

    # （三）原告遭受的损失
    plaintiff_loss = facts.get("plaintiff_loss", "")
    if plaintiff_loss:
        add_para(doc, "（三）原告遭受的损失", bold=True, font_size=13,
                 font_cn="黑体", space_before=12, space_after=6)
        add_para(doc, plaintiff_loss, font_size=10.5, indent_first_line=0.74,
                 color=RGBColor(0x33, 0x33, 0x33), space_after=6)

    # （四）法律依据
    legal_basis = facts.get("legal_basis", [])
    if legal_basis:
        add_para(doc, "（四）法律依据", bold=True, font_size=13,
                 font_cn="黑体", space_before=12, space_after=6)

        for i, item in enumerate(legal_basis, 1):
            law = item.get("law", "")
            application = item.get("application", "")
            add_para(doc, f'{i}. {law}', bold=True, font_size=10.5,
                     color=COLORS["blue"], indent_first_line=0.74, space_after=2)
            if application:
                add_para(doc, application, font_size=10.5, indent_first_line=0.74,
                         color=RGBColor(0x33, 0x33, 0x33), space_after=4)

    # （五）证据和证据来源
    evidence_list = facts.get("evidence_list", [])
    if evidence_list:
        add_para(doc, "（五）证据和证据来源", bold=True, font_size=13,
                 font_cn="黑体", space_before=12, space_after=6)

        for item in evidence_list:
            eid = item.get("id", "")
            name = item.get("name", "")
            source = item.get("source", "")
            proves = item.get("proves", "")
            add_para(doc, f'{eid}. {name}', bold=True, font_size=10.5,
                     font_cn="黑体", indent_first_line=0.74, space_after=2)
            add_para(doc, f'来源：{source}；证明目的：{proves}',
                     font_size=10, indent_first_line=0.74,
                     color=COLORS["gray"], space_after=6)

    # 管辖依据
    jurisdiction = data.get("jurisdiction_basis", "")
    if jurisdiction:
        add_para(doc, "（六）管辖依据", bold=True, font_size=13,
                 font_cn="黑体", space_before=12, space_after=6)
        add_para(doc, jurisdiction, font_size=10.5, indent_first_line=0.74,
                 color=RGBColor(0x55, 0x55, 0x55), space_after=4)

    # 诉讼时效
    sol = data.get("statute_of_limitations", {})
    if sol:
        status = sol.get("status", "未届满")
        if status != "未届满":
            add_para(doc, "（七）诉讼时效说明", bold=True, font_size=13,
                     font_cn="黑体", space_before=12, space_after=6)
            add_para(doc, f'诉讼时效状态：{status}',
                     font_size=10.5, indent_first_line=0.74,
                     color=COLORS["red"] if status == "已届满" else COLORS["gray"],
                     space_after=4)
            if sol.get("note"):
                add_para(doc, sol["note"], font_size=10, indent_first_line=0.74,
                         color=COLORS["gray"], space_after=4)

    # ====== 四、结论 ======
    doc.add_page_break()
    add_heading_cn(doc, "四、结论", level=1)

    conclusion = data.get("conclusion", "")
    if conclusion:
        add_para(doc, conclusion, font_size=11, indent_first_line=0.74,
                 space_after=12)

    add_para(doc, "综上所述，恳请贵院依法查明事实，支持原告的全部诉讼请求。",
             font_size=11, indent_first_line=0.74, bold=True, space_after=16)

    # 此致 + 法院
    add_para(doc, "此致", font_size=11, font_cn="黑体",
             alignment=WD_ALIGN_PARAGRAPH.LEFT, space_after=4)
    add_para(doc, data.get("court", "XX人民法院"), font_size=12, bold=True,
             font_cn="黑体", alignment=WD_ALIGN_PARAGRAPH.LEFT, space_after=16)

    # 附件
    appendices = data.get("appendices", [])
    if appendices:
        add_para(doc, "附：", bold=True, font_size=10.5, font_cn="黑体",
                 space_after=4)
        for item in appendices:
            add_para(doc, item, font_size=10, indent_first_line=0.74,
                     space_after=2)
        add_para(doc, "", font_size=4, space_after=8)

    # 签名栏
    add_para(doc, f'原告（签名/盖章）：', font_size=11, font_cn="黑体",
             alignment=WD_ALIGN_PARAGRAPH.RIGHT)
    if agent.get("name"):
        add_para(doc, f'委托代理人（签名）：', font_size=11, font_cn="黑体",
                 alignment=WD_ALIGN_PARAGRAPH.RIGHT, space_after=8)
    else:
        add_para(doc, "", font_size=4, space_after=8)
    add_para(doc, f'日期：{" " * 20}', font_size=11, font_cn="黑体",
             alignment=WD_ALIGN_PARAGRAPH.RIGHT)

    # 页脚声明
    add_para(doc, "", font_size=6, space_after=12)
    add_para(doc, "本文件由AI法律文书系统生成，仅供律师参考，不构成正式法律意见。建议经执业律师复核后使用。",
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
    parser = argparse.ArgumentParser(description="起诉状生成器")
    parser.add_argument("--input", "-i", required=True, help="起诉状JSON文件路径")
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

    if "claims" not in data:
        print("错误：JSON缺少 'claims' 字段")
        return 1

    path = generate_report(data, args.output)
    print(f"起诉状已生成：{path}")
    print(f"共 {len(data.get('claims', []))} 项诉讼请求")
    return 0


if __name__ == "__main__":
    exit(main())
