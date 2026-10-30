#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
legal-damages-calc · 四类损害赔偿计算（纯标准库，离线）

用法：
  python3 calc.py --type injury --medical 12000 --daily-income 300 --lost-days 20
  python3 calc.py --type labor --monthly-wage 8000 --work-years 3.5 --mode N
  python3 calc.py --type interest --principal 100000 --rate 6 --start 2024-01-01 --end 2024-12-31
  python3 calc.py --type penalty --base 200000 --rate 20 --actual-loss 20000
  python3 calc.py --demo --out ./赔偿计算
  python3 calc.py --type injury ... --json

原则：只做算术与校验，不联网、不查标准、不内置地方标准数字。
"""

import argparse
import csv
import json
import math
import os
import sys
from datetime import date, datetime

CATEGORY = {"injury": "人身损害", "labor": "劳动争议", "interest": "借款利息", "penalty": "违约金"}


def q2(x):
    """与 JS Math.round(x*100)/100 同口径（四舍五入到分）"""
    return math.floor(x * 100 + 0.5) / 100


def money(x):
    return f"{q2(x):.2f}"


def show(n):
    return str(int(n)) if float(n).is_integer() else str(q2(n)).rstrip("0").rstrip(".")


def parse_num(v):
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return float("nan")


def positive(v, name, errs):
    n = parse_num(v)
    if n is None:
        return None
    if math.isnan(n):
        errs.append(f"{name}必须是数字")
    elif n <= 0:
        errs.append(f"{name}必须大于 0")
    else:
        return n
    return None


def truthy(v):
    if v is True or v == 1:
        return True
    return str(v or "").strip().lower() in ("1", "true", "yes", "on", "是")


def parse_date(v, name, errs):
    s = str(v or "").strip()
    if not s:
        errs.append(f"{name}不能为空")
        return None
    try:
        d = datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        errs.append(f"{name}格式须为 YYYY-MM-DD（收到「{s}」）")
        return None
    if d.isoformat() != s:
        errs.append(f"{name}不是有效日期（收到「{s}」）")
        return None
    return d


def item(name, formula, sub, amount, basis, pending=None):
    it = {"name": name, "formula": formula, "sub": sub, "amount": q2(amount), "basis": basis}
    if pending:
        it["pending"] = pending
    return it


def summarize(kind, items, notes):
    total = q2(sum(i["amount"] for i in items))
    pending = [f'{i["name"]}：{i["pending"]}' for i in items if i.get("pending")]
    notes = list(notes) + ["本表为可复算草稿，不构成法律意见；正式主张前由承办律师复核当地标准与证据。"]
    return {"ok": True, "type": kind, "title": CATEGORY[kind], "items": items,
            "total": total, "notes": notes, "pending": pending}


# ────────────────────────────── 人身损害 ──────────────────────────────

def calc_injury(raw):
    e = []
    n = lambda k, label: positive(raw.get(k), label, e)
    medical = n("medical", "医疗费")
    daily_income = n("dailyIncome", "日收入")
    lost_days = n("lostDays", "误工天数")
    care_daily = n("careDaily", "护理日标准")
    care_days = n("careDays", "护理天数")
    nutrition_daily = n("nutritionDaily", "营养日标准")
    nutrition_days = n("nutritionDays", "营养期天数")
    meal_daily = n("mealDaily", "伙食补助日标准")
    hospital_days = n("hospitalDays", "住院天数")
    dis_base = n("disabilityBase", "残疾赔偿金基数")
    dis_years = n("disabilityYears", "残疾赔偿金年限")
    dis_coef_raw = n("disabilityCoef", "伤残系数")
    mental = n("mental", "精神损害抚慰金")
    transport = n("transport", "交通费")

    coef = None
    if dis_coef_raw is not None:
        if dis_coef_raw > 100:
            e.append("伤残系数不能大于 100（十级 10，一级 100；也可填 0.1）")
        else:
            coef = q2(dis_coef_raw / 100) if dis_coef_raw > 1 else dis_coef_raw

    pairs = [
        (daily_income, lost_days, "误工费需同时填写「日收入」与「误工天数」"),
        (care_daily, care_days, "护理费需同时填写「护理日标准」与「护理天数」"),
        (nutrition_daily, nutrition_days, "营养费需同时填写「营养日标准」与「营养期天数」"),
        (meal_daily, hospital_days, "住院伙食补助费需同时填写「日补助标准」与「住院天数」"),
        (dis_base, dis_years, "残疾赔偿金需同时填写「基数」与「年限」"),
    ]
    for a, b, msg in pairs:
        if (a is None) != (b is None):
            e.append(msg)
    if (dis_base is not None or dis_years is not None) and coef is None:
        e.append("已填残疾赔偿金基数/年限，还需填写「伤残系数」（十级 10，一级 100）")
    if e:
        return {"ok": False, "error": "；".join(e)}

    if not any(x is not None for x in (medical, daily_income, care_daily, nutrition_daily,
                                      meal_daily, dis_base, mental, transport)):
        return {"ok": False, "error": "人身损害：至少填写一项赔偿项目（医疗费/误工费/护理费/营养费/伙食补助/残疾赔偿金/精神抚慰金/交通费）"}

    items, notes = [], []
    if medical is not None:
        items.append(item("医疗费", "按票据金额合计", f"票据合计 {money(medical)} 元", medical, "民法典第1179条"))
    if daily_income is not None:
        items.append(item("误工费", "日收入 × 误工天数", f"{money(daily_income)} 元/日 × {show(lost_days)} 天",
                          daily_income * lost_days, "民法典第1179条"))
    if care_daily is not None:
        items.append(item("护理费", "护理日标准 × 护理天数", f"{money(care_daily)} 元/日 × {show(care_days)} 天",
                          care_daily * care_days, "民法典第1179条"))
    if nutrition_daily is not None:
        items.append(item("营养费", "营养日标准 × 营养期天数", f"{money(nutrition_daily)} 元/日 × {show(nutrition_days)} 天",
                          nutrition_daily * nutrition_days, "民法典第1179条"))
    if meal_daily is not None:
        items.append(item("住院伙食补助费", "日补助标准 × 住院天数", f"{money(meal_daily)} 元/日 × {show(hospital_days)} 天",
                          meal_daily * hospital_days, "民法典第1179条"))
    if dis_base is not None:
        items.append(item("残疾赔偿金", "基数 × 年限 × 伤残系数",
                          f"{money(dis_base)} × {show(dis_years)} 年 × {show(q2(coef * 100))}%",
                          dis_base * dis_years * coef,
                          "民法典第1179条；基数=受诉法院所在地上一年度城镇居民人均可支配收入",
                          "基数与年限须按受诉法院所在地标准核定"))
        notes.append(f"残疾赔偿金基数按 {money(dis_base)} 元填报，须以受诉法院所在地上一年度城镇居民人均可支配收入核定（各地不同，本表不含任何地方标准数字）。")
        notes.append("残疾赔偿金年限：自定残之日起按 20 年计；60 周岁以上每增 1 岁减 1 年，75 周岁以上按 5 年。")
    else:
        notes.append("未主张残疾赔偿金：如已构成伤残，须补填基数（当地上一年度城镇居民人均可支配收入）、年限与伤残系数。")
    if mental is not None:
        items.append(item("精神损害抚慰金", "酌定（无统一公式）", f"填报 {money(mental)} 元", mental,
                          "民法典第1183条", "金额由法院酌定，本表仅记录填报值"))
    if transport is not None:
        items.append(item("交通费", "按实际发生票据合计", f"票据合计 {money(transport)} 元", transport, "民法典第1179条"))

    notes.append("医疗费、交通费按实际票据金额计；后续治疗费、康复费、被扶养人生活费未计入本表。")
    notes.append("误工费以实际减少的收入为准；无固定收入的按近三年平均收入或当地同行业标准（需另行举证）。")
    if not any(i["name"] == "残疾赔偿金" for i in items):
        notes.append("如构成伤残，还须补做伤残等级鉴定——没有鉴定意见，残疾赔偿金无法确定。")
    return summarize("injury", items, notes)


# ────────────────────────────── 劳动争议 ──────────────────────────────

def calc_labor(raw):
    e = []
    wage = positive(raw.get("monthlyWage"), "月工资", e)
    years = positive(raw.get("workYears"), "工作年限", e)
    social = positive(raw.get("socialAvgWage"), "当地上年度职工月平均工资", e)
    ot_wd = positive(raw.get("otWeekday"), "平日加班小时", e)
    ot_rest = positive(raw.get("otRest"), "休息日加班小时", e)
    ot_hol = positive(raw.get("otHoliday"), "法定节假日加班小时", e)
    leave_days = positive(raw.get("annualLeaveDays"), "未休年假天数", e)
    double_months = positive(raw.get("doubleWageMonths"), "未签书面合同月数", e)
    notice = truthy(raw.get("noticeMonth"))
    mode = "2N" if str(raw.get("mode") or "N").strip().upper() == "2N" else "N"
    if wage is not None and wage > 1e8:
        e.append("月工资数值异常（超过 1 亿元），请检查单位是否为「元」")
    if double_months is not None and double_months > 11:
        e.append("未签书面合同月数最多 11 个月（第 1 个月为宽限期）")
    if e:
        return {"ok": False, "error": "；".join(e)}
    if wage is None:
        return {"ok": False, "error": "劳动争议：必须填写「月工资」（解除前 12 个月平均应得工资，税前）"}

    has_claim = any(x is not None for x in (years, ot_wd, ot_rest, ot_hol, leave_days, double_months)) or notice
    if not has_claim:
        return {"ok": False, "error": "劳动争议：至少填写一项主张（工作年限/代通知金/加班小时/未休年假/未签合同月数）"}
    if mode == "2N" and years is None:
        return {"ok": False, "error": "赔偿金 2N 需填写「工作年限」"}

    items, notes = [], []
    months = 0.0
    if years is not None:
        total_months = round(years * 12)
        full = total_months // 12
        rem = total_months % 12
        months = full + (1 if rem >= 6 else 0.5 if rem > 0 else 0)
        if months <= 0:
            months = 0.5

    base = wage
    capped = False
    if social is not None and wage > 3 * social:
        base = 3 * social
        capped = True
        if months > 12:
            months = 12

    if years is not None:
        if mode == "2N":
            items.append(item("违法解除赔偿金（2N）", "经济补偿 N × 2",
                              f"{money(base)} 元 × {show(months)} 个月 × 2", base * months * 2,
                              "劳动合同法第87条", "已按 3 倍社平封顶且年限不超过 12 年" if capped else "未做 3 倍社平封顶校验"))
        else:
            items.append(item("经济补偿（N）", "月工资 × 补偿月数",
                              f"{money(base)} 元 × {show(months)} 个月", base * months,
                              "劳动合同法第47条", "已按 3 倍社平封顶且年限不超过 12 年" if capped else "未做 3 倍社平封顶校验"))
        notes.append(f"补偿月数按「每满 1 年 1 个月；6 个月以上不满 1 年按 1 年；不满 6 个月半个月」折算：工作 {show(years)} 年 → {show(months)} 个月。")
    if mode == "2N" and years is not None:
        notes.append("经济补偿 N 与违法解除赔偿金 2N 只能主张其一，本表按【2N】口径计算，未叠加。")
    elif years is not None:
        notes.append("经济补偿 N 与违法解除赔偿金 2N 只能主张其一，本表按【N】口径计算；如系违法解除，可改选 2N。")

    if capped:
        notes.append(f"月工资高于当地上年度职工月平均工资 3 倍（{money(3 * social)} 元），已按 3 倍计（{money(base)} 元），且补偿年限不超过 12 年（劳动合同法第47条第2款）。")
    else:
        notes.append("未填当地上年度职工月平均工资，未做 3 倍封顶校验：如月工资高于当地社平 3 倍，经济补偿按 3 倍计且年限最高 12 年（劳动合同法第47条第2款）。")
    notes.append("月工资按解除或终止前 12 个月平均应得工资计（税前，含奖金、津贴、补贴）。")

    if notice:
        items.append(item("代通知金", "1 个月工资", f"{money(wage)} 元 × 1", wage, "劳动合同法第40条"))
        notes.append("代通知金仅适用劳动合同法第 40 条的三种情形，且用人单位未提前 30 日书面通知时才支付；第 39 条过失性解除没有代通知金。")

    if any(x is not None for x in (ot_wd, ot_rest, ot_hol)):
        hourly = wage / 21.75 / 8
        factor = 1.5 * (ot_wd or 0) + 2 * (ot_rest or 0) + 3 * (ot_hol or 0)
        items.append(item("加班费", "小时工资 × (1.5×平日 + 2×休息日 + 3×法定节假日)",
                          f"{money(wage)} ÷ 21.75 ÷ 8 × (1.5×{show(ot_wd or 0)} + 2×{show(ot_rest or 0)} + 3×{show(ot_hol or 0)})",
                          hourly * factor, "劳动法第44条"))
        notes.append(f"小时工资 = 月工资 ÷ 21.75 ÷ 8 = {money(wage)} ÷ 21.75 ÷ 8 ≈ {money(hourly)} 元/小时（中间值不四舍五入，直接用算式复核）；21.75 为计薪天数，不是当月实际工作日。")
        notes.append("休息日加班已安排补休的不再支付 2 倍；法定节假日加班不能用补休替代。")

    if leave_days is not None:
        daily = wage / 21.75
        items.append(item("未休年休假工资", "日工资 × 未休天数 × 200%",
                          f"{money(wage)} ÷ 21.75 × {show(leave_days)} 天 × 200%", daily * leave_days * 2,
                          "职工带薪年休假条例第5条"))
        notes.append("未休年假法定按日工资 300% 支付，其中 100% 为已发的正常工资，故本表只计另行支付的 200%。")

    if double_months is not None:
        items.append(item("二倍工资差额", "月工资 × 未签月数（补差额一倍）",
                          f"{money(wage)} 元 × {show(double_months)} 个月", wage * double_months,
                          "劳动合同法第82条"))
        notes.append("二倍工资差额 = 再补一倍（已发一倍）；最多 11 个月（用工满 1 个月次日起至满 1 年前一日），并注意仲裁时效。")

    return summarize("labor", items, notes)


# ────────────────────────────── 借款利息 ──────────────────────────────

def calc_interest(raw):
    e = []
    principal = positive(raw.get("principal"), "本金", e)
    if e:
        return {"ok": False, "error": "；".join(e)}
    if principal is None:
        return {"ok": False, "error": "借款利息：必须填写「本金」"}

    segs = [s for s in (raw.get("segments") or []) if isinstance(s, dict)]
    items, notes = [], []
    if segs:
        total_days = 0
        for idx, s in enumerate(segs, 1):
            se = []
            rate = positive(s.get("rate"), f"第{idx}段年利率", se)
            a = parse_date(s.get("start"), f"第{idx}段起算日", se)
            b = parse_date(s.get("end"), f"第{idx}段截止日", se)
            if rate is None and not se:
                se.append(f"第{idx}段缺少年利率")
            if a and b and (b - a).days <= 0:
                se.append(f"第{idx}段截止日必须晚于起算日")
            if se:
                return {"ok": False, "error": "；".join(se)}
            days = (b - a).days
            total_days += days
            amount = principal * (rate / 100) * days / 365
            items.append(item(f"利息（第 {idx} 段）", "本金 × 年利率 × 天数 ÷ 365",
                              f"{money(principal)} × {show(rate)}% × {days} ÷ 365（{s.get('start')} ~ {s.get('end')}）",
                              amount, "民法典第674条、第676条"))
        notes.append(f"分段计息共 {len(segs)} 段、合计 {total_days} 天，各段按各自利率计算后相加。")
    else:
        rate = positive(raw.get("rate"), "年利率", e)
        a = parse_date(raw.get("start"), "起算日", e)
        b = parse_date(raw.get("end"), "截止日", e)
        if rate is None and not e:
            e.append("借款利息：必须填写「年利率」")
        if e:
            return {"ok": False, "error": "；".join(e)}
        days = (b - a).days
        if days <= 0:
            return {"ok": False, "error": "截止日必须晚于起算日（算头不算尾，同一天为 0 天）"}
        items.append(item("利息", "本金 × 年利率 × 天数 ÷ 365",
                          f"{money(principal)} × {show(rate)}% × {days} ÷ 365", principal * (rate / 100) * days / 365,
                          "民法典第674条、第676条"))
        notes.append(f"计息天数 {days} 天（{raw.get('start')} 起算，{raw.get('end')} 不计入，算头不算尾）。")

    notes.append("按 365 天/年单利计算，未计复利、未计已还本金冲抵；如有还款，请按每次还款日拆分本金后分段计算。")
    notes.append("民间借贷利率不得超过合同成立时一年期 LPR 的四倍，超过部分不受保护；LPR 数值请按合同成立日自行核对（本表不内置）。")
    notes.append("约定不明的自然人之间借款视为不支付利息（民法典第680条）；逾期利息与违约金、其他费用总计仍受利率上限约束。")
    return summarize("interest", items, notes)


# ────────────────────────────── 违约金 ──────────────────────────────

def calc_penalty(raw):
    e = []
    base = positive(raw.get("base"), "违约金计算基数", e)
    rate = positive(raw.get("rate"), "约定比例", e)
    amount_in = positive(raw.get("amount"), "约定违约金金额", e)
    loss = positive(raw.get("actualLoss"), "实际损失", e)
    if e:
        return {"ok": False, "error": "；".join(e)}
    if base is None:
        return {"ok": False, "error": "违约金：必须填写「计算基数」（合同总价/未履行部分价款/定金，以合同约定为准）"}
    if rate is None and amount_in is None:
        return {"ok": False, "error": "违约金：必须填写「约定比例」或「约定金额」之一"}
    if rate is not None and rate > 1000:
        return {"ok": False, "error": "约定比例数值异常（超过 1000%），请检查是否误填小数"}

    items, notes = [], []
    if rate is not None:
        amount = q2(base * rate / 100)
        items.append(item("违约金", "基数 × 约定比例", f"{money(base)} × {show(rate)}%", amount, "民法典第585条第1款"))
        if amount_in is not None and abs(amount_in - amount) > 0.01:
            notes.append(f"填报的约定金额 {money(amount_in)} 元与按比例算出的 {money(amount)} 元不一致，本表按比例计；请核对合同条款。")
    else:
        amount = q2(amount_in)
        items.append(item("违约金", "按合同约定金额", f"约定 {money(amount_in)} 元", amount, "民法典第585条第1款"))

    notes.append("违约金基数须以合同约定为准（合同总价 / 未履行部分价款 / 定金）；合同未写明基数的，本表按填报值暂计并列入待核。")

    if loss is not None:
        threshold = q2(loss * 1.3)
        if amount > threshold:
            notes.append(f"🔴 调减风险：约定违约金 {money(amount)} 元 > 实际损失 {money(loss)} 元 × 1.3 = {money(threshold)} 元，违约方可依民法典第585条第2款请求适当减少（司法实践以超过损失 30% 为「过分高于」的一般参考）。")
            notes.append("应对：守约方补充损失证据（价款差额、另行采购差价、逾期收益、维权费用）；违约方从损失未实际发生、可预见性抗辩。")
        elif amount < loss:
            notes.append(f"🟡 违约金 {money(amount)} 元低于实际损失 {money(loss)} 元，守约方可请求增加，但须举证损失金额（民法典第585条第2款）。")
        else:
            notes.append(f"未超过损失 130%（阈值 {money(threshold)} 元），被调减风险较低；仍须准备损失证据。")
    else:
        notes.append("未填实际损失，无法做 30% 比对：民法典第585条第2款允许在「过分高于损失」时调减，司法实践一般以超过损失 30% 为参考；请补填损失金额后复核。")
    notes.append("违约金与继续履行可以并存；违约金与损失赔偿一般择一主张，违约金不足以弥补损失的可请求增加（需证明损失）。")
    return summarize("penalty", items, notes)


def calc(kind, raw):
    k = str(kind or "").strip().lower()
    if k not in CATEGORY:
        return {"ok": False, "error": f"不支持的计算类型「{kind or ''}」；可选：" + "、".join(f"{a}（{b}）" for a, b in CATEGORY.items())}
    fn = {"injury": calc_injury, "labor": calc_labor, "interest": calc_interest, "penalty": calc_penalty}[k]
    try:
        return fn(raw if isinstance(raw, dict) else {})
    except Exception as ex:  # 坏输入不崩
        return {"ok": False, "error": f"计算失败：{ex}"}


# ────────────────────────────── 产物 ──────────────────────────────

def build_csv(r):
    rows = [["类别", "项目", "公式", "代入值", "金额（元）", "依据", "待核项"]]
    for i in r["items"]:
        rows.append([r["title"], i["name"], i["formula"], i["sub"], f'{i["amount"]:.2f}', i["basis"], i.get("pending", "")])
    rows.append([r["title"], "合计", "", "", f'{r["total"]:.2f}', "", ""])
    lines = []
    for row in rows:
        cells = []
        for c in row:
            s = str(c if c is not None else "")
            cells.append('"' + s.replace('"', '""') + '"' if any(ch in s for ch in ',"\r\n') else s)
        lines.append(",".join(cells))
    return "\ufeff" + "\r\n".join(lines) + "\r\n"


def build_md(r, generated_at=""):
    out = [f'# {r["title"]}赔偿计算说明', ""]
    out += [f"- 生成时间：{generated_at}", f'- 计算类型：{r["title"]}（{r["type"]}）', "- 金额口径：人民币元，保留两位小数；各项先四舍五入再相加", ""]
    out += [f'## 合计：{r["total"]:.2f} 元（{len(r["items"])} 项）', ""]
    out += ["| 项目 | 公式 | 代入值 | 金额（元） | 依据 |", "|---|---|---|---:|---|"]
    for i in r["items"]:
        out.append(f'| {i["name"]} | {i["formula"]} | {i["sub"]} | {i["amount"]:.2f} | {i["basis"]} |')
    out += [f'| **合计** |  |  | **{r["total"]:.2f}** |  |', "", "## 提示与依据", ""]
    out += [f"- {n}" for n in r["notes"]]
    out += ["", "## 待核项", ""]
    if r["pending"]:
        out += [f"- [ ] {p}" for p in r["pending"]]
    else:
        out.append("- [ ] 无脚本判定项；仍须核对票据、合同条款与当地标准出处")
    out += ["- [ ] 受诉法院所在地 / 当地上一年度标准（如涉及残疾赔偿金、社平工资封顶）", "", "## 复核方法", ""]
    out += ["逐行用「公式 + 代入值」在计算器上重算，结果应与「金额」一致；合计应等于各行金额之和。", ""]
    out.append("> AI 辅助生成，需承办律师复核。本表只做算术，不替代责任认定、证据审查与法律判断。")
    return "\n".join(out) + "\n"


DEMO = {
    "injury": dict(medical=12000, dailyIncome=300, lostDays=20, careDaily=150, careDays=10,
                   nutritionDaily=30, nutritionDays=20, mealDaily=50, hospitalDays=15,
                   disabilityBase=40000, disabilityYears=20, disabilityCoef=10, mental=5000, transport=800),
    "labor": dict(monthlyWage=8000, workYears=3.5, socialAvgWage=10000, mode="N", noticeMonth=False),
    "interest": dict(principal=100000, rate=6, start="2024-01-01", end="2024-12-31"),
    "penalty": dict(base=200000, rate=20, actualLoss=20000),
}


def text_summary(r):
    lines = [f'{r["title"]}：合计 {r["total"]:.2f} 元（{len(r["items"])} 项）']
    for i in r["items"]:
        lines.append(f'  {i["name"]}  {i["sub"]}  = {i["amount"]:.2f}')
    lines.append("")
    lines += [f"- {n}" for n in r["notes"]]
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(add_help=True, description="深鲸损害赔偿计算器（离线）")
    p.add_argument("--type", help="injury / labor / interest / penalty")
    p.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    p.add_argument("--demo", action="store_true", help="用内置四类样例跑一遍")
    p.add_argument("--out", default="", help="输出目录（生成 计算表.csv 与 计算说明.md）")
    for k in ("medical daily-income lost-days care-daily care-days nutrition-daily nutrition-days "
              "meal-daily hospital-days disability-base disability-years disability-coef mental transport "
              "monthly-wage work-years social-avg-wage ot-weekday ot-rest ot-holiday annual-leave-days "
              "double-wage-months mode notice-month principal rate start end base amount actual-loss").split():
        p.add_argument("--" + k, dest=k.replace("-", "_"), default=None)
    a = p.parse_args(argv)

    if a.demo:
        results = []
        for t in CATEGORY:
            r = calc(t, DEMO[t])
            if not r["ok"]:
                print("❌ " + r["error"], file=sys.stderr)
                return 2
            results.append(r)
        outdir = a.out or os.path.join(os.getcwd(), "赔偿计算-样例")
        os.makedirs(outdir, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        for r in results:
            with open(os.path.join(outdir, f'计算表-{r["type"]}.csv'), "w", encoding="utf-8") as f:
                f.write(build_csv(r))
            with open(os.path.join(outdir, f'计算说明-{r["type"]}.md'), "w", encoding="utf-8") as f:
                f.write(build_md(r, stamp))
        if a.json:
            print(json.dumps({"ok": True, "out": outdir, "results": results}, ensure_ascii=False, indent=2))
        else:
            for r in results:
                print(text_summary(r))
                print()
            print(f"产物目录：{outdir}")
            print("  " + "、".join(f'计算表-{r["type"]}.csv / 计算说明-{r["type"]}.md' for r in results))
        return 0

    if not a.type:
        p.print_help()
        return 2

    raw = {k: getattr(a, k) for k in (
        "medical daily_income lost_days care_daily care_days nutrition_daily nutrition_days meal_daily hospital_days "
        "disability_base disability_years disability_coef mental transport monthly_wage work_years social_avg_wage "
        "ot_weekday ot_rest ot_holiday annual_leave_days double_wage_months mode notice_month principal rate start end "
        "base amount actual_loss").split() if getattr(a, k) is not None}
    # 显式映射为引擎字段名（camelCase）
    mapping = {
        "daily_income": "dailyIncome", "lost_days": "lostDays", "care_daily": "careDaily", "care_days": "careDays",
        "nutrition_daily": "nutritionDaily", "nutrition_days": "nutritionDays", "meal_daily": "mealDaily",
        "hospital_days": "hospitalDays", "disability_base": "disabilityBase", "disability_years": "disabilityYears",
        "disability_coef": "disabilityCoef", "monthly_wage": "monthlyWage", "work_years": "workYears",
        "social_avg_wage": "socialAvgWage", "ot_weekday": "otWeekday", "ot_rest": "otRest", "ot_holiday": "otHoliday",
        "annual_leave_days": "annualLeaveDays", "double_wage_months": "doubleWageMonths", "notice_month": "noticeMonth",
        "actual_loss": "actualLoss",
    }
    raw = {mapping.get(k, k): v for k, v in raw.items()}

    r = calc(a.type, raw)
    if not r["ok"]:
        if a.json:
            print(json.dumps({"ok": False, "error": r["error"]}, ensure_ascii=False, indent=2))
        else:
            print("❌ " + r["error"], file=sys.stderr)
        return 2

    if a.out:
        os.makedirs(a.out, exist_ok=True)
        with open(os.path.join(a.out, "计算表.csv"), "w", encoding="utf-8") as f:
            f.write(build_csv(r))
        with open(os.path.join(a.out, "计算说明.md"), "w", encoding="utf-8") as f:
            f.write(build_md(r, datetime.now().strftime("%Y-%m-%d %H:%M")))
        r["outputs"] = {"dir": a.out, "csv": os.path.join(a.out, "计算表.csv"), "md": os.path.join(a.out, "计算说明.md")}

    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(text_summary(r))
        if a.out:
            print(f'\n产物目录：{a.out}\n  计算表.csv\n  计算说明.md')
    return 0


if __name__ == "__main__":
    sys.exit(main())
