# Legal-KB 演示材料生成 Skill

为 Legal-KB 律师知识库项目生成完整的演示材料，包括科技风 PPT、HTML 演示页、配图和视频。

## 文件结构

```
legal-kb-presentation/
├── SKILL.md              # 本文件
├── scripts/
│   ├── gen_ppt.py        # PPT 生成器
│   ├── gen_html_demo.py  # HTML 演示页生成器
│   ├── gen_images.py     # Agnes AI 配图生成器
│   ├── gen_video.py      # Agnes AI 视频生成器
│   └── generate_all.py   # 主入口（整合所有脚本）
├── assets/               # 生成的配图和视频
└── references/           # 参考文档
```

## 使用方法

### 完整生成（推荐）

```bash
# 设置 API Key（可选，不设置则使用占位图）
export AGNES_API_KEY="your-agnes-api-key"

# 运行完整生成
python3 /Users/mac/.claude/skills/legal-kb-presentation/scripts/generate_all.py \
  --output /Users/mac/git/Legal-KB-Presentation \
  --kb-path /Users/mac/Legal-KB
```

### 单独生成

```bash
# 仅生成 PPT
python3 scripts/gen_ppt.py --output /path/to/output

# 仅生成 HTML
python3 scripts/gen_html_demo.py --output /path/to/output

# 仅生成配图
python3 scripts/gen_images.py --output /path/to/output --count 4

# 仅生成视频（需 API Key）
python3 scripts/gen_video.py --output /path/to/output --duration 15
```

### 检查环境

```bash
python3 scripts/generate_all.py --check-only
```

## 输出内容

| 文件 | 说明 | 大小 |
|------|------|------|
| Legal-KB-演示.pptx | 科技风演示 PPT（10 页） | ~500KB |
| Legal-KB-Demo.html | 可离线传阅的演示网页 | ~15KB |
| assets/slide_*.png | 科技感配图（4-5 张） | 每张 ~500KB |
| assets/Legal-KB-Demo.mp4 | 15 秒 demo 视频（可选） | ~10MB |

## 触发条件

以下情况使用此 skill：
- 用户要求生成 Legal-KB 项目演示材料
- 用户提到"演示"、"展示"、"汇报材料"
- 用户需要给客户/领导展示 Legal-KB
- 用户要求生成 PPT 或 demo
- 关键词：legal KB presentation, 知识库演示, 项目展示

## Agnes API 配置

Agnes AI 用于生成科技风配图和 demo 视频。如需使用：

1. 在 https://platform.agnes-ai.com/ 注册账号
2. 获取 API Key
3. 设置环境变量：`export AGNES_API_KEY="your-key"`

**注意**：当前网络环境下 Agnes API 可能无法访问（需要 VPN/代理），脚本会自动降级使用占位图。

## 技术细节

### PPT 设计

- 科技风深色主题（#0a0e27 背景）
- 霓虹蓝/青色高亮（#00d4ff / #00ffcc）
- 中英文对照
- 10 页完整演示流程

### HTML 演示页

- 单文件自包含（无需外部依赖）
- 响应式设计（支持手机/平板）
- 科技感 UI（渐变、发光效果）
- 可离线传阅

### 配图生成

- 使用 agnes-image-2.1-flash 模型
- 科技风 UI/UX 设计
- 深色背景 + 霓虹高亮
- 1024x576 分辨率（适合 PPT）

### 视频生成

- 使用 agnes-video-v2.0 模型
- 15 秒时长
- 720p 分辨率
- 需要 API Key 和网络通畅

## 依赖

- Python 3.8+
- python-pptx
- Pillow
- requests
- openai (可选，用于 Agnes API)
