#!/usr/bin/env python3
"""将DOCX文件转换为PDF。优先使用docx2pdf(需要Word)，回退到LibreOffice，再回退到python-docx2pdf。"""

import os
import sys
import argparse


def convert_docx2pdf(docx_path, pdf_path):
    """使用 docx2pdf (需要安装Word) 转换"""
    try:
        from docx2pdf import convert
        convert(docx_path, pdf_path)
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"  docx2pdf转换失败: {e}", file=sys.stderr)
        return False


def convert_libreoffice(docx_path, output_dir):
    """使用 LibreOffice 转换"""
    import subprocess
    try:
        subprocess.run([
            "soffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", output_dir,
            docx_path
        ], check=True, timeout=120,
           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def convert_python(docx_path, pdf_path):
    """使用 python-docx + reportlab 组合（最基础的保底方案）"""
    try:
        from docx import Document
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # 注册中文字体
        font_registered = False
        for font_path in [
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
        ]:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont("ChineseFont", font_path))
                    font_registered = True
                    break
                except Exception:
                    continue

        if not font_registered:
            return False

        doc = Document(docx_path)

        style = ParagraphStyle(
            'ChineseStyle',
            fontName='ChineseFont',
            fontSize=11,
            leading=18,
            spaceAfter=8,
        )

        story = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                story.append(Spacer(1, 6))
                continue

            alignment = TA_CENTER if para.alignment == 1 else TA_LEFT
            pstyle = ParagraphStyle(
                f'Style_{hash(text)}',
                fontName='ChineseFont',
                fontSize=11,
                leading=18,
                spaceAfter=6,
                alignment=alignment,
                wordSpace=2,
            )

            # 字体加粗
            is_bold = any(r.bold for r in para.runs if r.bold)
            story.append(Paragraph(f'<b>{text}</b>' if is_bold else text, pstyle))

        output_dir = os.path.dirname(pdf_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        pdf_doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                    topMargin=2.54*28.35, bottomMargin=2.54*28.35,
                                    leftMargin=3.18*28.35, rightMargin=3.18*28.35)
        pdf_doc.build(story)
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"  python转换失败: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description='DOCX转PDF转换器')
    parser.add_argument('input', help='输入DOCX文件路径')
    parser.add_argument('--output', '-o', default=None, help='输出PDF文件路径（默认与输入同目录同名）')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"错误：文件不存在 —— {args.input}", file=sys.stderr)
        return 1

    docx_path = os.path.abspath(args.input)
    if args.output:
        pdf_path = os.path.abspath(args.output)
    else:
        pdf_path = os.path.splitext(docx_path)[0] + '.pdf'

    print(f"正在转换: {docx_path}")

    # 按优先级尝试各种转换方式
    if convert_docx2pdf(docx_path, pdf_path):
        print(f"PDF已生成 (docx2pdf): {pdf_path}")
        return 0

    output_dir = os.path.dirname(pdf_path)
    if convert_libreoffice(docx_path, output_dir):
        # LibreOffice 生成的文件名在output_dir中与输入同名的.pdf
        generated_pdf = os.path.join(output_dir,
                                     os.path.splitext(os.path.basename(docx_path))[0] + '.pdf')
        if generated_pdf != pdf_path and os.path.exists(generated_pdf):
            os.rename(generated_pdf, pdf_path)
        print(f"PDF已生成 (LibreOffice): {pdf_path}")
        return 0

    if convert_python(docx_path, pdf_path):
        print(f"PDF已生成 (python): {pdf_path}")
        return 0

    print("错误：无法转换DOCX为PDF。请安装以下任一工具：", file=sys.stderr)
    print("  1. Microsoft Word + pip install docx2pdf", file=sys.stderr)
    print("  2. LibreOffice (需在PATH中)", file=sys.stderr)
    print("  3. pip install reportlab (基础保底)", file=sys.stderr)
    return 1


if __name__ == '__main__':
    exit(main())
