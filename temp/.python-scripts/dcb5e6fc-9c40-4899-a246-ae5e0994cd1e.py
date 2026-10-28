import requests, urllib3, json
urllib3.disable_warnings()
sess = requests.Session()
sess.verify = False
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Referer': 'https://data.eastmoney.com/'})
r = sess.get('https://datacenter-web.eastmoney.com/api/data/v1/get',
             params={'reportName': 'RPT_DAILYBILLBOARD_DETAILSNEW', 'columns': 'ALL',
                     'filter': "(TRADE_DATE='2024-02-05')", 'pageNumber': 1, 'pageSize': 1,
                     'sortColumns': 'TRADE_DATE', 'sortTypes': '-1'}, timeout=15)
j = r.json()
row = j['result']['data'][0]
for k, v in row.items():
    print(f'{k}: {v}')
