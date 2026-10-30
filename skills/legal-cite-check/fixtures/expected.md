# 验收检查点（fixtures/case-01.md）

跑：

```bash
python3 scripts/check_citations.py fixtures/case-01.md -o /tmp/cite-out
```

## 必须包含

1. `《中华人民共和国合同法》第一百零七条` 判为 `OUTDATED`，说明里出现「民法典」。
2. `《民法典》第五百七十七条` 判为 `OK`（民法典共 1260 条）。
3. `《民法典》第一千三百条` 判为 `OUT_OF_RANGE`，说明里出现「1260」。
4. `法释〔2001〕14号` 判为 `OUTDATED`，说明里出现「法释〔2020〕26号」。
5. `《最高人民法院关于审理劳动争议案件适用法律若干问题的解释》`（只出现法名、无条号）也要被抓到并判 `OUTDATED`。
6. `（2026）浙0302民初1234号` 判为 `UNVERIFIED`，说明里明确「无法离线核验」。
7. 输出目录含 `citations.csv`、`citations.md`、`case-01.核验标注.md`。
8. `citations.md` 开头有「必须处理（material）」段；结尾保留「索引未收录 ≠ 引用正确」的边界声明。

## 不得包含

1. 不得把 `合同法` 判成 `OK` 或 `UNKNOWN`（它是已知失效法）。
2. 不得把案号判成 `OK`。
3. 不得因为 `第十三条` 单独出现就把它错配给上一行的《民事诉讼法》/旧劳动争议解释并判 `OK`——跨行裸条号必须丢弃或标待核。
4. 不得在没有任何引用的文档上报错（用空文档跑一遍，应为 0 条、退出码 0）。

## 严格模式

```bash
python3 scripts/check_citations.py fixtures/case-01.md --strict; echo $?
```

应输出 `1`（存在 material 错误），而普通模式退出码为 `0`。
