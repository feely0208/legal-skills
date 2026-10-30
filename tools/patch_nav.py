#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给站点页面导航加「法律专区」「法律插件」入口（幂等）。

用法：python3 tools/patch_nav.py <站点目录> [--apply]
默认 dry-run，只打印会改哪些文件。
"""
import re
import sys
from pathlib import Path

LEGAL_MAIN = '<a href="legal.html" data-zh="法律专区" data-en="Legal">法律专区</a>'
LEGAL_DROP = '<a href="plugins.html#legal" data-zh="法律插件" data-en="Legal Plugins">法律插件</a>'
HOME = '<a href="index.html" data-zh="← 返回首页" data-en="← Home">← 返回首页</a>'
HOME_PLAIN = '<a href="index.html">首页</a>'
MCP = '<a href="mcp.html" data-zh="插件 MCP" data-en="Plugin MCP">插件 MCP</a>'
MCP_PLAIN = '<a href="mcp.html">插件 MCP</a>'
COMMITTEE = '<a href="committees.html" data-zh="律协专委" data-en="Bar Committees">律协专委</a>'


def patch(s: str) -> tuple[str, list[str]]:
    notes = []
    # 1) 主链接（以 href 判断，避免被正文里的「法律专区」误判）
    if 'href="legal.html"' in s:
        pass
    elif HOME in s:
        s = s.replace(HOME, HOME + "\n    " + LEGAL_MAIN, 1); notes.append("links:after-home")
    elif '<div class="links">' in s:
        s = s.replace('<div class="links">', '<div class="links">\n    ' + LEGAL_MAIN, 1); notes.append("links:first")
    elif HOME_PLAIN in s and 'nav class="nav"' in s:
        s = s.replace(HOME_PLAIN, HOME_PLAIN + "\n  " + LEGAL_MAIN.replace(' data-zh="法律专区" data-en="Legal"', ''), 1)
        notes.append("nav:after-home")
    # 1.5) 律协专委（紧跟法律专区）
    if 'committees.html' not in s:
        plain_rel = '<a href="legal.html">法律专区</a>'
        plain_abs = '<a href="/legal.html">法律专区</a>'
        if LEGAL_MAIN in s:
            s = s.replace(LEGAL_MAIN, LEGAL_MAIN + "\n    " + COMMITTEE, 1); notes.append("after-legal:committee")
        elif plain_rel in s:
            s = s.replace(plain_rel, plain_rel + "\n    " + COMMITTEE.replace(' data-zh="律协专委" data-en="Bar Committees"', ''), 1); notes.append("after-legal:committee")
        elif plain_abs in s:
            s = s.replace(plain_abs, plain_abs + "\n    " + COMMITTEE.replace(' data-zh="律协专委" data-en="Bar Committees"', '').replace('href="committees.html"', 'href="/committees.html"'), 1); notes.append("after-legal:committee")

    # 2) 下拉菜单里的「法律插件」
    if 'href="plugins.html#legal"' not in s:
        if MCP in s:
            s = s.replace(MCP, LEGAL_DROP + MCP, 1); notes.append("drop:before-mcp")
        elif MCP_PLAIN in s:
            s = s.replace(MCP_PLAIN, LEGAL_DROP.replace(' data-zh="法律插件" data-en="Legal Plugins"', '') + MCP_PLAIN, 1)
            notes.append("drop-plain:before-mcp")
    return s, notes


def main() -> None:
    root = Path(sys.argv[1])
    apply = "--apply" in sys.argv
    changed, skipped = [], []
    for p in sorted(root.rglob("*.html")):
        parts = p.parts
        if any(x.startswith(".") for x in parts):
            continue
        if ".bak" in p.name or "safety" in p.name or "bak-" in p.name:
            continue
        if "skills/" in str(p.relative_to(root)) or "img/" in str(p.relative_to(root)):
            continue
        s = p.read_text(encoding="utf-8", errors="replace")
        if 'class="links"' not in s and 'nav class="nav"' not in s:
            skipped.append(str(p.relative_to(root)))
            continue
        new, notes = patch(s)
        if notes:
            changed.append((str(p.relative_to(root)), notes))
            if apply:
                p.write_text(new, encoding="utf-8")
    print(f"{'已修改' if apply else '将修改'} {len(changed)} 个页面；跳过无导航 {len(skipped)} 个")
    for f, n in changed:
        print(" ", f, n)
    if skipped:
        print("  无导航：", ", ".join(skipped))


if __name__ == "__main__":
    main()
