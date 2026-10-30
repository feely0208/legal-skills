#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新首页法律技能数字与文案（幂等）。"""
import sys
from pathlib import Path

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
s = src.read_text(encoding="utf-8")
n = 0

old_stat = '<div class="s"><b>10</b><span data-zh="法律技能" data-en="Legal Skills">法律技能</span></div>'
new_stat = '<div class="s"><b>23</b><span data-zh="法律技能" data-en="Legal Skills">法律技能</span></div>'
if old_stat in s:
    s = s.replace(old_stat, new_stat); n += 1

old_p = ('<p data-zh="10 个开源法律 Skill，给 Agent 用。" data-en="10 open-source legal skills for agents.">'
         '10 个开源法律 Skill，给 Agent 用。</p>')
new_p = ('<p data-zh="23 个开源法律技能：检索核验、诉讼文书、证据链、合同尽调，本地运行。" '
         'data-en="23 open-source legal skills: citation checking, litigation docs, evidence chains, due diligence — all local.">'
         '23 个开源法律技能：检索核验、诉讼文书、证据链、合同尽调，本地运行。</p>')
if old_p in s:
    s = s.replace(old_p, new_p); n += 1

if n == 0:
    raise SystemExit("首页没有匹配到要改的文案（可能已被改过）")
dst.write_text(s, encoding="utf-8")
print(f"首页更新 {n} 处")
