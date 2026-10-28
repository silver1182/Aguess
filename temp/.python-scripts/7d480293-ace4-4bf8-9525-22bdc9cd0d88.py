import requests, urllib3, json, time
urllib3.disable_warnings()
sess = requests.Session()
sess.verify = False
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Referer': 'https://data.eastmoney.com/'})

def probe(name, url, params):
    try:
        r = sess.get(url, params=params, timeout=15)
        if r.status_code == 403:
            print(f'{name}: HTTP 403')
            return None
        j = r.json()
        if j.get('result') is None:
            print(f'{name}: 无数据 result=None msg={j.get("message")}')
            return None
        rows = j['result'].get('data') or []
        print(f'{name}: OK rows={len(rows)} 首行键={list(rows[0].keys())[:8] if rows else []}')
        if rows:
            print(f'  示例: {json.dumps(rows[0], ensure_ascii=False)[:200]}')
        return rows
    except Exception as e:
        print(f'{name}: ERR {str(e)[:100]}')
        return None

# 1) 龙虎榜日榜 (最近一个交易日)
probe('龙虎榜', 'https://datacenter-web.eastmoney.com/api/data/v1/get',
      {'reportName': 'RPT_DAILYBILLBOARD_DETAILSNEW', 'columns': 'ALL',
       'filter': "(TRADE_DATE='2026-10-28')", 'pageNumber': 1, 'pageSize': 5, 'sortColumns': 'TRADE_DATE', 'sortTypes': '-1'})
# 2) 两融个股 (最新)
probe('两融个股', 'https://datacenter-web.eastmoney.com/api/data/v1/get',
      {'reportName': 'RPTA_WEB_RZRQ_GGDATA', 'columns': 'ALL',
       'filter': "(TRADE_DATE='2026-10-28')", 'pageNumber': 1, 'pageSize': 5, 'sortColumns': 'TRADE_DATE', 'sortTypes': '-1'})
# 3) 北向资金个股持股
probe('北向个股持股', 'https://datacenter-web.eastmoney.com/api/data/v1/get',
      {'reportName': 'RPT_MUTUAL_STOCK_NORTHSTA', 'columns': 'ALL',
       'filter': "(TRADE_DATE='2026-10-28')", 'pageNumber': 1, 'pageSize': 5, 'sortColumns': 'TRADE_DATE', 'sortTypes': '-1'})
