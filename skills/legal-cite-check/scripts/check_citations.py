#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_citations.py — 法律文书引用核验（离线）

做什么：
  1. 从 .md / .txt / .docx 文书里抽取三类引用：
       《法名》第 N 条（含第 N 款）
       法释〔年份〕N 号
       案号（如（2026）浙0302民初123号）
  2. 用同目录 data/statutes.json 做四项检查：
       失效法条     → 引用了已被民法典等取代的旧法（material，直接拦）
       条号越界     → 条号大于该法条文总数
       已废止文件   → 法释编号已被新解释取代
       未收录       → 索引里没有，标「需人工核验」，不假装通过
  3. 输出：
       citations.csv       逐条核验表（Excel 可开）
       citations.md        人看的核验报告
       highlighted.md      在原位置给问题引用加标记的版本

设计原则：
  - 只对自己索引里的事实负责；查不到就说查不到。
  - 不联网、不上传、不调用模型。
  - 判断不了的（案号、未收录法名）绝不标成「通过」。

用法：
  python3 scripts/check_citations.py 文书.md
  python3 scripts/check_citations.py 案卷目录/ -o 核验结果/
  python3 scripts/check_citations.py 文书.md --strict   # 有 material 错误时退出码 1
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "statutes.json"
INDEX = HERE.parent / "data" / "statutes-index.json"

CN_DIGITS = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
             "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
CN_UNITS = {"十": 10, "百": 100, "千": 1000}


def cn_to_int(s: str) -> int | None:
    """把「五百七十七」「1260」这类写法转成整数。"""
    s = s.strip()
    if not s:
        return None
    if s.isdigit():
        return int(s)
    total, section, num = 0, 0, 0
    for ch in s:
        if ch in CN_DIGITS:
            num = CN_DIGITS[ch]
        elif ch in CN_UNITS:
            unit = CN_UNITS[ch]
            if num == 0:
                num = 1
            section += num * unit
            num = 0
        else:
            return None
    total = section + num
    return total or None


def norm_name(name: str) -> str:
    n = name.strip().replace(" ", "").replace("　", "")
    n = n.replace("〈", "《").replace("〉", "》")
    n = re.sub(r"^中华人民共和国", "", n)
    n = re.sub(r"^最高(人民)?(法院|人民检察院)关于", "", n)
    n = re.sub(r"^关于", "", n)
    return n


def load_index() -> dict:
    with open(DATA, encoding="utf-8") as f:
        raw = json.load(f)

    laws, superseded, docs = {}, {}, {}
    for item in raw.get("laws", []):
        keys = {norm_name(item["name"])} | {norm_name(a) for a in item.get("aliases", [])}
        for k in keys:
            laws[k] = item
    for item in raw.get("superseded_laws", []):
        keys = {norm_name(item["name"])} | {norm_name(a) for a in item.get("aliases", [])}
        for k in keys:
            superseded[k] = item
    for item in raw.get("superseded_docs", []):
        docs[item["doc_no"]] = item
    renumbered = {norm_name(i["name"]): i for i in raw.get("renumbered_laws", [])}

    # 全量索引（来自 chinese-law-corpus，CC0）：1513 部现行/待生效法规 + 条文总数
    if INDEX.exists():
        try:
            corpus = json.loads(INDEX.read_text(encoding="utf-8"))
        except Exception:
            corpus = {"laws": []}
        for item in corpus.get("laws", []):
            title = item.get("title") or ""
            key = norm_name(title)
            if not key:
                continue
            entry = {
                "name": title,
                "aliases": [],
                "article_count": item.get("articleCount"),
                "status": item.get("status"),
                "effective_from": item.get("effectiveDate"),
                "source": "chinese-law-corpus (CC0)",
            }
            if key not in laws:
                laws[key] = entry
            else:
                # 条数以全量索引（官方文本逐条解析）为准；精编条目只保留别名与备注
                if entry["article_count"]:
                    laws[key]["article_count"] = entry["article_count"]
                if not laws[key].get("effective_from"):
                    laws[key]["effective_from"] = entry["effective_from"]
        # 把精编别名挂到全量索引上，让「民法典」「民诉法解释」这类简称也能命中
        for key, item in list(laws.items()):
            for alias in item.get("aliases") or []:
                laws.setdefault(norm_name(alias), item)
        corpus_count = corpus.get("count") or len(corpus.get("laws", []))
    else:
        corpus_count = 0

    return {"laws": laws, "superseded": superseded, "docs": docs,
            "renumbered": renumbered, "raw": raw, "corpus_count": corpus_count}


RE_CITE = re.compile(r"《([^》\n]{2,80})》\s*(?:第\s*([0-9一二三四五六七八九十百千零〇两]{1,8})\s*条)")
RE_BARE = re.compile(r"(?<!《)第\s*([0-9一二三四五六七八九十百千零〇两]{1,8})\s*条")
RE_DOCNO = re.compile(r"法释\s*[〔\[(（]\s*(\d{4})\s*[〕\])）]\s*(\d+)\s*号")
RE_CASE = re.compile(r"[（(]\s*(\d{4})\s*[）)]\s*([\u4e00-\u9fa5]{1,8}\d*)\s*(民初|民终|民再|执|执异|刑初|刑终|行初|行终|行赔|民申|行申|执恢|破申|财保)\s*([\d]+)\s*号")


def extract_citations(text: str) -> list[dict]:
    items = []
    # 裸条号（第 N 条）只在同一行内续接前面的法名：
    # 跨行续接会把「上一个法名 + 下一个条号」错配成另一个法条，宁可标待核验也不猜。
    lines = text.splitlines()
    for ln, line in enumerate(lines, 1):
        covered = []
        line_law = None
        for m in RE_CITE.finditer(line):
            name, art = m.group(1), m.group(2)
            items.append({"line": ln, "kind": "法条", "raw": m.group(0),
                          "name": name, "article": cn_to_int(art), "start": m.start(), "end": m.end()})
            covered.append((m.start(), m.end()))
            line_law = name
        for m in RE_BARE.finditer(line):
            if any(a <= m.start() < b for a, b in covered):
                continue
            if not line_law:
                continue
            items.append({"line": ln, "kind": "法条(续)", "raw": m.group(0),
                          "name": line_law, "article": cn_to_int(m.group(1)),
                          "start": m.start(), "end": m.end()})
        for m in RE_DOCNO.finditer(line):
            items.append({"line": ln, "kind": "司法解释文号", "raw": m.group(0),
                          "doc_no": f"法释〔{m.group(1)}〕{m.group(2)}号",
                          "start": m.start(), "end": m.end()})
        for m in RE_CASE.finditer(line):
            items.append({"line": ln, "kind": "案号", "raw": m.group(0),
                          "start": m.start(), "end": m.end()})
    return items


def judge(item: dict, idx: dict) -> None:
    """就地写入 status / severity / note。"""
    if item["kind"] == "案号":
        item["status"] = "UNVERIFIED"
        item["severity"] = "info"
        item["note"] = "案号无法离线核验真伪；请在中国裁判文书网或法院系统核对是否存在"
        return

    if item["kind"] == "司法解释文号":
        doc_no = item["doc_no"]
        hit = idx["docs"].get(doc_no)
        if hit:
            item["status"] = "OUTDATED"
            item["severity"] = "material"
            item["note"] = f"该解释已于 {hit['invalid_since']} 被 {hit['replaced_by']} 取代，应改引新解释"
        else:
            item["status"] = "UNVERIFIED"
            item["severity"] = "info"
            item["note"] = "索引未收录该文号；请到最高人民法院官网核对文号与现行有效性"
        return

    name = item.get("name") or ""
    key = norm_name(name)

    old = idx["superseded"].get(key)
    if old:
        item["status"] = "OUTDATED"
        item["severity"] = "material"
        item["note"] = f"{old['invalid_since']} 起已被《{old['replaced_by']}》取代" + (
            "，" + old["note"] if old.get("note") else "")
        return

    law = idx["laws"].get(key)
    if law:
        art = item.get("article")
        count = law.get("article_count")
        if art is not None and count and art > count:
            item["status"] = "OUT_OF_RANGE"
            item["severity"] = "material"
            item["note"] = f"《{law['name']}》共 {count} 条，第 {art} 条超出条文总数"
            return
        if law.get("status") == "pending":
            item["status"] = "PENDING"
            item["severity"] = "warn"
            item["note"] = "该法已公布但尚未生效（施行日 " + str(law.get("effective_from") or "待核") + "），引用前确认案件适用时点"
            return
        if art is not None and count and art == 0:
            item["status"] = "OUT_OF_RANGE"
            item["severity"] = "material"
            item["note"] = "条号不可能是 0"
            return
        item["status"] = "OK"
        item["severity"] = "ok"
        if law.get("name") in idx["renumbered"]:
            item["status"] = "RENUMBERED"
            item["severity"] = "warn"
            item["note"] = idx["renumbered"][law["name"]]["note"]
        elif count:
            item["note"] = f"法名与条号在索引内（共 {count} 条）"
        else:
            item["note"] = "法名在索引内；该法条数未收录，条号未做越界判断"
        return

    item["status"] = "UNKNOWN"
    item["severity"] = "warn"
    item["note"] = "法名不在离线索引内；可能是简称、地方性法规或已失效文件，需人工核验"


SEV_ORDER = {"material": 0, "warn": 1, "info": 2, "ok": 3}


def read_file(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        try:
            from docx import Document  # type: ignore
        except Exception:
            raise SystemExit("读取 .docx 需要 python-docx：pip install python-docx")
        doc = Document(str(path))
        parts = [p.text for p in doc.paragraphs]
        for t in doc.tables:
            for row in t.rows:
                parts.append(" | ".join(c.text for c in row.cells))
        return "\n".join(parts)
    return path.read_text(encoding="utf-8", errors="replace")


def iter_inputs(root: Path):
    if root.is_file():
        yield root
        return
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in {".md", ".txt", ".docx"}:
            yield p


def write_csv(rows: list[dict], out: Path) -> None:
    cols = ["文件", "行号", "类型", "原文", "状态", "级别", "说明"]
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([r["file"], r["line"], r["kind"], r["raw"], r["status"],
                        r["severity"], r["note"]])


def write_report(rows: list[dict], out: Path, index: dict) -> None:
    total = len(rows)
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    material = [r for r in rows if r["severity"] == "material"]
    warn = [r for r in rows if r["severity"] == "warn"]

    lines = ["# 引用核验报告", ""]
    lines.append(f"- 核验时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"- 索引版本：{index['raw'].get('checked', '未标注')}（离线，不联网）")
    if index.get("corpus_count"):
        lines.append(f"- 覆盖范围：{index['corpus_count']} 部现行/待生效法规（chinese-law-corpus, CC0）")
    lines.append(f"- 引用总数：{total}")
    lines.append("")
    lines.append("| 状态 | 数量 |")
    lines.append("|---|---|")
    for k in ["OK", "RENUMBERED", "OUTDATED", "OUT_OF_RANGE", "UNKNOWN", "UNVERIFIED"]:
        if counts.get(k):
            lines.append(f"| {k} | {counts[k]} |")
    lines.append("")

    if material:
        lines.append("## 一、必须处理（material）")
        lines.append("")
        for r in material:
            lines.append(f"- **{r['file']}:{r['line']}** `{r['raw']}` — {r['status']}：{r['note']}")
        lines.append("")
    if warn:
        lines.append("## 二、需要人工核验")
        lines.append("")
        for r in warn:
            lines.append(f"- {r['file']}:{r['line']} `{r['raw']}` — {r['status']}：{r['note']}")
        lines.append("")

    lines.append("## 三、逐条明细")
    lines.append("")
    lines.append("| 文件 | 行 | 引用 | 状态 | 说明 |")
    lines.append("|---|---|---|---|---|")
    for r in rows:
        raw = r["raw"].replace("|", "\\|")
        note = r["note"].replace("|", "\\|")
        lines.append(f"| {r['file']} | {r['line']} | `{raw}` | {r['status']} | {note} |")
    lines.append("")
    lines.append("> 本报告只对离线索引负责。索引未收录 ≠ 引用正确；索引内通过 ≠ 该条适用于本案。")
    lines.append("> 正式提交前仍须由承办律师核对国家法律法规数据库（flk.npc.gov.cn）原文。")
    out.write_text("\n".join(lines), encoding="utf-8")


def highlight(text: str, hits: list[dict]) -> str:
    """按行内位置从后往前插入标记，避免位移。"""
    by_line: dict[int, list[dict]] = {}
    for h in hits:
        by_line.setdefault(h["line"], []).append(h)
    lines = text.splitlines()
    for ln, items in by_line.items():
        line = lines[ln - 1]
        for it in sorted(items, key=lambda x: x["start"], reverse=True):
            tag = "⚠️失效" if it["status"] == "OUTDATED" else (
                "⚠️越界" if it["status"] == "OUT_OF_RANGE" else "⚠️待核")
            line = line[:it["end"]] + f"〔{tag}〕" + line[it["end"]:]
        lines[ln - 1] = line
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="离线核验法律文书里的法条/司法解释/案号引用")
    ap.add_argument("input", help="文书文件或目录")
    ap.add_argument("-o", "--out", default=None, help="输出目录（默认在输入同级的 引用核验/）")
    ap.add_argument("--strict", action="store_true", help="存在 material 错误时退出码 1")
    args = ap.parse_args()

    idx = load_index()
    root = Path(args.input).expanduser()
    if not root.exists():
        print(f"找不到输入：{root}", file=sys.stderr)
        return 2

    outdir = Path(args.out).expanduser() if args.out else (
        root.parent / "引用核验" if root.is_file() else root / "引用核验")
    outdir.mkdir(parents=True, exist_ok=True)

    rows, all_hits = [], []
    for path in iter_inputs(root):
        text = read_file(path)
        items = extract_citations(text)
        # 补：只写了法名、没带条号的失效法律，也要提示（例：根据《合同法》……）
        anchored = {(it["line"], it["start"]) for it in items if it["kind"].startswith("法条")}
        for ln, line in enumerate(text.splitlines(), 1):
            for m in re.finditer(r"《([^》\n]{2,80})》", line):
                if (ln, m.start()) in anchored:
                    continue
                if norm_name(m.group(1)) in idx["superseded"]:
                    items.append({"line": ln, "kind": "法律名称", "raw": m.group(0),
                                  "name": m.group(1), "article": None,
                                  "start": m.start(), "end": m.end()})
        for it in items:
            judge(it, idx)
            it["file"] = path.name
            rows.append(it)
        if items:
            all_hits.append((path, text, items))
            hl = highlight(text, items)
            (outdir / f"{path.stem}.核验标注{path.suffix}").write_text(hl, encoding="utf-8")

    rows.sort(key=lambda r: (r["file"], r["line"], SEV_ORDER.get(r["severity"], 9)))

    write_csv(rows, outdir / "citations.csv")
    write_report(rows, outdir / "citations.md", idx)

    material = [r for r in rows if r["severity"] == "material"]
    print(f"共核验 {len(rows)} 处引用 → {outdir}")
    print(f"  必须处理 {len(material)} 处；需人工核验 {sum(1 for r in rows if r['severity']=='warn')} 处")
    for r in material[:10]:
        print(f"  ✗ {r['file']}:{r['line']} {r['raw']} — {r['note']}")
    if material and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
