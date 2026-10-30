#!/usr/bin/env python3
"""
Legal-KB HTML 演示页面生成器
生成可离线传阅的科技风演示网页
"""

import argparse
import os
from pathlib import Path
from datetime import datetime


def generate_html(output_dir, kb_path=None):
    """生成 HTML 演示页面"""
    if kb_path is None:
        kb_path = "/Users/mac/Legal-KB"

    today = datetime.now().strftime("%Y-%m-%d")

    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Legal-KB · 律师专属知识库</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
            --bg-dark: #0a0e27;
            --bg-card: #1a1f3a;
            --accent-blue: #00d4ff;
            --accent-cyan: #00ffcc;
            --accent-pink: #ff0080;
            --text-primary: #ffffff;
            --text-secondary: #b4bee0;
            --text-muted: #7882a0;
        }}

        body {{
            font-family: 'PingFang SC', 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
        }}

        /* 导航栏 */
        .navbar {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            padding: 1rem 2rem;
            background: rgba(10, 14, 39, 0.95);
            backdrop-filter: blur(10px);
            z-index: 1000;
            border-bottom: 1px solid rgba(0, 212, 255, 0.2);
        }}

        .navbar-content {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .logo {{
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--accent-cyan);
            text-shadow: 0 0 20px rgba(0, 255, 204, 0.5);
        }}

        .nav-links {{
            display: flex;
            gap: 2rem;
            list-style: none;
        }}

        .nav-links a {{
            color: var(--text-secondary);
            text-decoration: none;
            transition: color 0.3s;
        }}

        .nav-links a:hover {{
            color: var(--accent-cyan);
        }}

        /* Hero 区域 */
        .hero {{
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 2rem;
            position: relative;
            overflow: hidden;
        }}

        .hero::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(ellipse at center, rgba(0, 212, 255, 0.15) 0%, transparent 70%);
            animation: pulse 4s ease-in-out infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 0.5; }}
            50% {{ opacity: 1; }}
        }}

        .hero-content {{
            position: relative;
            z-index: 1;
        }}

        .hero h1 {{
            font-size: 4rem;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 40px rgba(0, 212, 255, 0.3);
        }}

        .hero .subtitle {{
            font-size: 1.5rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }}

        .hero .english-subtitle {{
            font-size: 1.2rem;
            color: var(--text-muted);
            margin-bottom: 2rem;
        }}

        .hero .tagline {{
            font-size: 1rem;
            color: var(--text-muted);
            padding: 0.5rem 1.5rem;
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 20px;
            display: inline-block;
        }}

        /* 模块区域 */
        .section {{
            padding: 5rem 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }}

        .section-title {{
            font-size: 2.5rem;
            text-align: center;
            margin-bottom: 1rem;
            color: var(--accent-cyan);
        }}

        .section-subtitle {{
            font-size: 1rem;
            text-align: center;
            color: var(--text-muted);
            margin-bottom: 3rem;
        }}

        /* 模块卡片 */
        .modules-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
        }}

        .module-card {{
            background: var(--bg-card);
            border: 1px solid rgba(0, 212, 255, 0.2);
            border-radius: 12px;
            padding: 1.5rem;
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }}

        .module-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, var(--accent-cyan), var(--accent-blue));
            opacity: 0;
            transition: opacity 0.3s;
        }}

        .module-card:hover {{
            transform: translateY(-5px);
            border-color: var(--accent-blue);
            box-shadow: 0 10px 30px rgba(0, 212, 255, 0.2);
        }}

        .module-card:hover::before {{
            opacity: 1;
        }}

        .module-icon {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}

        .module-name {{
            font-size: 1.2rem;
            font-weight: bold;
            color: var(--text-primary);
            margin-bottom: 0.25rem;
        }}

        .module-name-en {{
            font-size: 0.9rem;
            color: var(--text-muted);
            margin-bottom: 0.75rem;
        }}

        .module-desc {{
            font-size: 0.9rem;
            color: var(--text-secondary);
        }}

        /* 标签区域 */
        .tags-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            justify-content: center;
            margin-top: 2rem;
        }}

        .tag {{
            padding: 0.5rem 1rem;
            background: var(--bg-card);
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 20px;
            font-size: 0.9rem;
            color: var(--accent-cyan);
            transition: all 0.3s;
        }}

        .tag:hover {{
            background: rgba(0, 212, 255, 0.1);
            border-color: var(--accent-cyan);
            box-shadow: 0 0 15px rgba(0, 255, 204, 0.3);
        }}

        /* 功能区域 */
        .features-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
        }}

        .feature-item {{
            display: flex;
            gap: 1rem;
            padding: 1.5rem;
            background: var(--bg-card);
            border-radius: 12px;
            border: 1px solid rgba(0, 212, 255, 0.1);
        }}

        .feature-icon {{
            font-size: 2rem;
            flex-shrink: 0;
        }}

        .feature-content h3 {{
            color: var(--accent-cyan);
            margin-bottom: 0.25rem;
        }}

        .feature-content .en {{
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
        }}

        .feature-content p {{
            font-size: 0.9rem;
            color: var(--text-secondary);
        }}

        /* 时间线 */
        .timeline {{
            position: relative;
            padding-left: 2rem;
        }}

        .timeline::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 2px;
            background: linear-gradient(180deg, var(--accent-cyan), var(--accent-blue));
        }}

        .timeline-item {{
            position: relative;
            padding-bottom: 2rem;
        }}

        .timeline-item::before {{
            content: '';
            position: absolute;
            left: -2rem;
            top: 0.5rem;
            width: 12px;
            height: 13px;
            background: var(--accent-cyan);
            border-radius: 50%;
            transform: translateX(-5px);
            box-shadow: 0 0 10px var(--accent-cyan);
        }}

        .timeline-item h4 {{
            color: var(--accent-cyan);
            margin-bottom: 0.25rem;
        }}

        .timeline-item .en {{
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
        }}

        .timeline-item p {{
            font-size: 0.9rem;
            color: var(--text-secondary);
            font-family: 'Menlo', 'Courier New', monospace;
        }}

        /* 快速开始 */
        .steps {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 2rem;
            margin-top: 3rem;
        }}

        .step {{
            text-align: center;
            padding: 2rem;
            background: var(--bg-card);
            border-radius: 12px;
            border: 1px solid rgba(0, 212, 255, 0.1);
        }}

        .step-number {{
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--bg-dark);
            margin: 0 auto 1rem;
        }}

        .step h3 {{
            color: var(--text-primary);
            margin-bottom: 0.25rem;
        }}

        .step .en {{
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
        }}

        .step p {{
            font-size: 0.9rem;
            color: var(--text-secondary);
        }}

        /* 页脚 */
        .footer {{
            text-align: center;
            padding: 3rem 2rem;
            border-top: 1px solid rgba(0, 212, 255, 0.1);
            color: var(--text-muted);
        }}

        .footer .highlight {{
            color: var(--accent-cyan);
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
        }}

        /* 响应式 */
        @media (max-width: 768px) {{
            .hero h1 {{
                font-size: 2.5rem;
            }}
            .nav-links {{
                display: none;
            }}
        }}

        /* 动画 */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .animate {{
            animation: fadeInUp 0.6s ease-out;
        }}
    </style>
</head>
<body>
    <!-- 导航栏 -->
    <nav class="navbar">
        <div class="navbar-content">
            <div class="logo">Legal-KB</div>
            <ul class="nav-links">
                <li><a href="#overview">概述</a></li>
                <li><a href="#modules">模块</a></li>
                <li><a href="#features">功能</a></li>
                <li><a href="#workflow">流程</a></li>
                <li><a href="#start">开始</a></li>
            </ul>
        </div>
    </nav>

    <!-- Hero 区域 -->
    <section class="hero">
        <div class="hero-content animate">
            <h1>Legal-KB</h1>
            <p class="subtitle">律师专属知识库系统</p>
            <p class="english-subtitle">Lawyer Exclusive Knowledge Base System</p>
            <span class="tagline">基于 Obsidian · AI 辅助 · 自动化</span>
        </div>
    </section>

    <!-- 项目概述 -->
    <section id="overview" class="section">
        <h2 class="section-title">项目概述</h2>
        <p class="section-subtitle">Project Overview</p>
        <div style="background: var(--bg-card); padding: 2rem; border-radius: 12px; border: 1px solid rgba(0,212,255,0.2);">
            <p style="font-size: 1.1rem; color: var(--text-secondary); line-height: 2;">
                • 基于 <strong style="color: var(--accent-cyan)">Obsidian</strong> 构建的律师执业全流程知识管理工具<br>
                • 覆盖法律法规、文书模板、案例库、案件管理、企业顾问、实务技能等核心模块<br>
                • 支持动态资讯自动抓取（每日 9:30 定时更新）<br>
                • 集成 AI 辅助写作（起诉状、合同、答辩状等）<br>
                • 多标签体系支持快速检索和关联分析
            </p>
        </div>
    </section>

    <!-- 知识库模块 -->
    <section id="modules" class="section">
        <h2 class="section-title">知识库模块</h2>
        <p class="section-subtitle">Knowledge Base Modules</p>
        <div class="modules-grid">
            <div class="module-card">
                <div class="module-icon">🏠</div>
                <div class="module-name">工作台</div>
                <div class="module-name-en">Workbench</div>
                <div class="module-desc">每日工作入口、案件速查、时间追踪</div>
            </div>
            <div class="module-card">
                <div class="module-icon">⚖️</div>
                <div class="module-name">法律法规</div>
                <div class="module-name-en">Laws & Regulations</div>
                <div class="module-desc">法律法规汇编（含知识产权、建设工程专项）</div>
            </div>
            <div class="module-card">
                <div class="module-icon">📄</div>
                <div class="module-name">文书模板库</div>
                <div class="module-name-en">Document Templates</div>
                <div class="module-desc">各类文书模板（含知识产权、建设工程专项）</div>
            </div>
            <div class="module-card">
                <div class="module-icon">📚</div>
                <div class="module-name">案例库</div>
                <div class="module-name-en">Case Library</div>
                <div class="module-desc">典型案例归档与胜败分析</div>
            </div>
            <div class="module-card">
                <div class="module-icon">📁</div>
                <div class="module-name">案件管理</div>
                <div class="module-name-en">Case Management</div>
                <div class="module-desc">案件全流程管理（在办/待接/已结）</div>
            </div>
            <div class="module-card">
                <div class="module-icon">🏢</div>
                <div class="module-name">企业顾问</div>
                <div class="module-name-en">Corporate Advisory</div>
                <div class="module-desc">法律顾问客户档案管理</div>
            </div>
            <div class="module-card">
                <div class="module-icon">🛠️</div>
                <div class="module-name">实务技能</div>
                <div class="module-name-en">Practical Skills</div>
                <div class="module-desc">庭审技巧、谈判策略、证据搜集</div>
            </div>
            <div class="module-card">
                <div class="module-icon">📰</div>
                <div class="module-name">动态资讯</div>
                <div class="module-name-en">Daily News</div>
                <div class="module-desc">实时法律动态（法规、司法、司法部资讯）</div>
            </div>
            <div class="module-card">
                <div class="module-icon">💡</div>
                <div class="module-name">知识产权专属库</div>
                <div class="module-name-en">IP Exclusive Library</div>
                <div class="module-desc">专利、商标、著作权、商业秘密专项</div>
            </div>
            <div class="module-card">
                <div class="module-icon">🏗️</div>
                <div class="module-name">建设工程专属库</div>
                <div class="module-name-en">Construction Exclusive Library</div>
                <div class="module-desc">招投标、施工合同、工程结算专项</div>
            </div>
        </div>
    </section>

    <!-- 核心功能 -->
    <section id="features" class="section">
        <h2 class="section-title">核心功能</h2>
        <p class="section-subtitle">Core Features</p>
        <div class="features-grid">
            <div class="feature-item">
                <div class="feature-icon">📂</div>
                <div class="feature-content">
                    <h3>知识库管理</h3>
                    <div class="en">Knowledge Management</div>
                    <p>全模块知识归档、标签分类、快速检索</p>
                </div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">📅</div>
                <div class="feature-content">
                    <h3>每日资讯</h3>
                    <div class="en">Daily News</div>
                    <p>自动抓取最高人民法院、最高检、司法部动态</p>
                </div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">✍️</div>
                <div class="feature-content">
                    <h3>AI 辅助写作</h3>
                    <div class="en">AI Writing</div>
                    <p>起诉状、合同、答辩状自动生成</p>
                </div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">📊</div>
                <div class="feature-content">
                    <h3>案件看板</h3>
                    <div class="en">Case Kanban</div>
                    <p>拖拽式案件进度管理</p>
                </div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">🔔</div>
                <div class="feature-content">
                    <h3>定时任务</h3>
                    <div class="en">Scheduled Tasks</div>
                    <p>launchd 自动执行，邮件通知</p>
                </div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">🏷️</div>
                <div class="feature-content">
                    <h3>标签体系</h3>
                    <div class="en">Tag System</div>
                    <p>民商事、刑事、劳动等多维度标签</p>
                </div>
            </div>
        </div>
    </section>

    <!-- 标签体系 -->
    <section class="section">
        <h2 class="section-title">标签体系</h2>
        <p class="section-subtitle">Tag System</p>
        <div class="tags-container">
            <span class="tag">#民商事 Civil</span>
            <span class="tag">#刑事 Criminal</span>
            <span class="tag">#劳动 Labor</span>
            <span class="tag">#家事 Family</span>
            <span class="tag">#非诉 Non-litigation</span>
            <span class="tag">#知识产权 IP</span>
            <span class="tag">#建设工程 Construction</span>
            <span class="tag">#在办 Active</span>
            <span class="tag">#已结 Closed</span>
            <span class="tag">#模板 Template</span>
            <span class="tag">#案例 Case</span>
            <span class="tag">#法律法规 Law</span>
        </div>
    </section>

    <!-- 每日动态流程 -->
    <section id="workflow" class="section">
        <h2 class="section-title">每日动态流程</h2>
        <p class="section-subtitle">Daily Automation Workflow</p>
        <div class="timeline">
            <div class="timeline-item">
                <h4>launchd 触发脚本</h4>
                <div class="en">launchd Trigger Script</div>
                <p>每天 9:30 自动执行 daily_legal_news.py</p>
            </div>
            <div class="timeline-item">
                <h4>抓取法律资讯</h4>
                <div class="en">Scrape Legal News</div>
                <p>最高人民法院、最高人民检察院、司法部官网</p>
            </div>
            <div class="timeline-item">
                <h4>解析与归档</h4>
                <div class="en">Parse & Archive</div>
                <p>生成 Obsidian Markdown 笔记</p>
            </div>
            <div class="timeline-item">
                <h4>更新索引</h4>
                <div class="en">Update Index</div>
                <p>自动更新动态资讯索引和汇总文件</p>
            </div>
            <div class="timeline-item">
                <h4>发送邮件通知</h4>
                <div class="en">Send Email Notification</div>
                <p>通过 agently-cli 发送邮件到指定邮箱</p>
            </div>
            <div class="timeline-item">
                <h4>自动刷新</h4>
                <div class="en">Auto Refresh</div>
                <p>打开 Obsidian 查看最新内容</p>
            </div>
        </div>
    </section>

    <!-- 快速开始 -->
    <section id="start" class="section">
        <h2 class="section-title">快速开始</h2>
        <p class="section-subtitle">Quick Start</p>
        <div class="steps">
            <div class="step">
                <div class="step-number">1</div>
                <h3>打开 Obsidian</h3>
                <div class="en">Open Obsidian</div>
                <p>选择「打开文件夹作为仓库」</p>
            </div>
            <div class="step">
                <div class="step-number">2</div>
                <h3>选择路径</h3>
                <div class="en">Select Path</div>
                <p>选择 Legal-KB 目录</p>
            </div>
            <div class="step">
                <div class="step-number">3</div>
                <h3>安装插件</h3>
                <div class="en">Install Plugins</div>
                <p>社区插件：Dataview、Templater、Kanban</p>
            </div>
            <div class="step">
                <div class="step-number">4</div>
                <h3>开始使用</h3>
                <div class="en">Start Using</div>
                <p>从工作台开始管理案件</p>
            </div>
        </div>
    </section>

    <!-- 页脚 -->
    <footer class="footer">
        <div class="highlight">Legal-KB</div>
        <p>律师专属知识库系统 · Lawyer Exclusive Knowledge Base</p>
        <p style="margin-top: 1rem; font-size: 0.85rem;">演示日期: {today} · 基于 Obsidian 知识库平台</p>
    </footer>

    <script>
        // 平滑滚动
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth' }});
                }}
            }});
        }});

        // 滚动动画
        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    entry.target.classList.add('animate');
                }}
            }});
        }}, {{ threshold: 0.1 }});

        document.querySelectorAll('.module-card, .feature-item, .step').forEach(el => {{
            observer.observe(el);
        }});
    </script>
</body>
</html>'''

    # 保存 HTML
    html_path = Path(output_dir) / "Legal-KB-Demo.html"
    html_path.write_text(html_content, encoding='utf-8')
    print(f"✅ HTML 演示页面已生成: {html_path}")
    return str(html_path)


def main():
    parser = argparse.ArgumentParser(description='Legal-KB HTML 演示页面生成器')
    parser.add_argument('--output', '-o', default='/Users/mac/git/Legal-KB-Presentation',
                        help='输出目录')
    parser.add_argument('--kb-path', default='/Users/mac/Legal-KB',
                        help='知识库路径')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    generate_html(args.output, args.kb_path)


if __name__ == '__main__':
    main()
