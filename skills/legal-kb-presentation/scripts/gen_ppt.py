#!/usr/bin/env python3
"""
Legal-KB 演示 PPT 生成器
生成科技风演示 PPT，包含中英文对照的模块介绍
"""

import argparse
import os
import sys
import json
from pathlib import Path
from datetime import datetime

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt, Emu
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.oxml.ns import nsmap
except ImportError:
    print("Error: python-pptx not installed. Run: pip3 install python-pptx")
    sys.exit(1)


# 科技风配色
COLORS = {
    'bg_dark': RGBColor(10, 14, 39),      # 深蓝黑背景
    'bg_card': RGBColor(26, 31, 58),      # 卡片背景
    'accent_blue': RGBColor(0, 212, 255),  # 霓虹蓝
    'accent_cyan': RGBColor(0, 255, 204),  # 青色
    'accent_pink': RGBColor(255, 0, 128),  # 粉色点缀
    'text_primary': RGBColor(255, 255, 255),  # 主文字
    'text_secondary': RGBColor(180, 190, 220),  # 次要文字
    'text_muted': RGBColor(120, 130, 160),  # 弱化文字
    'gradient_start': RGBColor(0, 100, 200),  # 渐变起始
    'gradient_end': RGBColor(0, 212, 255),  # 渐变结束
}


def add_background(slide, color=None):
    """设置幻灯片背景"""
    if color:
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = color
    else:
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = COLORS['bg_dark']


def add_text_box(slide, left, top, width, height, text, font_size=18,
                 color=None, bold=False, alignment=PP_ALIGN.LEFT, font_name='Microsoft YaHei'):
    """添加文本框"""
    shape = slide.shapes.add_textbox(Inches(left), Inches(top),
                                     Inches(width), Inches(height))
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    if color:
        p.font.color.rgb = color
    else:
        p.font.color.rgb = COLORS['text_primary']
    return shape


def add_title_shape(slide, left, top, width, height, text, font_size=44,
                    color=None, bold=True):
    """添加标题样式文本框（带发光效果）"""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(left), Inches(top),
        Inches(width), Inches(height)
    )
    shape.fill.background()
    shape.line.fill.background()

    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.name = 'Microsoft YaHei'
    p.alignment = PP_ALIGN.CENTER
    if color:
        p.font.color.rgb = color
    else:
        p.font.color.rgb = COLORS['accent_cyan']
    return shape


def add_accent_line(slide, left, top, width, color=None):
    """添加装饰线条"""
    if color is None:
        color = COLORS['accent_blue']
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(left), Inches(top),
        Inches(width), Inches(0.03)
    )
    line.fill.solid()
    line.fill.fore_color.rgb = color
    line.line.fill.background()
    return line


def add_icon_card(slide, left, top, width, height, icon, title, subtitle,
                  description=""):
    """添加图标卡片"""
    # 卡片背景
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top),
        Inches(width), Inches(height)
    )
    card.fill.solid()
    card.fill.fore_color.rgb = COLORS['bg_card']
    card.line.color.rgb = COLORS['accent_blue']
    card.line.width = Pt(1)

    # 图标
    add_text_box(slide, left + 0.15, top + 0.1, 0.6, 0.5,
                 icon, font_size=28, color=COLORS['accent_cyan'],
                 alignment=PP_ALIGN.CENTER)

    # 标题
    add_text_box(slide, left + 0.15, top + 0.55, width - 0.3, 0.35,
                 title, font_size=14, color=COLORS['text_primary'], bold=True)

    # 副标题
    if subtitle:
        add_text_box(slide, left + 0.15, top + 0.85, width - 0.3, 0.25,
                     subtitle, font_size=10, color=COLORS['text_secondary'])

    # 描述
    if description:
        add_text_box(slide, left + 0.15, top + 1.1, width - 0.3, 0.6,
                     description, font_size=9, color=COLORS['text_muted'])

    return card


def scan_kb_structure(kb_path):
    """扫描知识库结构"""
    modules = []
    root = Path(kb_path)

    for dir_path in sorted(root.iterdir()):
        if dir_path.is_dir() and dir_path.name.startswith('0'):
            name = dir_path.name
            # 提取中文名
            chinese_name = name.split('-', 1)[1] if '-' in name else name
            # 获取子目录
            sub_dirs = [d.name for d in dir_path.iterdir() if d.is_dir()][:5]
            # 计算文件数
            file_count = sum(1 for _ in dir_path.rglob('*.md'))
            modules.append({
                'path': str(dir_path),
                'name': name,
                'chinese': chinese_name,
                'subdirs': sub_dirs,
                'files': file_count
            })

    return modules


def generate_ppt(output_dir, kb_path=None, add_images=False):
    """生成演示 PPT"""
    if kb_path is None:
        kb_path = "/Users/mac/Legal-KB"

    # 扫描知识库
    modules = scan_kb_structure(kb_path)

    # 创建 PPT
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # 封面页
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # 空白布局
    add_background(slide)

    # 标题
    add_text_box(slide, 0.5, 2.0, 12.333, 1.0,
                 "Legal-KB", font_size=72, color=COLORS['accent_cyan'],
                 bold=True, alignment=PP_ALIGN.CENTER)

    # 副标题
    add_text_box(slide, 0.5, 3.0, 12.333, 0.6,
                 "律师专属知识库系统", font_size=36, color=COLORS['text_primary'],
                 alignment=PP_ALIGN.CENTER)

    # 英文副标题
    add_text_box(slide, 0.5, 3.6, 12.333, 0.4,
                 "Lawyer Exclusive Knowledge Base System",
                 font_size=18, color=COLORS['text_secondary'],
                 alignment=PP_ALIGN.CENTER)

    # 装饰线
    add_accent_line(slide, 4.5, 4.2, 4.333, COLORS['accent_blue'])

    # 底部信息
    today = datetime.now().strftime("%Y-%m-%d")
    add_text_box(slide, 0.5, 6.5, 12.333, 0.5,
                 f"演示日期: {today}  |  基于 Obsidian 知识库平台",
                 font_size=14, color=COLORS['text_muted'],
                 alignment=PP_ALIGN.CENTER)

    # 项目概述页
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide)
    add_title_shape(slide, 0.5, 0.3, 12.333, 0.8, "项目概述", 36,
                    COLORS['accent_cyan'])
    add_accent_line(slide, 0.5, 1.1, 1.5, COLORS['accent_blue'])

    overview_text = """• 基于 Obsidian 构建的律师执业全流程知识管理工具
• 覆盖法律法规、文书模板、案例库、案件管理、企业顾问、实务技能等核心模块
• 支持动态资讯自动抓取（每日 9:30 定时更新）
• 集成 AI 辅助写作（起诉状、合同、答辩状等）
• 多标签体系支持快速检索和关联分析"""

    add_text_box(slide, 0.5, 1.5, 12.333, 5.5, overview_text,
                 font_size=20, color=COLORS['text_primary'])

    # 知识库结构页
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide)
    add_title_shape(slide, 0.5, 0.3, 12.333, 0.8, "知识库结构", 36,
                    COLORS['accent_cyan'])
    add_accent_line(slide, 0.5, 1.1, 1.5, COLORS['accent_blue'])

    # 模块列表（两列布局）
    col_width = 6.0
    col1_x, col2_x = 0.5, 6.8
    row_y = 1.5
    row_height = 0.55

    module_icons = ['📌', '🏠', '⚖️', '📄', '📚', '📁', '🏢', '🛠️', '📰', '📝', '🔗', '📦', '💡', '🏗️']

    for i, mod in enumerate(modules[:14]):
        col = 0 if i < 7 else 1
        x = col1_x if col == 0 else col2_x
        y = row_y + (i % 7) * row_height

        # 模块卡片
        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y),
            Inches(col_width), Inches(0.45)
        )
        card.fill.solid()
        card.fill.fore_color.rgb = COLORS['bg_card']
        card.line.fill.background()

        # 图标 + 名称
        text = f"{module_icons[i] if i < len(module_icons) else '•'} {mod['chinese']} ({mod['name'].split('-')[0]})"
        tf = card.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(13)
        p.font.name = 'Microsoft YaHei'
        p.font.color.rgb = COLORS['text_primary']
        p.alignment = PP_ALIGN.LEFT

    # 核心功能页
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide)
    add_title_shape(slide, 0.5, 0.3, 12.333, 0.8, "核心功能", 36,
                    COLORS['accent_cyan'])
    add_accent_line(slide, 0.5, 1.1, 1.5, COLORS['accent_blue'])

    features = [
        ("📂", "知识库管理", "Knowledge Management",
         "全模块知识归档、标签分类、快速检索"),
        ("📅", "每日资讯", "Daily News",
         "自动抓取最高人民法院、最高检、司法部动态"),
        ("✍️", "AI 辅助写作", "AI Writing",
         "起诉状、合同、答辩状自动生成"),
        ("📊", "案件看板", "Case Kanban",
         "拖拽式案件进度管理"),
        ("🔔", "定时任务", "Scheduled Tasks",
         "launchd 自动执行，邮件通知"),
        ("🏷️", "标签体系", "Tag System",
         "民商事、刑事、劳动等多维度标签"),
    ]

    for i, (icon, title_cn, title_en, desc) in enumerate(features):
        row = i // 3
        col = i % 3
        x = 0.5 + col * 4.2
        y = 1.5 + row * 2.8

        add_icon_card(slide, x, y, 4.0, 2.5, icon, title_cn, title_en, desc)

    # 技术架构页
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide)
    add_title_shape(slide, 0.5, 0.3, 12.333, 0.8, "技术架构", 36,
                    COLORS['accent_cyan'])
    add_accent_line(slide, 0.5, 1.1, 1.5, COLORS['accent_blue'])

    arch_text = """┌─────────────────────────────────────────────────────────────┐
│                    用户交互层 (User Interface)                 │
│   Obsidian (Markdown 编辑器)  │  Web Dashboard (待开发)       │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    核心逻辑层 (Core Logic)                    │
│   Python 脚本  │  Obsidian Plugins  │  Claude Agent          │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    自动化层 (Automation)                      │
│   launchd 定时任务  │  agently-cli 邮件  │  动态资讯抓取        │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    数据层 (Data Layer)                        │
│   Obsidian Vault  │  Markdown 文件  │  外部 API (Agnes AI)    │
└─────────────────────────────────────────────────────────────┘"""

    add_text_box(slide, 0.5, 1.5, 12.333, 5.5, arch_text,
                 font_size=14, color=COLORS['accent_cyan'],
                 font_name='Menlo')

    # 每日动态页
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide)
    add_title_shape(slide, 0.5, 0.3, 12.333, 0.8, "每日动态资讯", 36,
                    COLORS['accent_cyan'])
    add_accent_line(slide, 0.5, 1.1, 1.5, COLORS['accent_blue'])

    flow_text = """每日 9:30 自动执行流程：

1. launchd 触发 daily_legal_news.py 脚本
   ↓
2. 抓取最高人民法院、最高人民检察院、司法部官网资讯
   ↓
3. 解析 HTML，提取标题和链接
   ↓
4. 生成 Obsidian Markdown 笔记
   ↓
5. 更新动态资讯索引
   ↓
6. 生成汇总文件
   ↓
7. 通过 agently-cli 发送邮件通知
   ↓
8. 自动打开 Obsidian 查看最新内容"""

    add_text_box(slide, 0.5, 1.5, 12.333, 5.5, flow_text,
                 font_size=18, color=COLORS['text_primary'],
                 font_name='Menlo')

    # 标签体系页
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide)
    add_title_shape(slide, 0.5, 0.3, 12.333, 0.8, "标签体系", 36,
                    COLORS['accent_cyan'])
    add_accent_line(slide, 0.5, 1.1, 1.5, COLORS['accent_blue'])

    tags_cn = ['民商事', '刑事', '劳动', '家事', '非诉', '知识产权', '建设工程', '在办', '已结', '模板', '案例', '法律法规']
    tags_en = ['Civil', 'Criminal', 'Labor', 'Family', 'Non-litigation', 'IP', 'Construction', 'Active', 'Closed', 'Template', 'Case', 'Law']

    for i, (cn, en) in enumerate(zip(tags_cn, tags_en)):
        col = i % 6
        row = i // 6
        x = 0.5 + col * 2.1
        y = 1.5 + row * 1.2

        tag = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y),
            Inches(1.9), Inches(0.9)
        )
        tag.fill.solid()
        tag.fill.fore_color.rgb = COLORS['bg_card']
        tag.line.color.rgb = COLORS['accent_blue']
        tag.line.width = Pt(1)

        tf = tag.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = cn
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.name = 'Microsoft YaHei'
        p.font.color.rgb = COLORS['accent_cyan']
        p.alignment = PP_ALIGN.CENTER

        p2 = tf.add_paragraph()
        p2.text = en
        p2.font.size = Pt(10)
        p2.font.name = 'Microsoft YaHei'
        p2.font.color.rgb = COLORS['text_secondary']
        p2.alignment = PP_ALIGN.CENTER

    # 推荐插件页
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide)
    add_title_shape(slide, 0.5, 0.3, 12.333, 0.8, "推荐插件", 36,
                    COLORS['accent_cyan'])
    add_accent_line(slide, 0.5, 1.1, 1.5, COLORS['accent_blue'])

    plugins = [
        ("Dataview", "数据查询", "自动生成案件列表、案例检索表"),
        ("Templater", "模板引擎", "新建案件/案例时自动填充标准模板"),
        ("Calendar", "日历视图", "日程管理与案件开庭日历"),
        ("Kanban", "看板管理", "拖拽式案件进度管理"),
        ("Advanced Tables", "表格增强", "表格编辑增强功能"),
        ("Periodic Notes", "周期笔记", "每日/每周/每月笔记"),
        ("Obsidian Git", "版本控制", "自动备份到 Git 仓库"),
    ]

    for i, (name, cn, desc) in enumerate(plugins):
        y = 1.5 + i * 0.85
        # 插件名称
        add_text_box(slide, 0.5, y, 2.5, 0.4, name,
                     font_size=16, color=COLORS['accent_cyan'], bold=True)
        # 中文名
        add_text_box(slide, 3.0, y, 2.0, 0.4, cn,
                     font_size=14, color=COLORS['text_primary'])
        # 描述
        add_text_box(slide, 5.0, y, 7.8, 0.4, desc,
                     font_size=12, color=COLORS['text_secondary'])

    # 快速开始页
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide)
    add_title_shape(slide, 0.5, 0.3, 12.333, 0.8, "快速开始", 36,
                    COLORS['accent_cyan'])
    add_accent_line(slide, 0.5, 1.1, 1.5, COLORS['accent_blue'])

    steps = [
        ("1", "打开 Obsidian", "Open Obsidian",
         "选择「打开文件夹作为仓库」"),
        ("2", "选择路径", "Select Path",
         "选择 Legal-KB 目录"),
        ("3", "安装插件", "Install Plugins",
         "社区插件：Dataview、Templater、Kanban"),
        ("4", "开始使用", "Start Using",
         "从工作台开始管理案件"),
    ]

    for i, (num, cn, en, desc) in enumerate(steps):
        x = 0.5 + i * 3.2
        # 步骤编号
        num_shape = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, Inches(x), Inches(1.8),
            Inches(0.8), Inches(0.8)
        )
        num_shape.fill.solid()
        num_shape.fill.fore_color.rgb = COLORS['accent_blue']
        num_shape.line.fill.background()

        tf = num_shape.text_frame
        p = tf.paragraphs[0]
        p.text = num
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = COLORS['bg_dark']
        p.alignment = PP_ALIGN.CENTER

        # 标题
        add_text_box(slide, x - 0.2, 2.8, 2.5, 0.5, cn,
                     font_size=18, color=COLORS['text_primary'], bold=True,
                     alignment=PP_ALIGN.CENTER)
        # 英文
        add_text_box(slide, x - 0.2, 3.3, 2.5, 0.4, en,
                     font_size=12, color=COLORS['text_secondary'],
                     alignment=PP_ALIGN.CENTER)
        # 描述
        add_text_box(slide, x - 0.2, 3.8, 2.5, 1.5, desc,
                     font_size=12, color=COLORS['text_muted'],
                     alignment=PP_ALIGN.CENTER)

    # 结尾页
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide)

    add_text_box(slide, 0.5, 2.5, 12.333, 1.0,
                 "Legal-KB", font_size=60, color=COLORS['accent_cyan'],
                 bold=True, alignment=PP_ALIGN.CENTER)
    add_text_box(slide, 0.5, 3.5, 12.333, 0.6,
                 "律师专属知识库系统", font_size=28, color=COLORS['text_primary'],
                 alignment=PP_ALIGN.CENTER)
    add_text_box(slide, 0.5, 4.1, 12.333, 0.4,
                 "Lawyer Exclusive Knowledge Base System",
                 font_size=16, color=COLORS['text_secondary'],
                 alignment=PP_ALIGN.CENTER)

    add_accent_line(slide, 4.5, 4.7, 4.333, COLORS['accent_blue'])

    add_text_box(slide, 0.5, 6.0, 12.333, 0.5,
                 "感谢观看  |  Thank You",
                 font_size=20, color=COLORS['text_muted'],
                 alignment=PP_ALIGN.CENTER)

    # 保存 PPT
    ppt_path = Path(output_dir) / "Legal-KB-演示.pptx"
    prs.save(str(ppt_path))
    print(f"✅ PPT 已生成: {ppt_path}")
    return str(ppt_path)


def main():
    parser = argparse.ArgumentParser(description='Legal-KB 演示 PPT 生成器')
    parser.add_argument('--output', '-o', default='/Users/mac/git/Legal-KB-Presentation',
                        help='输出目录')
    parser.add_argument('--kb-path', default='/Users/mac/Legal-KB',
                        help='知识库路径')
    parser.add_argument('--no-images', action='store_true',
                        help='跳过配图生成')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    generate_ppt(args.output, args.kb_path, not args.no_images)


if __name__ == '__main__':
    main()
