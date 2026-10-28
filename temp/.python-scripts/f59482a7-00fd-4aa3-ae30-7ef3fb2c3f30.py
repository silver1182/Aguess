import json
from collections import Counter
import pandas as pd

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
lp = json.load(open(base + r'\temp\limitup_pools_ext.json', encoding='utf-8'))
pools_raw = lp['pools']
pools = {k[:4] + '-' + k[4:6] + '-' + k[6:8]: v for k, v in pools_raw.items()}
pool_dates = sorted(pools.keys())
print('pool_dates:', pool_dates[0], pool_dates[-1], len(pool_dates))

cache = json.load(open(base + r'\temp\kline_cache_em.json', encoding='utf-8'))
all_bars = []
for code, bars in cache.items():
    for b in bars:
        b['code'] = code
        all_bars.append(b)
df = pd.DataFrame(all_bars)
df['date'] = pd.to_datetime(df['date'])
df = df[df['close'].notna()].sort_values(['code', 'date']).reset_index(drop=True)
trade_days = sorted(df['date'].unique())
td_str = [d.strftime('%Y-%m-%d') for d in trade_days]
td_index = {d: i for i, d in enumerate(td_str)}

d = pool_dates[0]
print('d in td_index:', d in td_index, '| next:', td_index.get(d))

# 检查涨停池某天的成分
def split_tags(x):
    return [t.strip() for t in str(x).split('+') if t.strip()]

noise_tags = {'中报预增', '业绩增长', '半年报增长', '半年报预增', '中报扭亏', '中报增长',
              '一季报增长', '一季报扭亏', '三季报增长', '年报增长', '年报预增', '业绩预增',
              '扭亏', '预增', '高送转', '分红', '回购', '增持', '央企', '国企改革', '上海国资',
              '深圳国资', '国资', '低价股', '次新股', '破净', 'ST', '举牌', '股权转让', '重组', '并购重组'}

lst = pools[d]
main_lst = [x for x in lst if x['code'].startswith(('60','00'))]
print('涨停数:', len(lst), '主板:', len(main_lst))
tc = {}
for x in main_lst:
    for t in split_tags(x.get('reason')):
        tc.setdefault(t, set()).add(x['code'])
tag_cnt = Counter({t: len(c) for t, c in tc.items() if t not in noise_tags})
print('非噪音标签数:', len(tag_cnt))
top3 = [t for t, _ in tag_cnt.most_common(9) if t not in noise_tags][:3]
print('top3:', top3)
cand = set()
for t in top3:
    cand |= tc.get(t, set())
print('cand:', len(cand))

# 次日开盘pct 0~6 且收盘未涨停
buy_d = td_str[td_index[d] + 1]
kmap = {}
for r in df.itertuples():
    kmap.setdefault(r.code, {})[r.date] = r
n_ok = 0
for c in list(cand)[:20]:
    b = kmap.get(c, {}).get(pd.Timestamp(buy_d))
    if b:
        n_ok += 1
print('cand中20只有次日K线:', n_ok, '/20, buy_d =', buy_d)
