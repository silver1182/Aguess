import requests, urllib3, json
urllib3.disable_warnings()
sess = requests.Session()
sess.verify = False
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Referer': 'https://data.eastmoney.com/'})

def probe(name, url, params, expect_keys=None):
    try:
        r = sess.get(url, params=params, timeout=15)
        st = r.status_code
        if st != 200:
            print(f'{name}: HTTP {st}')
            return None
        try:
            j = r.json()
        except Exception:
            print(f'{name}: 非JSON, len={len(r.text)} 前80={r.text[:80]!r}')
            return None
        if j.get('result') is None:
            print(f'{name}: result=None msg={j.get("message")} code={j.get("code")}')
            return None
        rows = j['result'].get('data') or []
        print(f'{name}: OK rows={len(rows)} 键={list(rows[0].keys())[:10] if rows else []}')
        if rows:
            print(f'  示例: {json.dumps(rows[0], ensure_ascii=False)[:220]}')
        return rows
    except Exception as e:
        print(f'{name}: ERR {str(e)[:100]}')
        return None

# 龙虎榜: 不带filter, 看最近
probe('龙虎榜-近期', 'https://datacenter-web.eastmoney.com/api/data/v1/get',
      {'reportName': 'RPT_DAILYBILLBOARD_DETAILSNEW', 'columns': 'ALL',
       'pageNumber': 1, 'pageSize': 3, 'sortColumns': 'TRADE_DATE', 'sortTypes': '-1'})
# 龙虎榜: 试历史日期2024-02
probe('龙虎榜-20240205', 'https://datacenter-web.eastmoney.com/api/data/v1/get',
      {'reportName': 'RPT_DAILYBILLBOARD_DETAILSNEW', 'columns': 'ALL',
       'filter': "(TRADE_DATE='2024-02-05')", 'pageNumber': 1, 'pageSize': 3, 'sortColumns': 'TRADE_DATE', 'sortTypes': '-1'})
# 两融: 换报表名
probe('两融-RPTA_RZRQ_GGDATA', 'https://datacenter-web.eastmoney.com/api/data/v1/get',
      {'reportName': 'RPTA_RZRQ_GGDATA', 'columns': 'ALL',
       'filter': "(TRADE_DATE='2024-02-05')", 'pageNumber': 1, 'pageSize': 3})
probe('两融-RPT_RZRQ_GGDATA', 'https://datacenter-web.eastmoney.com/api/data/v1/get',
      {'reportName': 'RPT_RZRQ_GGDATA', 'columns': 'ALL',
       'filter': "(TRADE_DATE='2024-02-05')", 'pageNumber': 1, 'pageSize': 3})
# 北向: 换报表名
probe('北向-RPT_MUTUAL_HOLDSTOCKNORTH_STA', 'https://datacenter-web.eastmoney.com/api/data/v1/get',
      {'reportName': 'RPT_MUTUAL_HOLDSTOCKNORTH_STA', 'columns': 'ALL',
       'filter': "(TRADE_DATE='2024-02-05')", 'pageNumber': 1, 'pageSize': 3})
