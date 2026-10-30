---
name: legal-kb-presentation
description: Legal-KB 项目演示材料生成工具。当用户提到"Legal-KB 演示"、"生成演示 PPT"、"制作 Legal-KB 演示"、"法律知识库 demo"、"legal KB presentation"、"project demo"、"知识库演示材料"时使用此 skill。自动扫描 Legal-KB 知识库结构，生成中英文对照的科技风演示 PPT，调用 Agnes AI 生成科技感图片素材和 15 秒 demo 视频，输出完整演示套件。
---

# Legal-KB 项目演示材料生成 Skill

为 Legal-KB 律师知识库项目生成完整的演示材料，包括：
1. **科技风演示 PPT**（中英文对照）
2. **Agnes AI 生成的科技感配图**
3. **15 秒 demo 视频**（可选，需网络通畅）
4. **传阅用 demo 小样**（HTML 网页版）

## 输出位置

所有文件输出到：`/Users/mac/git/Legal-KB-Presentation/`

## 工作流程

### 第 0 步：环境检查

```bash
# 检查 Python 依赖
python3 -c "import pptx; import PIL; print('pptx + PIL OK')"
python3 -c "import openai; print('openai OK')" 2>/dev/null || pip3 install openai python-pptx pillow --break-system-packages

# 检查 Agnes API 可达性
curl -s --connect-timeout 5 https://apihub.agnes-ai.com/v1/images/generations -I 2>/dev/null && echo "API OK" || echo "API unavailable"
```

如果 Agnes API 不可用，跳过图片/视频生成，使用内置占位图。

### 第 1 步：扫描知识库结构

读取 `/Users/mac/Legal-KB/` 目录结构，提取：
- 主模块列表（00-09，10-12）
- 各模块子目录
- 文件总数
- 最近更新时间（从动态资讯索引获取）

### 第 2 步：生成演示 PPT

使用 `scripts/gen_ppt.py` 生成科技风 PPT，包含：

| 幻灯片 | 标题 | 内容 |
|--------|------|------|
| 1 | 封面 | Legal-KB · 律师专属知识库 / Lawyer Exclusive Knowledge Base |
| 2 | 项目概述 | 一句话定位 + 核心价值 |
| 3 | 知识库结构 | 中文+英文双语言模块对照表 |
| 4 | 核心功能 | 案件管理、案例库、动态资讯等 |
| 5 | 技术架构 | Obsidian + launchd + Python 自动化 |
| 6 | 每日动态 | 法律资讯自动抓取流程 |
| 7 | 标签体系 | 中国法律标签分类 |
| 8 | 推荐插件 | Obsidian 社区插件列表 |
| 9 | 快速开始 | 三步上手指南 |
| 10 | 结尾 | 联系方式/二维码占位 |

**科技风设计要素：**
- 深色背景（#0a0e27 / #1a1f3a）
- 霓虹蓝/青色高亮（#00d4ff / #00ffcc）
- 发光边框和渐变效果
- 数据可视化风格图标
- 等宽字体 + 现代无衬线字体混合

### 第 3 步：生成科技感配图（可选）

调用 Agnes AI 图像模型生成 3-5 张科技风格配图：
- 法律科技仪表盘
- 知识图谱可视化
- 数据流动画界面
- 网络安全/加密概念图

图片保存路径：`/Users/mac/git/Legal-KB-Presentation/assets/`

### 第 4 步：生成 demo 小样

生成一个自包含的 HTML 演示页面，包含：
- 知识库结构可视化
- 模块交互展示
- 科技风 UI 设计
- 可离线传阅

### 第 5 步：生成 demo 视频（可选）

调用 Agnes AI 视频模型生成 15 秒展示视频，保存为 MP4。

## 脚本说明

### scripts/gen_ppt.py

核心 PPT 生成脚本，参数：
- `--output DIR`：输出目录
- `--kb-path PATH`：知识库路径
- `--images`：是否生成配图（需要 Agnes API）
- `--no-images`：跳过配图生成
- `--width WIDTH`：PPT 宽度（默认 13.333）
- `--height HEIGHT`：PPT 高度（默认 7.5）

### scripts/gen_html_demo.py

HTML 演示页面生成脚本，参数：
- `--output DIR`：输出目录
- `--kb-path PATH`：知识库路径

### scripts/gen_images.py

Agnes AI 图片生成脚本（可选），参数：
- `--output DIR`：输出目录
- `--count N`：生成数量
- `--api-key KEY`：Agnes API Key（也可从环境变量读取）

### scripts/gen_video.py

Agnes AI 视频生成脚本（可选），参数：
- `--output DIR`：输出目录
- `--duration SECONDS`：视频时长（默认 15）
- `--api-key KEY`：Agnes API Key

## 触发条件

在以下情况下使用此 skill：
- 用户要求生成 Legal-KB 项目演示材料
- 用户提到需要给客户/领导展示 Legal-KB
- 用户要求生成知识库的 PPT 或 demo
- 用户提到"演示"、"展示"、"汇报材料"等关键词

## 注意事项

1. **API 可用性**：Agnes API 可能需要 VPN/代理，如遇连接超时自动降级为占位图
2. **中文支持**：PPT 中所有文本使用中文，英文作为副标题
3. **文件大小**：PPT 控制在 10MB 以内，视频控制在 50MB 以内
4. **输出格式**：最终交付 .pptx + .html + 可选的 .mp4
