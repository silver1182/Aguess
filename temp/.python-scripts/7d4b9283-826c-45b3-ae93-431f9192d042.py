import pandas as pd, json
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
df = pd.read_csv(base + r'\temp\backtest_long.csv')
cache = json.load(open(base + r'\temp\kline_cache_em.json', encoding='utf-8'))
miss = df[df['rsi'].isna()]
# code 是否在缓存中？
codes = miss['code'].astype(str).str.zfill(6)
print('缺样本 code 在缓存中:', codes.isin(cache.keys()).sum(), '/', len(miss))
print('缓存中有但无date匹配样本示例:')
cnt = 0
for _, r in miss.iterrows():
    c = str(r['code']).zfill(6)
    kl = cache.get(c, [])
    dates = [x['date'] for x in kl] if kl else []
    if r['date'] not in dates and cnt < 3:
        print(r['date'], c, 'K线首末:', dates[:2], dates[-2:] if dates else 'EMPTY')
        cnt += 1