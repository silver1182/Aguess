import requests, pandas as pd, numpy as np

url = 'https://push2ex.eastmoney.com/getTopicZTPool'
params = {'ut':'7eea3edcaed734bea9cbfc24409ed989','dpt':'wz.ztzt','Pageindex':0,'pagesize':170,'sort':'fbt:asc','date':'20261026'}
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
r = requests.get(url, params=params, headers=headers, timeout=15)
pool = r.json().get('data', {}).get('pool', [])
print('涨停总数:', len(pool))
df = pd.DataFrame(pool)
for c in ['c','n','p','zdp','fbt','lbt','hy','zttj','days','fund','zbc','hs','lb']:
    if c not in df.columns: df[c] = None
df['fund'] = pd.to_numeric(df['fund'], errors='coerce')
df['zbc'] = pd.to_numeric(df['zbc'], errors='coerce')
df['seal_rate'] = df['fund'] / df['zbc'].replace(0, np.nan)
out = df[['c','n','p','zdp','fbt','lbt','hy','zttj','days','fund','seal_rate','hs']].copy()
out['fbt_min'] = out['fbt'].apply(lambda s: (int(str(s).split(':')[0])*60+int(str(s).split(':')[1])-570) if pd.notna(s) and ':' in str(s) else None)
pd.set_option('display.max_rows', None); pd.set_option('display.width', 250)
print(out.sort_values('fbt_min').to_string(index=False))
out.to_csv(r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\ztpool_20261026_v2.csv', index=False)