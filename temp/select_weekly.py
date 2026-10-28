# -*- coding: utf-8 -*-
"""
周频选股脚本 select_weekly.py
策略: v9七因子周频 · Top5 · 止损-12% · 评分强度过滤avg≥0.64 · 仅沪深主板(60/00)
节奏: 周五收盘后运行 -> 输出下周一开盘买入清单 -> 周五收盘卖出
用法: python select_weekly.py
产出: output/周频选股_YYYYMMDD.md
"""
import json, os, sys, time, importlib.util
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
temp_dir = base + r'\temp'
out_dir = base + r'\output'
os.makedirs(out_dir, exist_ok=True)

spec = importlib.util.spec_from_file_location('asd', temp_dir + r'\a_stock_data.py')
asd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asd)

TODAY = datetime.now()
TODAY_STR = TODAY.strftime('%Y-%m-%d')
WEEK_PATH = temp_dir + r'\week_kline_long.json'

# ---------------- 1. 周K增量刷新 ----------------
def norm_code(code):
    return ('sh' if code.startswith('6') else 'sz') + code

def fetch(code):
    try:
        old = results.get(code, [])
        if old:
            last_date = old[-1]['date']
            start = (datetime.strptime(last_date, '%Y-%m-%d') - timedelta(days=14)).strftime('%Y-%m-%d')
            bars = asd.tencent_kline(norm_code(code), period='week', start=start, end=TODAY_STR)
            if hasattr(bars, 'to_dict'):
                bars = bars.to_dict('records')
            dmap = {b['date']: b for b in old}
            for b in bars:
                dmap[b['date']] = b
            merged = [dmap[k] for k in sorted(dmap)]
            return code, merged
        else:
            bars = asd.tencent_kline(norm_code(code), period='week', start='2022-01-01', end=TODAY_STR)
            if hasattr(bars, 'to_dict'):
                bars = bars.to_dict('records')
            return code, list(bars)
    except Exception:
        return code, results.get(code, [])

with open(temp_dir + r'\kline_cache_em.json', 'r', encoding='utf-8') as f:
    em_cache = json.load(f)
codes = list(em_cache.keys())  # 1650 只主板

results = {}
if os.path.exists(WEEK_PATH):
    with open(WEEK_PATH, 'r', encoding='utf-8') as f:
        results = json.load(f)

t0 = time.time()
done = 0
with ThreadPoolExecutor(max_workers=16) as ex:
    futs = {ex.submit(fetch, c): c for c in codes}
    for fut in as_completed(futs):
        code, bars = fut.result()
        results[code] = bars
        done += 1
print(f'[数据] 刷新完成 {done} 只, 耗时 {time.time()-t0:.1f}s', flush=True)
with open(WEEK_PATH, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False)

# ---------------- 2. 因子计算（与回测完全一致） ----------------
all_bars = []
for code, bars in results.items():
    for b in bars:
        b['code'] = code
        all_bars.append(b)
df = pd.DataFrame(all_bars)
df['date'] = pd.to_datetime(df['date'])
df = df[df['close'].notna()]
df = df.sort_values(['code', 'date']).reset_index(drop=True)

g = df.groupby('code')
df['prev_close'] = g['close'].shift(1)
df['prev_vol'] = g['volume'].shift(1)
df['pct'] = df['close'] / df['prev_close'] - 1
df['gap'] = df['open'] / df['prev_close'] - 1
df['tail'] = df['close'] / df['open'] - 1
df['vol_chg'] = df['volume'] / df['prev_vol']

cond_shrink = (df['pct'] > 0) & (df['vol_chg'] < 1)
df['shrink_up'] = cond_shrink.groupby(df['code']).transform(lambda x: x.rolling(10).mean())
df['amount_20d'] = g['volume'].transform(lambda x: x.rolling(20).mean())
df['max_up_20d'] = g['pct'].transform(lambda x: x.rolling(20).max())
cond_expand = (df['pct'] < 0) & (df['vol_chg'] > 1.2)
df['expand_down'] = cond_expand.groupby(df['code']).transform(lambda x: x.rolling(10).mean())
df['tail_return'] = g['tail'].transform(lambda x: x.rolling(20).mean())
df['vol_chg_std'] = g['vol_chg'].transform(lambda x: x.rolling(20).std())
df['overnight_gap'] = g['gap'].transform(lambda x: x.rolling(20).mean())

df['yw'] = df['date'].dt.strftime('%Y-%U')
factor_cols = ['shrink_up', 'amount_20d', 'max_up_20d', 'expand_down', 'tail_return', 'vol_chg_std', 'overnight_gap']
sel_df = df[df[factor_cols].notna().all(axis=1)].copy()

def rank_std(s):
    s = s.fillna(s.median())
    r = s.rank(pct=True)
    return (r - 0.5) * 2

week_list = df.groupby('yw')['date'].max().sort_values().index.tolist()
yw_to_next = {w: week_list[i + 1] for i, w in enumerate(week_list[:-1])}
sel_df['buy_yw'] = sel_df['yw'].map(yw_to_next)
buy_df = df[['code', 'yw', 'open']].rename(columns={'open': 'buy_open', 'yw': 'buy_yw'})
sel = sel_df.merge(buy_df, on=['code', 'buy_yw'], how='left')
sel = sel[['yw', 'buy_yw', 'code', 'close', 'buy_open'] + factor_cols].dropna(subset=['buy_open']).copy()
for c in factor_cols:
    sel[c] = rank_std(sel.groupby('yw')[c].transform(lambda x: x))
sel['score'] = (
    + sel['shrink_up'] - sel['amount_20d'] - sel['max_up_20d'] + sel['expand_down']
    - sel['tail_return'] - sel['vol_chg_std'] - sel['overnight_gap']
) / 7

# ---------------- 3. 最新截面判定 ----------------
last_yw = week_list[-1]
yw_now = TODAY.strftime('%Y-%U')
# 本周是否已完整（周五收盘后视为完整；weekday: Mon=0..Fri=4）
complete_this_week = (last_yw == yw_now) and (TODAY.weekday() >= 4)
if last_yw == yw_now and not complete_this_week:
    # 最后一根是进行中的本周 -> 信号截面取上一完整周
    signal_yw = week_list[-2]
    buy_yw = last_yw
    buy_window_passed = True   # 该截面买入周=本周, 周一可能已过
else:
    signal_yw = last_yw
    # 构造下周号: 取信号周内最后一天 +7 天
    sig_end = df[df['yw'] == signal_yw]['date'].max()
    buy_yw = (sig_end + timedelta(days=7)).strftime('%Y-%U')
    buy_window_passed = False

# ---------------- 4. 输出 Top5 候选 + 评分强度过滤 ----------------
sub = sel[sel['yw'] == signal_yw].sort_values('score', ascending=False).head(8)
picks = sub.head(5)
avg_score = picks['score'].mean()
SKIP_AVG = 0.64   # 选股强度阈值: 好周入选股平均分显著更高(回测Cohen d=0.45, 2026-10-27)
skip_week = avg_score < SKIP_AVG
sig_end = df[df['yw'] == signal_yw]['date'].max().date()
buy_monday = sig_end + timedelta(days=3)          # 周五后首个周一
sell_friday = buy_monday + timedelta(days=4)      # 买入周周五

lines = []
lines.append(f'# 周频选股提醒（v9七因子 · Top5 · 止损12% · 评分过滤avg≥{SKIP_AVG}）')
lines.append('')
lines.append(f'- 生成时间: {TODAY_STR} {TODAY.strftime("%H:%M")}')
lines.append(f'- 信号截面: {signal_yw}（截至 {sig_end} 周）')
lines.append(f'- 本批Top5平均分: {avg_score:.3f}（阈值 {SKIP_AVG}）')
lines.append(f'- 买入窗口: {buy_monday}（周一开盘）→ 卖出: {sell_friday}（周五收盘）')
if skip_week:
    lines.append(f'- ⚠️ 评分强度不足（{avg_score:.3f} < {SKIP_AVG}），本周空仓观望，不买入')
elif buy_window_passed:
    lines.append(f'- ⚠️ 提示: 本批买入窗口（{buy_monday}）已错过，请以本周五收盘后生成的新信号为准')
else:
    lines.append('- 操作: 周一开盘价买入，周五收盘价卖出；盘中跌破买入价-12% 次日/当日止损离场')
lines.append('')
lines.append('| 代码 | score | 参考买入价(周五收盘) | 止损价(-12%) |')
lines.append('|------|-------|---------------------|-------------|')
for r in picks.itertuples():
    ref_price = r.close
    sl_price = ref_price * 0.88
    lines.append(f'| {r.code} | {r.score:.3f} | {ref_price:.2f} | {sl_price:.2f} |')
lines.append('')
lines.append('备用(6-8名): ' + ', '.join(f'{r.code}({r.score:.3f})' for r in sub.iloc[5:8].itertuples()))
lines.append('')
lines.append('## 策略参数')
lines.append('- 选股: 周五截面七因子等权打分 Top5；仅沪深主板(60/00)')
lines.append('- 强度过滤: Top5平均分 ≥ 0.64 才买入，否则当周空仓（回测累计+215.9%→+256.3%，2026弱市+27.8%）')
lines.append('- 买入: 下周一开盘价；卖出: 下周五收盘价')
lines.append('- 风控: 单票周内最低价 ≤ 买入价×0.88 → 按-12%止损')
lines.append('- 成本: 单边 0.25% 计入；回测年化 ~30%（2022-2026, 回撤-24.9%）')
lines.append('- 注意: 参考买入价为信号周收盘价，实际以周一开盘价成交')

report = '\n'.join(lines)
out_path = out_dir + f'\\周频选股_{TODAY_STR}.md'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(report)

print()
print(report)
print()
print('[产出]', out_path)
