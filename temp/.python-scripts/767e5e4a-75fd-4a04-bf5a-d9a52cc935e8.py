import json, pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

# 数据范围检查
all_bars = []
for code, bars in cache.items():
    for b in bars:
        b['code'] = code
        all_bars.append(b)
df = pd.DataFrame(all_bars)
df['date'] = pd.to_datetime(df['date'])
print('总行数:', len(df))
print('日期范围:', df['date'].min().date(), '~', df['date'].max().date())
print('股票数:', df['code'].nunique())
print('每只股票平均K线数:', len(df) / df['code'].nunique())
print('字段:', list(df.columns))
# 每只股票K线数分布
cnt = df.groupby('code').size()
print('K线数分布: min', cnt.min(), 'p25', cnt.quantile(0.25), 'median', cnt.median(), 'p75', cnt.quantile(0.75), 'max', cnt.max())
# 是否有amount
print('amount非空比例:', df['amount'].notna().mean())