import json, pandas as pd

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
cache = json.load(open(base + r'\temp\kline_cache_em.json', encoding='utf-8'))
pools_data = json.load(open(base + r'\temp\limitup_pools_ext.json', encoding='utf-8'))
pools = pools_data['pools']

def norm(d):
    # 统一为 YYYY-MM-DD
    s = str(d)
    if '-' in s: return s
    return f'{s[:4]}-{s[4:6]}-{s[6:]}'

records = []
miss = 0
for d, lst in pools.items():
    nd = norm(d)
    for r in lst:
        code = str(r['code']).zfill(6)
        if not code.startswith(('60','00')):
            continue
        kl = cache.get(code)
        if not kl:
            miss += 1; continue
        for i, row in enumerate(kl):
            if row['date'] == nd:
                if i+1 < len(kl):
                    nxt = kl[i+1]
                    rec = {
                        'date': nd, 'code': code, 'name': r['name'], 'pct': r['pct'],
                        'board_type': r['board_type'], 'high_days': r['high_days'],
                        'seal_rate': r['seal_rate'], 'break_times': r['break_times'],
                        'first_time': r['first_time'], 'is_again': r['is_again'],
                        'reason': r['reason'],
                        'close_t': row['close'],
                        'ret_open': (nxt['open']/row['close'] - 1)*100,
                        'ret_close': (nxt['close']/row['close'] - 1)*100,
                        'next_date': nxt['date'],
                    }
                    records.append(rec)
                break

df = pd.DataFrame(records)
print('样本数:', len(df))
print('日期范围:', df['date'].min(), '~', df['date'].max())
print('交易日数:', df['date'].nunique())
df.to_csv(base + r'\temp\backtest_long.csv', index=False)
print('saved')