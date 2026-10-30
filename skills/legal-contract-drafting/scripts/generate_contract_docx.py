#!/usr/bin/env python3
"""合同文档生成器 —— 将JSON合同数据转为专业排版的Word文档。"""

import json
import argparse
import os
from datetime import datetime

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn


def set_run_font(run, font_name_en="Times New Roman", font_name_cn="仿宋",
                 font_size=16, bold=False, color=None):
    """设置run的字体（中西文分别设置）"""
    run.font.size = Pt(font_size)
    run.font.name = font_name_en
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name_cn)
    run.bold = bold
    if color:
        run.font.color.rgb = color


def add_para(doc, text, font_cn="仿宋", font_en="Times New Roman",
             font_size=16, bold=False, color=None, alignment=None,
             space_after=0, space_before=0, first_line_indent=None,
             line_spacing=1.5):
    """添加段落"""
    para = doc.add_paragraph()
    if alignment is not None:
        para.alignment = alignment
    pf = para.paragraph_format
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(space_before)
    pf.line_spacing = line_spacing
    if first_line_indent:
        pf.first_line_indent = Cm(first_line_indent)
    run = para.add_run(text)
    set_run_font(run, font_name_en=font_en, font_name_cn=font_cn,
                 font_size=font_size, bold=bold, color=color)
    return para


def add_title(doc, text):
    """添加合同标题——黑体二号加粗居中"""
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = para.paragraph_format
    pf.space_after = Pt(24)
    pf.space_before = Pt(12)
    pf.line_spacing = 1.5
    run = para.add_run(text)
    set_run_font(run, font_name_cn="黑体", font_size=22, bold=True)
    return para


def add_clause_title(doc, text):
    """添加条款标题——黑体三号加粗"""
    para = doc.add_paragraph()
    pf = para.paragraph_format
    pf.space_after = Pt(4)
    pf.space_before = Pt(12)
    pf.line_spacing = 1.5
    run = para.add_run(text)
    set_run_font(run, font_name_cn="黑体", font_size=16, bold=True)
    return para


def add_body(doc, text):
    """添加正文段落——仿宋三号，首行缩进2字符"""
    paragraphs = text.split('\n')
    for i, p_text in enumerate(paragraphs):
        stripped = p_text.strip()
        if not stripped:
            continue
        para = doc.add_paragraph()
        pf = para.paragraph_format
        pf.space_after = Pt(2)
        pf.space_before = Pt(2)
        pf.line_spacing = 1.5
        pf.first_line_indent = Cm(0.85)  # 约2个三号字
        run = para.add_run(stripped)
        set_run_font(run, font_name_cn="仿宋", font_size=16)


def add_party_info(doc, data):
    """添加当事人信息"""
    parties = data.get("parties", [])
    for party in parties:
        add_para(doc, f'{party.get("role", "")}：{party.get("name", "")}',
                 font_cn="仿宋", font_size=16, bold=True, space_after=2)
        info_lines = []
        if party.get("legal_rep"):
            info_lines.append(f'法定代表人：{party["legal_rep"]}')
        if party.get("credit_code"):
            info_lines.append(f'统一社会信用代码：{party["credit_code"]}')
        if party.get("address"):
            info_lines.append(f'地址：{party["address"]}')
        if party.get("contact"):
            contact_line = f'联系人：{party["contact"]}'
            if party.get("phone"):
                contact_line += f'　　电话：{party["phone"]}'
            if party.get("email"):
                contact_line += f'　　邮箱：{party["email"]}'
            info_lines.append(contact_line)
        for line in info_lines:
            add_para(doc, line, font_cn="仿宋", font_size=16, space_after=2,
                     first_line_indent=0.85)


def add_signature_block(doc, data):
    """添加签署栏"""
    sig = data.get("signatures", {})
    add_para(doc, "", font_size=10, space_after=16)

    for key in ["party_a", "party_b"]:
        party_sig = sig.get(key, {})
        if party_sig:
            add_para(doc, party_sig.get("name", ""), font_cn="仿宋",
                     font_size=16, space_after=8, space_before=12)
            add_para(doc, party_sig.get("legal_rep", "法定代表人/授权代表（签字）："),
                     font_cn="仿宋", font_size=16, space_after=8)
            add_para(doc, party_sig.get("date_label", "签订日期：    年    月    日"),
                     font_cn="仿宋", font_size=16, space_after=16)


def add_separator(doc):
    """添加分隔线"""
    add_para(doc, "—" * 36, font_size=10,
             color=RGBColor(0xBB, 0xBB, 0xBB),
             alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)


def generate_contract(data, output_path):
    """主函数——生成合同Word文档"""
    doc = Document()

    # 页面设置 (A4)
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.54)
    sec.bottom_margin = Cm(2.54)
    sec.left_margin = Cm(3.18)
    sec.right_margin = Cm(3.18)

    title = data.get("title", "合同")

    # ====== 封面页 ======
    for _ in range(6):
        doc.add_paragraph()

    add_para(doc, "合　　同", font_cn="黑体", font_size=36, bold=True,
             alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=30,
             color=RGBColor(0x2F, 0x54, 0x96))

    add_para(doc, title, font_cn="黑体", font_size=22, bold=True,
             alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=18)

    contract_type = data.get("contract_type", "")
    if contract_type:
        add_para(doc, f'（{contract_type}）', font_cn="仿宋", font_size=16,
                 alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=36,
                 color=RGBColor(0x66, 0x66, 0x66))

    date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    place_str = data.get("place", "")
    add_para(doc, f'签订日期：{date_str}',
             font_cn="仿宋", font_size=16,
             alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)
    if place_str:
        add_para(doc, f'签订地点：{place_str}',
                 font_cn="仿宋", font_size=16,
                 alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)

    doc.add_page_break()

    # ====== 正文首页 ======
    # 合同标题
    add_title(doc, title)

    # 当事人信息
    add_party_info(doc, data)

    # 鉴于条款/前言
    preamble = data.get("preamble", "")
    if preamble:
        add_para(doc, "", font_size=10, space_after=4)
        add_body(doc, preamble)

    add_separator(doc)

    # ====== 逐条写入条款 ======
    clauses = data.get("clauses", [])
    for clause in clauses:
        title_text = clause.get("title", "")
        content = clause.get("content", "")

        if title_text:
            add_clause_title(doc, title_text)
        if content:
            add_body(doc, content)

    # ====== 签署页 ======
    doc.add_page_break()
    add_para(doc, "（此页以下无正文，为签署页）", font_cn="仿宋",
             font_size=12, color=RGBColor(0x99, 0x99, 0x99),
             alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=24)

    add_signature_block(doc, data)

    # 页脚声明
    add_para(doc, "", font_size=10, space_after=12)
    add_para(doc, "本合同由AI法律草拟系统生成，仅供参考，建议律师复核后使用。",
             font_cn="仿宋", font_size=9,
             color=RGBColor(0xAA, 0xAA, 0xAA),
             alignment=WD_ALIGN_PARAGRAPH.CENTER)
    add_para(doc, f'生成时间：{datetime.now().strftime("%Y年%m月%d日 %H:%M")}',
             font_cn="仿宋", font_size=9,
             color=RGBColor(0xAA, 0xAA, 0xAA),
             alignment=WD_ALIGN_PARAGRAPH.CENTER)

    # 保存
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    doc.save(output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="合同文档生成器")
    parser.add_argument("--input", "-i", required=True, help="合同JSON文件路径")
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

    if "clauses" not in data:
        print("错误：JSON缺少 'clauses' 字段")
        return 1

    path = generate_contract(data, args.output)
    print(f"合同文档已生成：{path}")
    print(f"共 {len(data.get('clauses', []))} 条条款")
    return 0


if __name__ == "__main__":
    exit(main())
