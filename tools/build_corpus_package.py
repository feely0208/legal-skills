#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把全量法条库（chinese-law-corpus，CC0）打成可选下载包。

输出：dist/deepwhale-legal-corpus-<版本>.zip
内容：laws-full.json.gz + README.md + LICENSE-CC0.txt
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = Path("/tmp/laws-full.json.gz")
DIST = ROOT / "dist"
VERSION = "2026.10"

README = """# 深鲸法条全文库（可选下载）

**1,513 部现行/待生效法律、行政法规、司法解释的逐条全文**，供「法条速查」技能使用。

## 安装

1. 先安装深鲸法律技能集（`skills/legal-statute-lookup/`）；
2. 解压本包，把 `laws-full.json.gz` 放到：

```
skills/legal-statute-lookup/data/laws-full.json.gz
```

3. 验证：

```bash
python3 skills/legal-statute-lookup/scripts/lookup.py --list
# 应显示：语料：全量库 1,513 部
```

## 数据来源与许可

- 来源：[chinese-law-corpus](https://github.com/lttxzmj/chinese-law-corpus)，以 **CC0 1.0** 释出；
- 官方文本取自国家法律法规数据库（flk.npc.gov.cn）；
- 本包只做字段裁剪与打包，未改动条文内容；
- 正式引用前仍须以国家法律法规数据库原文为准。

## 结构

```json
{
  "civil-code": {
    "title": "中华人民共和国民法典",
    "category": "法律",
    "status": "effective",
    "effectiveDate": "2021-01-01",
    "articles": [{"n": 577, "display": "第五百七十七条", "path": ["第三编合同"], "text": "..."}]
  }
}
```

## 体积

- 压缩包约 6 MB，解压后约 25 MB。
"""

LICENSE = """CC0 1.0 Universal

本数据包的编排、结构化与裁剪工作由温州深鲸智能科技有限公司完成，
依 CC0 1.0 放弃全部权利。法条文本本身依法不受著作权保护。

来源：https://github.com/lttxzmj/chinese-law-corpus
官方文本：https://flk.npc.gov.cn/
"""


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"缺少 {SRC}，先运行 tools/build_corpus.py 生成")
    DIST.mkdir(exist_ok=True)
    out = DIST / f"deepwhale-legal-corpus-{VERSION}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("legal-corpus-2026.10/README.md", README)
        z.writestr("legal-corpus-2026.10/LICENSE-CC0.txt", LICENSE)
        z.write(SRC, "legal-corpus-2026.10/laws-full.json.gz")
    print(f"✓ {out} ({out.stat().st_size/1024/1024:.2f} MB)")


if __name__ == "__main__":
    main()
