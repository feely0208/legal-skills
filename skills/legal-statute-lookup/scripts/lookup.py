#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""法条本地定位（只用 Python 标准库）。

数据：../data/laws.json（29 部常用法律逐条全文，CC0 语料）。
只做定位与原文展示，不是官方文本；正式引用以 flk.npc.gov.cn 为准。

用法：
  python3 scripts/lookup.py --list
  python3 scripts/lookup.py 劳动合同法 47
  python3 scripts/lookup.py --law 民法典 --article 585
  python3 scripts/lookup.py 民法典 第五百八十五条
  python3 scripts/lookup.py --keyword 试用期 --law 劳动合同法 --limit 10
"""

import argparse
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data", "laws.json")
FULL = os.path.join(BASE, "..", "data", "laws-full.json.gz")

CN_DIGITS = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
             "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
CN_UNITS = {"十": 10, "百": 100, "千": 1000}

# 语料里司法解释标题很长，补常用简称
EXTRA_ALIASES = {
    "合同编通则解释": "sfjs-mfd-hetong",
    "合同编通则司法解释": "sfjs-mfd-hetong",
    "婚姻家庭编解释一": "sfjs-mfd-hunyin-1",
    "婚姻家庭编司法解释一": "sfjs-mfd-hunyin-1",
    "总则编解释": "sfjs-mfd-zongze",
    "工伤条例": "xzfg-8e4ae5638e",
}


def cn2int(text):
    """把「五百八十五」「第47条」转成整数；失败返回 None。"""
    s = str(text).strip()
    s = re.sub(r"^第", "", s)
    s = re.sub(r"条$", "", s)
    s = s.replace(" ", "")
    if not s:
        return None
    if s.isdigit():
        return int(s)
    total, cur = 0, 0
    for ch in s:
        if ch in CN_DIGITS:
            cur = CN_DIGITS[ch]
        elif ch in CN_UNITS:
            unit = CN_UNITS[ch]
            total += (cur or 1) * unit
            cur = 0
        else:
            return None
    return total + cur


def norm(text):
    text = str(text)
    for junk in ("《", "》", "〈", "〉", " ", "\u3000", "中华人民共和国",
                 "最高人民法院关于适用", "最高人民法院", "（", "）", "(", ")"):
        text = text.replace(junk, "")
    return text


def load():
    """优先用全量库（1,513 部，需下载法条全文库）；没有就退回随包 29 部。"""
    if os.path.exists(FULL):
        import gzip
        with gzip.open(FULL, "rt", encoding="utf-8") as f:
            return json.load(f)
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)["laws"]


def corpus_label():
    return "全量库 1,513 部" if os.path.exists(FULL) else "随包 29 部"


def law_max(law):
    # 刑法带附件，条号会出现 408001，按「正文条」最大 n<=1000 取
    nums = [a["n"] for a in law["articles"] if 0 < a["n"] <= 1000]
    return max(nums) if nums else 0


def match_laws(laws, query):
    """返回按匹配度排序的 (id, law, 匹配类型) 列表。"""
    q = norm(query)
    if not q:
        return []
    if query in laws:
        return [(query, laws[query], "id")]
    if query in EXTRA_ALIASES and EXTRA_ALIASES[query] in laws:
        key = EXTRA_ALIASES[query]
        return [(key, laws[key], "alias")]

    exact, starts, contains = [], [], []
    for key, law in laws.items():
        title = norm(law["title"])
        if q == title:
            exact.append((key, law, "全称"))
        elif title.startswith(q):
            starts.append((key, law, "前缀"))
        elif q in title:
            contains.append((key, law, "包含"))
    return exact + starts + contains


def find_article(law, number):
    for art in law["articles"]:
        if art["n"] == number:
            return art
    return None


def snippet(text, width=46):
    text = re.sub(r"\s+", "", text)
    return text if len(text) <= width else text[:width] + "…"


def render_card(law_id, law, art, with_neighbors=True):
    path = " / ".join(art.get("path") or []) or "（未标注编章）"
    lines = [
        f"## 《{law['title']}》{art['display']}",
        "",
        f"- 位置：{path}",
        f"- 状态：{law.get('status', '未知')}；施行日 {law.get('effectiveDate', '待核')}",
        f"- 条文：{art['text']}",
    ]
    if with_neighbors:
        for delta, label in ((-1, "上一条"), (1, "下一条")):
            nb = find_article(law, art["n"] + delta)
            if nb:
                lines.append(f"- {label}：{nb['display']} {snippet(nb['text'])}")
    lines += [
        "",
        "> 来源：本地语料（非官方全文）。正式引用前请以国家法律法规数据库 flk.npc.gov.cn 核对。",
        "> 声明：AI 辅助生成，需承办律师复核；是否适用于本案需结合事实判断。",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="本地法条定位（非官方全文）")
    ap.add_argument("law", nargs="?", help="法律名称或 id，如 劳动合同法 / civil-code")
    ap.add_argument("article", nargs="?", help="条号，支持 47 / 第四十七条 / 五百八十五")
    ap.add_argument("--law", dest="law_opt", help="法律名称（与位置参数二选一）")
    ap.add_argument("--article", dest="article_opt", help="条号（与位置参数二选一）")
    ap.add_argument("--keyword", help="在全文中搜索关键词")
    ap.add_argument("--limit", type=int, default=20, help="关键词结果上限，默认 20")
    ap.add_argument("--list", action="store_true", help="列出收录的法律")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = ap.parse_args()

    if not os.path.exists(DATA) and not os.path.exists(FULL):
        sys.exit(f"数据文件不存在：{DATA}")
    laws = load()

    if args.list:
        rows = []
        for key, law in sorted(laws.items(), key=lambda kv: kv[1]["title"]):
            rows.append((law["title"], law.get("status", ""), law.get("effectiveDate", ""),
                         len(law["articles"]), law_max(law), key))
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
            return
        print(f"> 语料：{corpus_label()}（共 {len(rows)} 部）")
        print("| 法律 | 状态 | 施行日 | 收录条数 | 最大条号 | id |")
        print("|---|---|---|---|---|---|")
        for r in rows[:80]:
            print("| {} | {} | {} | {} | {} | {} |".format(*r))
        return

    query = args.law_opt or args.law
    number_raw = args.article_opt or args.article

    if args.keyword:
        kw = args.keyword.strip()
        hits = []
        pool = laws.items()
        if query:
            matched = match_laws(laws, query)
            if not matched:
                sys.exit(f"未收录该法律：{query}（用 --list 查看范围）")
            pool = [(matched[0][0], matched[0][1])]
        for key, law in pool:
            for art in law["articles"]:
                if kw in art["text"]:
                    hits.append((law["title"], art, key))
        if args.json:
            print(json.dumps([{"law": t, "n": a["n"], "display": a["display"],
                               "path": a.get("path"), "text": a["text"]}
                              for t, a, _ in hits[:args.limit]], ensure_ascii=False, indent=2))
            return
        if not hits:
            print(f"未在收录范围内找到「{kw}」。可换关键词，或确认该法是否在 --list 中。")
            return
        print(f"命中 {len(hits)} 条（显示前 {min(len(hits), args.limit)} 条）：\n")
        print("| 法律 | 条 | 位置 | 摘录 |")
        print("|---|---|---|---|")
        for title, art, _ in hits[:args.limit]:
            path = " / ".join(art.get("path") or [])
            print(f"| {title} | {art['display']} | {path} | {snippet(art['text'], 60)} |")
        print("\n> 关键词命中不等于适用；条号与文本以 flk.npc.gov.cn 为准。")
        return

    if not query:
        ap.print_help()
        return

    matched = match_laws(laws, query)
    if not matched:
        sys.exit(f"未收录该法律：{query}（用 --list 查看范围；未收录不等于不存在）")
    if len(matched) > 1 and matched[0][2] != "全称" and not number_raw:
        print(f"「{query}」匹配到多部法律，请指明：")
        for key, law, kind in matched[:8]:
            print(f"  - {law['title']}（{key}）")
        return

    law_id, law, _ = matched[0]

    if not number_raw:
        print(f"《{law['title']}》共 {law_max(law)} 条（按最大条号）。请给出条号，或用 --keyword 搜索。")
        return

    number = cn2int(number_raw)
    if number is None:
        sys.exit(f"无法识别条号：{number_raw}")
    art = find_article(law, number)
    if not art:
        sys.exit(f"《{law['title']}》未找到第 {number} 条（最大条号 {law_max(law)}）。"
                 "条号可能因修订调整，请核对现行文本。")

    if args.json:
        print(json.dumps({"law": law["title"], "law_id": law_id, "status": law.get("status"),
                          "effectiveDate": law.get("effectiveDate"), "article": art},
                         ensure_ascii=False, indent=2))
        return
    print(render_card(law_id, law, art))


if __name__ == "__main__":
    main()
