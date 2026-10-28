# -*- coding: utf-8 -*-
"""午盘 vs 尾盘：基于日K OHLC 的收益结构验证（无分钟数据，做近似）"""
import json, os
import numpy as np

BASE = r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847"
d = json.load(open(os.path.join(BASE, "temp", "kline_cache_em.json"), encoding="utf-8"))

overnight, intraday, to_next_close = [], [], []          # 全样本
overnight_big, intraday_big = [], []                     # 当日涨>=5% 分组（追强势股场景）
mid_buy_next, tail_buy_next = [], []                     # 午盘近似价买 vs 尾盘价买 → 次日收盘

for code, rows in d.items():
    # 仅主板
    if not (code.startswith("60") or code.startswith("00")):
        continue
    rows = sorted(rows, key=lambda r: r["date"])
    for i in range(len(rows) - 1):
        a, b = rows[i], rows[i + 1]
        o, c = a["open"], a["close"]
        if o <= 0 or c <= 0:
            continue
        # 全样本收益结构
        overnight.append(b["open"] / c - 1)          # 尾盘买 → 次日开盘
        intraday.append(c / o - 1)                   # 早盘买 → 当日收盘
        to_next_close.append(b["close"] / c - 1)     # 尾盘买 → 次日收盘
        # 当日强势(涨幅>=5%)分组：短线追强势
        pct = a.get("pct")
        if pct is not None and pct >= 5:
            overnight_big.append(b["open"] / c - 1)
            intraday_big.append(c / o - 1)
            # 午盘近似：假设午盘价格 = 日内中点 (O+C)/2
            mid = (o + c) / 2
            if mid > 0:
                mid_buy_next.append(b["close"] / mid - 1)   # 午盘买 → 次日收盘
                tail_buy_next.append(b["close"] / c - 1)    # 尾盘买 → 次日收盘

def stat(x, name):
    x = np.array(x)
    return (name, len(x), x.mean() * 100, np.median(x) * 100, x.std() * 100,
            np.percentile(x, 5) * 100, np.percentile(x, 95) * 100)

print(f"{'指标':<28}{'N':>8}{'均值%':>9}{'中位%':>9}{'std%':>8}{'P5%':>8}{'P95%':>8}")
for r in [
    stat(overnight, "尾盘买->次日开盘(隔夜)"),
    stat(intraday, "早盘买->当日收盘(日内)"),
    stat(to_next_close, "尾盘买->次日收盘(隔夜+次日)"),
    stat(overnight_big, "[强势]尾盘买->次日开盘"),
    stat(intraday_big, "[强势]早盘买->当日收盘"),
    stat(mid_buy_next, "[强势]午盘近似买->次日收盘"),
    stat(tail_buy_next, "[强势]尾盘买->次日收盘"),
]:
    print(f"{r[0]:<28}{r[1]:>8}{r[2]:>9.3f}{r[3]:>9.3f}{r[4]:>8.3f}{r[5]:>8.3f}{r[6]:>8.3f}")
