#!/usr/bin/env bash
# 深鲸法律技能集 · 安装脚本
# 用法：
#   bash install.sh --target ~/.claude/skills          # 装全部
#   bash install.sh --target ~/.codex/skills --only legal-cite-check
#   bash install.sh --target ./skills --list
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/skills"
TARGET=""
ONLY=""
LIST=0

while [ $# -gt 0 ]; do
  case "$1" in
    --target) TARGET="${2:?--target 需要一个目录}"; shift 2 ;;
    --only)   ONLY="${2:?--only 需要一个技能名}"; shift 2 ;;
    --list)   LIST=1; shift ;;
    -h|--help)
      sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "未知参数：$1" >&2; exit 2 ;;
  esac
done

if [ "$LIST" = "1" ]; then
  for d in "$SRC"/*/; do basename "$d"; done
  exit 0
fi

[ -n "$TARGET" ] || { echo "缺少 --target（例如 ~/.claude/skills）" >&2; exit 2; }
mkdir -p "$TARGET"

copy_one() {
  local name="$1"
  [ -d "$SRC/$name" ] || { echo "找不到技能：$name" >&2; return 1; }
  rm -rf "$TARGET/$name"
  cp -R "$SRC/$name" "$TARGET/$name"
  echo "  ✓ $name"
}

echo "安装到：$TARGET"
if [ -n "$ONLY" ]; then
  copy_one "$ONLY"
else
  for d in "$SRC"/*/; do copy_one "$(basename "$d")"; done
fi

PROFILE="$HOME/.deepwhale/深鲸法律档案.md"
if [ ! -f "$PROFILE" ]; then
  if mkdir -p "$(dirname "$PROFILE")" 2>/dev/null && cp "$HERE/templates/法律档案.md" "$PROFILE" 2>/dev/null; then
    echo "  ✓ 已生成法律档案模板：$PROFILE（建议先填）"
  else
    echo "  ⚠️ 法律档案模板没写成（权限或 sandbox），可稍后手动复制：$HERE/templates/法律档案.md"
  fi
fi

echo "完成。重启对应的 Agent 即可生效。"
