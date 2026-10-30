#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把法律专区插进 plugins.html（幂等）。用法：python3 patch_plugins_page.py <in.html> <out.html>"""
import sys, re
from pathlib import Path

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
s = src.read_text(encoding="utf-8")
frag = (Path(__file__).resolve().parent.parent / "site" / "plugins-legal.html").read_text(encoding="utf-8")

force = "--force" in sys.argv
if 'id="legal"' in s:
    if not force:
        print("已存在法律专区，跳过（--force 可替换）")
        dst.write_text(s, encoding="utf-8")
        raise SystemExit(0)
    start = s.find('<h3 class="mod" id="legal"')
    end = s.find('<h3 class="mod">文档与交付', start)
    if start < 0 or end < 0:
        raise SystemExit("找不到旧法律专区边界")
    s = s[:start] + frag.strip() + "\n\n  " + s[end:]
    dst.write_text(s, encoding="utf-8")
    print("已替换法律专区")
    raise SystemExit(0)

anchor = '<h3 class="mod">文档与交付'
i = s.find(anchor)
if i < 0:
    raise SystemExit("找不到插入点（文档与交付）")
s = s[:i] + frag.strip() + "\n\n  " + s[i:]
dst.write_text(s, encoding="utf-8")
print(f"已插入法律专区：{i} 字节处")
