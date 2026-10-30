#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_statute_index.py — 从 chinese-law-corpus（CC0）生成离线法规索引。

输入：chinese-law-corpus 仓库的 laws/ 目录（1513 部现行/待生效法律法规，逐条 JSON）
输出：
  skills/legal-cite-check/data/statutes-index.json   名称 / 类别 / 效力 / 施行日 / 条文总数
  skills/legal-statute-lookup/data/laws.json         常用法律的条文全文（按 id 列表）

只保留核验与速查需要的字段，不复制官方 docx/pdf 路径。
数据来源：https://github.com/lttxzmj/chinese-law-corpus （CC0 1.0）
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = Path("/tmp/clc/laws")  # 自行 clone 后改这里
OUT_IDX = ROOT / "skills/legal-cite-check/data/statutes-index.json"
OUT_LAWS = ROOT / "skills/legal-statute-lookup/data/laws.json"

# 速查技能内置全文的常用法律（id 来自 corpus）
CORE_IDS = [
    "civil-code", "criminal-law", "civil-procedure-law", "criminal-procedure-law",
    "administrative-procedure-law", "labor-contract-law", "labor-law",
    "labor-dispute-mediation-arbitration-law", "social-insurance-law",
    "company-law", "partnership-enterprise-law", "enterprise-bankruptcy-law",
    "patent-law", "trademark-law", "copyright-law", "anti-unfair-competition-law",
    "personal-information-protection-law", "data-security-law", "cybersecurity-law",
    "consumer-rights-protection-law", "advertising-law", "food-safety-law",
    "road-traffic-safety-law", "land-administration-law",
    "urban-real-estate-administration-law", "xzfg-8e4ae5638e",
    "sfjs-mfd-hetong", "sfjs-mfd-zongze", "sfjs-mfd-hunyin-1",
]


def main() -> None:
    if not CORPUS.exists():
        raise SystemExit(f"找不到语料库：{CORPUS}\n先 git clone https://github.com/lttxzmj/chinese-law-corpus.git")
    laws, full = [], {}
    for f in sorted(CORPUS.glob("*.json")):
        if f.name == "index.json":
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        arts = d.get("articles") or []
        # ⚠️ 不要用顶层 articleCount：刑法等带附件/修正案的法律会把它算大
        # （刑法 articleCount=505，实际最后一条是第四百五十二条）。以最大条号为准。
        nums = [a.get("articleNumber") for a in arts if isinstance(a.get("articleNumber"), int)]
        laws.append({
            "id": d.get("id"),
            "title": d.get("title"),
            "category": d.get("category"),
            "status": d.get("status"),
            "effectiveDate": d.get("effectiveDate"),
            "promulgationDate": d.get("promulgationDate"),
            "articleCount": max(nums) if nums else d.get("articleCount"),
        })
        if d.get("id") in CORE_IDS:
            full[d["id"]] = {
                "title": d.get("title"),
                "category": d.get("category"),
                "status": d.get("status"),
                "effectiveDate": d.get("effectiveDate"),
                "articles": [
                    {"n": a.get("articleNumber"), "display": a.get("displayNumber"),
                     "path": a.get("path") or [], "text": a.get("text")}
                    for a in d.get("articles") or []
                ],
            }
    laws.sort(key=lambda x: (-(x["articleCount"] or 0), x["title"] or ""))
    meta = {
        "_note": "离线法规索引。来源：chinese-law-corpus（CC0 1.0），官方文本取自国家法律法规数据库。只覆盖现行/待生效法规，不含已废止法律；失效对照见 statutes.json。",
        "_source": "https://github.com/lttxzmj/chinese-law-corpus",
        "_checked": "2026-10-29",
        "count": len(laws),
        "laws": laws,
    }
    OUT_IDX.parent.mkdir(parents=True, exist_ok=True)
    OUT_IDX.write_text(json.dumps(meta, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    OUT_LAWS.parent.mkdir(parents=True, exist_ok=True)
    OUT_LAWS.write_text(json.dumps({
        "_note": "常用法律条文全文，来源 chinese-law-corpus（CC0）。速查用，正式引用以 flk.npc.gov.cn 为准。",
        "_source": "https://github.com/lttxzmj/chinese-law-corpus",
        "laws": full,
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(f"索引 {len(laws)} 部 → {OUT_IDX} ({OUT_IDX.stat().st_size//1024} KB)")
    print(f"全文 {len(full)} 部 → {OUT_LAWS} ({OUT_LAWS.stat().st_size//1024} KB)")
    missing = [i for i in CORE_IDS if i not in full]
    if missing:
        print("⚠️ 未找到的常用法 id：", missing)


if __name__ == "__main__":
    main()
