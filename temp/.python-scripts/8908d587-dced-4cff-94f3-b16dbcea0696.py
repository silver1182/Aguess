import requests, urllib3, json
urllib3.disable_warnings()
sess = requests.Session()
sess.verify = False
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Referer': 'https://data.eastmoney.com/'})
for d in ['2022-01-04', '2022-04-27', '2022-05-06', '2023-08-01']:
    try:
        r = sess.get('https://datacenter-web.eastmoney.com/api/data/v1/get',
                     params={'reportName': 'RPT_DAILYBILLBOARD_DETAILSNEW', 'columns': 'ALL',
                             'filter': f"(TRADE_DATE='{d}')", 'pageNumber': 1, 'pageSize': 3,
                             'sortColumns': 'TRADE_DATE', 'sortTypes': '-1'}, timeout=15)
        j = r.json()
        rows = j.get('result', {}).get('data') or []
        print(d, 'rows=', len(rows), 'total=', j.get('result', {}).get('count') if j.get('result') else None)
    except Exception as e:
        print(d, 'ERR', str(e)[:80])
