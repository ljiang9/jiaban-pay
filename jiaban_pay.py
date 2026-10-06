#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jiaban-pay: 国庆加班费计算器。

娱乐 + 实用小工具：输入月薪和国庆 7 天中加班的日期，
按"10/1-3 法定节假日 3 倍、10/4-7 休息日 2 倍"的简化规则估算加班费，
附奶茶换算和玩梗评语。

纯 Python 标准库，Python 3.10+。
"""

from __future__ import annotations

import argparse
import sys

MONTHLY_WORKDAYS = 21.75    # 月计薪天数
HOURS_PER_DAY = 8           # 每日标准工时（简化）
STATUTORY_DAYS = {1, 2, 3}  # 法定节假日：300%（另行支付，不含本薪）
WEEKEND_DAYS = {4, 5, 6, 7}  # 休息日：200%（另行支付，不含本薪）
ALL_DAYS = set(range(1, 8))


class InputError(Exception):
    """用户输入非法。"""


# ---------------- 输入解析 ----------------

def parse_salary(text):
    """解析月薪：必须为正数。"""
    if text is None:
        raise InputError("未提供月薪，请用 --salary 指定")
    try:
        salary = float(str(text).strip())
    except (TypeError, ValueError):
        raise InputError(f"月薪必须是数字: {text!r}")
    if salary <= 0:
        raise InputError("月薪必须大于 0")
    if salary > 10_000_000:
        raise InputError("月薪大得离谱，请重新输入")
    return salary


def parse_days(text):
    """解析加班日期。

    支持 '1,2,3'、'1 2 3'、'1-3'、中文逗号；返回排序去重后的列表。
    空字符串视为没加班；非法输入抛 InputError。
    """
    if text is None:
        raise InputError("未指定加班日期")
    text = str(text).strip().replace("，", ",").replace("；", ",").replace(";", ",")
    if not text:
        return []
    days = []
    for chunk in text.split(","):
        for part in chunk.split():
            if "-" in part:
                left, right = part.split("-", 1)
                try:
                    lo, hi = int(left), int(right)
                except ValueError:
                    raise InputError(f"日期格式非法: {part!r}")
                if lo > hi:
                    raise InputError(f"日期区间非法: {part!r}")
                days.extend(range(lo, hi + 1))
            else:
                try:
                    days.append(int(part))
                except ValueError:
                    raise InputError(f"日期格式非法: {part!r}")
    for d in days:
        if d not in ALL_DAYS:
            raise InputError(f"日期超出国庆 7 天范围(1-7): {d}")
    return sorted(set(days))


def parse_milktea(text):
    """解析奶茶单价：必须为正数。"""
    try:
        price = float(str(text).strip())
    except (TypeError, ValueError):
        raise InputError(f"奶茶单价必须是数字: {text!r}")
    if price <= 0:
        raise InputError("奶茶单价必须大于 0")
    return price


# ---------------- 核心计算 ----------------

def daily_wage(salary):
    """日薪 = 月薪 / 21.75。"""
    return salary / MONTHLY_WORKDAYS


def compute(salary, days):
    """返回 (日薪, 明细列表, 加班费总额)。"""
    dw = daily_wage(salary)
    items = []
    for d in sorted(days):
        mult = 3 if d in STATUTORY_DAYS else 2
        items.append({
            "day": d,
            "kind": "法定节假日" if d in STATUTORY_DAYS else "休息日",
            "mult": mult,
            "amount": dw * mult,
        })
    total = sum(i["amount"] for i in items)
    return dw, items, total


# ---------------- 玩梗评语 ----------------

def comment(days, total, cups):
    s = set(days)
    if not s:
        return "聪明人！7 天全休，加班费 0 元，但快乐无价，好好享受假期。"
    if s == ALL_DAYS:
        return (f"你就是公司最靓的牛马！7 天全勤拿下 {total:.2f} 元 ≈ {cups:.0f} 杯奶茶，"
                "但身体是革命的本钱——还是好好休息吧！")
    if s == STATUTORY_DAYS:
        return "精准拿下三倍，理财鬼才！三天法定假一分没浪费。"
    if s == WEEKEND_DAYS:
        return "曲线救国专攻双倍？也行吧，至少没白干。"
    if s <= STATUTORY_DAYS:
        return "专挑三倍下手，有头脑！"
    return f"加班 {len(days)} 天，{total:.2f} 元落袋，奶茶自由 +{cups:.0f} 杯。"


# ---------------- 报告与对比 ----------------

def make_report(salary, days, milktea):
    dw, items, total = compute(salary, days)
    cups = total / milktea
    hours = len(days) * HOURS_PER_DAY
    lines = [
        "国庆加班费计算",
        f"月薪：{salary:.2f} 元，日薪：{dw:.2f} 元（月薪 ÷ 21.75）",
        "-" * 40,
    ]
    for it in items:
        lines.append(f"10/{it['day']}（{it['kind']}） {it['mult']}倍  {it['amount']:.2f} 元")
    lines.append("-" * 40)
    lines.append(f"加班费合计：{total:.2f} 元")
    if days:
        lines.append(f"加班 {hours} 小时 ≈ {cups:.1f} 杯奶茶（{milktea:g} 元/杯）")
    lines.append("")
    lines.append("💬 " + comment(days, total, cups))
    lines.append("")
    lines.append("（简化估算，仅供参考，实际以单位核算为准）")
    return "\n".join(lines)


def compare_plans(salary, milktea):
    """对比：加班 7 天赚的钱 vs 请 3 天假拼出 13 天假期，哪个值。"""
    dw = daily_wage(salary)
    overtime_total = dw * (3 * 3 + 4 * 2)  # 10/1-3 三倍 + 10/4-7 双倍 = 17 倍日薪
    cups = overtime_total / milktea
    leave_cost = dw * 3                    # 请 3 天年假的机会成本
    leverage = 13 / 3
    lines = [
        "国庆终极抉择：加班赚钱 vs 请假拼假",
        "",
        "【方案 A：7 天全勤加班】",
        f"  加班费 = 17 × 日薪 = {overtime_total:.2f} 元 ≈ {cups:.1f} 杯奶茶（{milktea:g} 元/杯）",
        "  代价：7 天假期清零，喜提「最靓牛马」称号。",
        "",
        "【方案 B：请 3 天假，拼出 13 天假期】",
        f"  成本：3 天年假（约 {leave_cost:.2f} 元日薪价值）",
        f"  收获：13 天连续假期，假期杠杆 13÷3 ≈ {leverage:.2f}（每请 1 天换 {leverage:.2f} 天假）",
        "",
        "【结论】",
    ]
    if overtime_total >= leave_cost * 3:
        ratio = overtime_total / leave_cost
        lines.append(f"  加班费是 3 天假成本的 {ratio:.1f} 倍——钱是真香，选 A 不丢人。")
    else:
        lines.append("  这点加班费连假期零头都比不上，选 B 当时间管理大师不香吗？")
    lines.append("  终极建议：钱买不来快乐，但没钱快乐打折——按自己心意选。")
    return "\n".join(lines)


# ---------------- CLI ----------------

def build_parser():
    p = argparse.ArgumentParser(
        prog="jiaban-pay",
        description="国庆加班费计算器：10/1-3 法定节假日 3 倍，10/4-7 休息日 2 倍（简化估算，仅供参考）。",
    )
    p.add_argument("--salary", type=str, default=None, help="税前月薪（元），如 8000")
    p.add_argument("--days", type=str, default=None,
                   help="加班日期：10月1-7号多选，如 '1,2,3'（也支持 1-3 区间写法）")
    p.add_argument("--milktea", type=str, default="15", help="奶茶单价（元），默认 15")
    p.add_argument("--compare", action="store_true",
                   help="对比：加班 7 天赚的钱 vs 请 3 天假拼出 13 天假期，哪个值")
    return p


def ask_interactive(prompt_text, what):
    if not sys.stdin.isatty():
        raise InputError(f"非交互终端：请用 {what} 参数指定")
    try:
        return input(prompt_text)
    except EOFError:
        raise InputError("输入中断")


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.salary is not None:
            salary = parse_salary(args.salary)
        else:
            salary = parse_salary(ask_interactive("请输入税前月薪（元）: ", "--salary"))
        milktea = parse_milktea(args.milktea)
        if args.compare:
            print(compare_plans(salary, milktea))
            return 0
        if args.days is not None:
            days = parse_days(args.days)
        else:
            days = parse_days(ask_interactive(
                "请输入加班日期（10月1-7号多选，如 1,2,3；直接回车=没加班）: ", "--days"))
        print(make_report(salary, days, milktea))
        return 0
    except InputError as e:
        print(f"输入有误：{e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
