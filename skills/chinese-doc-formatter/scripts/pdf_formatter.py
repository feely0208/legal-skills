#!/usr/bin/env python3
"""
党政机关公文排版格式生成器 — PDF 文档
严格遵循 GB/T 9704-2012 标准
"""

import argparse
import glob
import os

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


# 字号（磅）
FONT_SIZES = {
    '二号': 22,
    '三号': 16,
    '四号': 14,
}

# 行距（磅）
LINE_SPACING = {
    'title': 36,
    'body': 28,
}

# 页边距（cm）
MARGINS = {
    'top': 3.7,
    'bottom': 3.5,
    'left': 2.8,
    'right': 2.6,
}

# 三号字（16pt）字符宽度（磅），用于缩进换算
CHAR_PT = 16

# 各排版元素使用的字体（注册成功后按可用性调整）
FONTS = {
    'title': 'FangBold',      # 标题：仿宋加粗（二号）
    'body':  'FangSC',        # 正文：仿宋（四号）
    'h1':    'FangBold',      # 一级标题：仿宋加粗（三号）
    'h2':    'FangBold',      # 二级标题：仿宋加粗（三号）
    'h3':    'FangBold',      # 三级标题：仿宋加粗（三号）
    'h4':    'FangBold',      # 四级标题：仿宋加粗（三号）
    'mi_ji': 'FangSC',        # 版头：仿宋（与全文一致）
    'page':  'FangSC',        # 页码：仿宋
}


def _first_file(patterns):
    for pat in patterns:
        hits = sorted(glob.glob(pat, recursive=True))
        if hits:
            return hits[0]
    return None


def register_fonts():
    """注册系统字体（TTC 用 subfontIndex 指定字面）"""
    # 字体查找顺序：本 skill 自带 → 用户字体目录 → WPS 安装目录 → 系统目录。
    # ⚠ 2026-09-22 修正：原实现只从 WPS 安装路径找常规体，
    #   WPS 未安装 / 路径变化时 PDF 会静默退回宋体，与「全文仿宋」规范不符。
    #   现改为优先使用随 skill 分发的 fonts/FangS-SC.ttf，不再依赖外部应用。
    _here = os.path.dirname(os.path.abspath(__file__))
    _skill_fonts = os.path.join(_here, '..', 'fonts')
    _home_fonts = os.path.expanduser('~/Library/Fonts')

    songti = _first_file([
        '/System/Library/Fonts/Supplemental/Songti.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
    ])
    fangsong = _first_file([
        os.path.join(_skill_fonts, 'FangS-SC.ttf'),          # 随 skill 分发（首选）
        os.path.join(_home_fonts, 'FangS-SC.ttf'),           # 已装到用户字体目录
        '/Applications/wpsoffice.app/Contents/Resources/office6/fonts/FangS-SC.ttf',
        '/Applications/WPS Office.app/Contents/Resources/office6/fonts/FangS-SC.ttf',
        '/Applications/WPS*.app/Contents/Resources/office6/fonts/FangS-SC.ttf',
    ])
    bold_fang = _first_file([
        os.path.join(_skill_fonts, 'FangS-SC-Bold.ttf'),
        os.path.join(_home_fonts, 'FangS-SC-Bold.ttf'),
    ])

    ok = {}

    def reg(name, path, sub=None):
        try:
            pdfmetrics.registerFont(
                TTFont(name, path, subfontIndex=sub) if sub is not None
                else TTFont(name, path))
            ok[name] = True
        except Exception:
            ok[name] = False

    reg('SongSC', songti, 6)        # 宋体-简 常规体（兜底）
    reg('SongSCBold', songti, 1)    # 宋体-简 粗体（兜底）
    if fangsong:
        reg('FangSC', fangsong)     # 仿宋（WPS 自带，TrueType）
    reg('FangBold', bold_fang)      # 仿宋加粗（skill 自带，由 FangS-SC 生成）

    # 仿宋缺失时给出可操作的提示，避免静默退宋体导致排版不达标
    if not ok.get('FangSC'):
        import sys as _sys
        print('[提示] 未找到仿宋字体 FangS-SC.ttf，PDF 将退回首选宋体。\n'
              '       获取方式（任一）：\n'
              '         1) 将 fonts/FangS-SC.ttf 放到本 skill 的 fonts/ 目录\n'
              '         2) 复制到 ~/Library/Fonts/\n'
              '         3) 安装 WPS Office（自带该字体）', file=_sys.stderr)

    # 字体缺失时回退
    if not ok.get('FangSC'):
        for key in ('body', 'mi_ji', 'page'):
            FONTS[key] = 'SongSC'
    if not ok.get('FangBold'):
        for key in ('title', 'h1', 'h2', 'h3', 'h4'):
            FONTS[key] = 'SongSCBold' if ok.get('SongSCBold') else 'SongSC'
    if not ok.get('SongSC'):
        raise RuntimeError('系统缺少宋体字体，无法生成 PDF')


def make_style(font_name, font_size, alignment=TA_LEFT, leading=None,
               first_line_indent=0, left_indent=0, right_indent=0):
    """创建段落样式（wordWrap='CJK' 保证中文逐字换行）"""
    if leading is None:
        leading = font_size * 1.75
    return ParagraphStyle(
        f'style_{font_name}_{font_size}_{alignment}_{first_line_indent}_{left_indent}_{right_indent}',
        parent=getSampleStyleSheet()['Normal'],
        fontName=font_name,
        fontSize=font_size,
        alignment=alignment,
        firstLineIndent=first_line_indent,
        leftIndent=left_indent,
        rightIndent=right_indent,
        leading=leading,
        spaceBefore=0,
        spaceAfter=0,
        wordWrap='CJK',
    )


def markup_text(text):
    """转义 XML（全文统一仿宋，不再单独换西文字体）"""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def text_width_chars(text):
    """估算文本宽度（三号字为单位：汉字/全角=1，半角数字字母=0.5）"""
    return sum(0.5 if ord(ch) < 128 else 1.0 for ch in text)


def is_level1_title(line):
    """一级标题：一、二、三……"""
    return bool(line and line[0] in '一二三四五六七八九十'
                and len(line) > 1 and line[1] == '、')


def is_level2_title(line):
    """二级标题：（一）（二）（三）……"""
    return bool(line and line.startswith('（') and len(line) >= 4
                and line[1] in '一二三四五六七八九十' and line[2] == '）')


def is_level3_title(line):
    """三级标题：1. 2. 3. ……（半角或全角点）"""
    return bool(line and line[:1].isdigit() and len(line) >= 2
                and line[1] in '.．')


def is_level4_title(line):
    """四级标题：（1）（2）（3）……"""
    return bool(line and line.startswith('（') and len(line) >= 4
                and line[1].isdigit() and line[2] == '）')


def on_page(canvas, doc):
    """每页页脚页码：- n -，宋体四号，单页码居右空一字，双页码居左空一字"""
    canvas.saveState()
    canvas.setFont(FONTS['page'], FONT_SIZES['四号'])
    text = f'- {canvas.getPageNumber()} -'
    y = doc.bottomMargin * 0.55
    if canvas.getPageNumber() % 2 == 1:
        x = doc.pagesize[0] - doc.rightMargin - CHAR_PT
        canvas.drawRightString(x, y, text)
    else:
        x = doc.leftMargin + CHAR_PT
        canvas.drawString(x, y, text)
    canvas.restoreState()


def generate_pdf(args):
    """生成 PDF 文档"""
    register_fonts()

    output_path = args.output
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    filepath = os.path.join(output_path, args.filename or '公文.pdf')

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        topMargin=MARGINS['top'] * cm,
        bottomMargin=MARGINS['bottom'] * cm,
        leftMargin=MARGINS['left'] * cm,
        rightMargin=MARGINS['right'] * cm,
    )

    story = []
    body_size = FONT_SIZES['四号']
    heading_size = FONT_SIZES['三号']
    body_leading = LINE_SPACING['body']
    body_indent = int(2 * body_size)      # 正文首行缩进 2 字
    heading_indent = int(2 * heading_size)  # 小标题左空 2 字
    right4 = int(4 * body_size)    # 右空 4 字（按四号字宽）

    # === 版头信息 ===
    for text in (args.fen_hao, args.mi_ji, args.jin_ji_chengdu):
        if text:
            style = make_style(FONTS['mi_ji'], heading_size, TA_LEFT,
                               leading=body_leading)
            story.append(Paragraph(markup_text(text), style))

    if args.fa_wen_zi_hao:
        if args.shang_xing_wen:
            style = make_style(FONTS['body'], body_size, TA_LEFT,
                               leading=body_leading, left_indent=CHAR_PT)
        else:
            style = make_style(FONTS['body'], body_size, TA_CENTER,
                               leading=body_leading)
        story.append(Paragraph(markup_text(args.fa_wen_zi_hao), style))

    # === 标题 ===
    if args.title:
        title_style = make_style(FONTS['title'], FONT_SIZES['二号'], TA_CENTER,
                                 leading=LINE_SPACING['title'])
        story.append(Paragraph(markup_text(args.title), title_style))

    # === 正文 ===
    if args.body:
        for line in args.body.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            if is_level1_title(line):
                font, size = FONTS['h1'], heading_size
            elif is_level2_title(line):
                font, size = FONTS['h2'], heading_size
            elif is_level3_title(line):
                font, size = FONTS['h3'], heading_size
            elif is_level4_title(line):
                font, size = FONTS['h4'], heading_size
            else:
                font, size = FONTS['body'], body_size
            line_indent = heading_indent if size == heading_size else body_indent
            style = make_style(font, size, TA_JUSTIFY,
                               first_line_indent=line_indent,
                               leading=body_leading)
            story.append(Paragraph(markup_text(line), style))

    # === 附件说明 ===
    if args.attachment:
        story.append(Spacer(1, body_leading))
        style = make_style(FONTS['body'], body_size, TA_JUSTIFY,
                           first_line_indent=body_indent, leading=body_leading)
        story.append(Paragraph(markup_text(args.attachment), style))

    # === 发文机关署名和日期 ===
    if args.sender or args.date:
        sign_block = [Spacer(1, body_leading * 3)]
        if args.sender and args.date:
            sender_indent = max(0, round((4 + (text_width_chars(args.date)
                                               - text_width_chars(args.sender)) / 2)
                                         * body_size))
        else:
            sender_indent = right4
        if args.sender:
            style = make_style(FONTS['body'], body_size, TA_RIGHT,
                               leading=body_leading, right_indent=sender_indent)
            sign_block.append(Paragraph(markup_text(args.sender), style))
        if args.date:
            style = make_style(FONTS['body'], body_size, TA_RIGHT,
                               leading=body_leading, right_indent=right4)
            sign_block.append(Paragraph(markup_text(args.date), style))
        story.append(KeepTogether(sign_block))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f'PDF 文档已生成: {filepath}')
    return filepath


def main():
    parser = argparse.ArgumentParser(description='党政机关公文排版格式生成器 (.pdf)')
    parser.add_argument('--output', required=True, help='输出目录')
    parser.add_argument('--filename', default='公文.pdf', help='文件名')
    parser.add_argument('--title', default='', help='标题')
    parser.add_argument('--body', default='', help='正文内容（多行用换行分隔）')
    parser.add_argument('--sender', default='', help='发文机关署名')
    parser.add_argument('--date', default='', help='成文日期')
    parser.add_argument('--attachment', default='', help='附件说明')
    parser.add_argument('--fen_hao', default='', help='份号')
    parser.add_argument('--mi_ji', default='', help='密级')
    parser.add_argument('--jin_ji_chengdu', default='', help='紧急程度')
    parser.add_argument('--fa_wen_zi_hao', default='', help='发文字号')
    parser.add_argument('--shang_xing_wen', action='store_true',
                        help='上行文（发文字号左空一字）')

    args = parser.parse_args()
    generate_pdf(args)


if __name__ == '__main__':
    main()
