# -*- coding: utf-8 -*-
"""尾盘可成交策略矩阵：排除封死涨停，测各涨幅分档 + 炸板回落 的尾盘买入次日卖出期望"""
import json, os
import numpy as np

BASE = r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847"
d = json.load(open(os.path.join(BASE, "temp", "kline_cache_em.json"), encoding="utf-8"))

recs = []  # (code, date, pct, prev_close, close, open_next, close_next, close_next2, hit_limit, zhaban)
for code, rows in d.items():
    if not (code.startswith("60") or code.startswith("00")):
        continue
    rows = sorted(rows, key=lambda r: r["date"])
    for i in range(len(rows) - 1):
        a, b = rows[i], rows[i + 1]
        if i == 0:
            prev_close = None
        else:
            prev_close = rows[i - 1]["close"]
        if prev_close is None or prev_close <= 0 or a["close"] <= 0:
            continue
        pct = a["close"] / prev_close - 1
        # 是否盘中触及涨停(近似10%)：high涨幅 >= 9.7%
        high_pct = a["high"] / prev_close - 1
        hit_limit = high_pct >= 0.097
        # 炸板：盘中触板但收盘未封（收盘涨幅<9.5%，主板10%涨停，留缓冲）
        zhaban = hit_limit and pct < 0.095
        recs.append({
            "pct": pct, "hit_limit": hit_limit, "zhaban": zhaban,
            "o_next": b["open"] / a["close"] - 1,          # 次日开盘卖
            "c_next": b["close"] / a["close"] - 1,         # 次日收盘卖
            "c_next2": (rows[i+2]["close"] / a["close"] - 1) if i + 2 < len(rows) else None,  # 持2日
        })

print(f"总样本: {len(recs)}")
print(f"盘中触板样本: {sum(r['hit_limit'] for r in recs)}  炸板样本: {sum(r['zhaban'] for r in recs)}")

def eval_group(name, sub, keys):
    if not sub:
        print(f"{name:<24} N=0")
        return
    for k in keys:
        arr = np.array([r[k] for r in sub if r[k] is not None])
        if len(arr) == 0:
            print(f"{name:<24} {k:<10} N=0")
            continue
        wr = (arr > 0).mean() * 100
        print(f"{name:<24} {k:<10} N={len(arr):>5} 均值{arr.mean()*100:>7.3f}% 中位{np.median(arr)*100:>7.3f}% 胜率{wr:>5.1f}% 最大单次{arr.min()*100:>7.1f}%")

print("\n===== A. 涨幅分档(收盘涨幅, 排除封板>=9.5%) =====")
bins = [(0, 0.02, "0~2%"), (0.02, 0.04, "2~4%"), (0.04, 0.06, "4~6%"), (0.06, 0.08, "6~8%"), (0.08, 0.095, "8~9.5%")]
for lo, hi, lbl in bins:
    sub = [r for r in recs if lo <= r["pct"] < hi and not (r["pct"] >= 0.095)]
    eval_group(f"A {lbl}", sub, ["o_next", "c_next"])

print("\n===== B. 炸板回落(盘中触板但未封, 收盘各区间) =====")
sub_z = [r for r in recs if r["zhaban"]]
for lo, hi, lbl in bins:
    sub = [r for r in sub_z if lo <= r["pct"] < hi]
    eval_group(f"B 炸板{lbl}", sub, ["o_next", "c_next"])
eval_group("B 炸板全部", sub_z, ["o_next", "c_next"])

print("\n===== C. 涨停封板样本(对照, 买不进) =====")
sub_lock = [r for r in recs if r["pct"] >= 0.095]
eval_group("C 封板>=9.5%", sub_lock, ["o_next", "c_next"])

print("\n===== D. 前一日炸板/封板 -> 今日尾盘买(收盘涨幅0~6%) =====")
# 用前一日状态分组
prev_flags = {}
for i, r in enumerate(recs):
    prev_flags[i] = {"zhaban": r["zhaban"], "hit_limit": r["hit_limit"], "pct": r["pct"]}
# 次日记录需要 prev 标识：简化为按索引相邻
new_recs = []
for i in range(1, len(recs)):
    pr = prev_flags[i-1]
    r = recs[i]
    r2 = dict(r)
    r2["prev_zhaban"] = pr["zhaban"]
    r2["prev_lock"] = pr["pct"] >= 0.095
    new_recs.append(r2)

sub_d1 = [r for r in new_recs if r["prev_zhaban"] and 0 <= r["pct"] < 0.06]   # 昨日炸板今日未大涨
sub_d2 = [r for r in new_recs if r["prev_lock"] and 0 <= r["pct"] < 0.06]    # 昨日封板今日未封
eval_group("D 昨炸板今0~6%", sub_d1, ["o_next", "c_next"])
eval_group("D 昨涨停今0~6%", sub_d2, ["o_next", "c_next"])
