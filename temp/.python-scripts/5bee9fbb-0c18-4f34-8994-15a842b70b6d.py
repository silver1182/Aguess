import requests, json, pandas as pd

# 拉今日涨停池（东方财富涨停板行情）
url = 'https://push2ex.eastmoney.com/getTopicZTPool'
params = {
    'ut': '7eea3edcaed734bea9cbfc24409ed989',
    'dpt': 'wz.ztzt',
    'Pageindex': 0,
    'pagesize': 170,
    'sort': 'fbt:asc',
    'date': '20261026',
    '_': '1779876543210',
}
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
try:
    r = requests.get(url, params=params, headers=headers, timeout=15)
    data = r.json()
    pool = data.get('data', {}).get('pool', [])
    print('拉取条数:', len(pool))
    if pool:
        df = pd.DataFrame(pool)
        cols = ['c','n','p','zdp','fbt','lbt','hy','zttj','days','fund','zbc']
        for c in cols:
            if c not in df.columns: df[c] = None
        out = df[['c','n','p','zdp','fbt','lbt','hy','zttj','days','fund','zbc']].copy()
        out['seal_rate'] = out['fund'] / (out['zbc'] if (out['zbc'] or 0)>0 else 1)
        print(out.head(60).to_string(index=False))
        out.to_csv(r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\ztpool_20261026.csv', index=False)
except Exception as e:
    print('ERR:', e)