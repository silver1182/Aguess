import json, pandas as pd

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
df = pd.read_csv(base + r'\temp\backtest_raw.csv')

with open(base + r'\temp\limitup_pools.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
pools = data['pools']

# 构建 code-date 索引补充字段
extra = []
for d, lst in pools.items():
    for r in lst:
        extra.append({
            'date': d, 'code': int(r['code']),
            'seal_rate': r.get('seal_rate'), 'break_times': r.get('break_times'),
            'seal_amount': r.get('seal_amount'), 'first_time': r.get('first_time'),
            'is_again': r.get('is_again'), 'reason': r.get('reason'),
        })
ex = pd.DataFrame(extra)
df = df.merge(ex, on=['date','code'], how='left')
print(df.shape)
print(df[['seal_rate','break_times','first_time','is_again']].describe(include='all'))
print(df['first_time'].notna().sum(), '有封板时间')

# 封板时间转分钟（从开盘 9:30 起算）
def t2min(t):
    try:
        h, m, s = map(int, str(t).split(':'))
        return (h*60+m) - 570  # 9:30=570
    except Exception:
        return None
df['seal_min'] = df['first_time'].apply(t2min)
# 尾盘定义：14:00后封板（min>=270），早盘：11:30前（<=120），午盘：中间
print(df['seal_min'].describe())
df.to_csv(base + r'\temp\backtest_enriched.csv', index=False)
print('saved')