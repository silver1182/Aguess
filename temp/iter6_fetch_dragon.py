# -*- coding: utf-8 -*-
"""
迭代2资金流: 全量采集东财龙虎榜 2022-01 ~ 2026-10 (iter6_fetch_dragon.py)
========================================================================
按交易日遍历 RPT_DAILYBILLBOARD_DETAILSNEW, 保留沪深主板(60/00)记录,
输出 temp\dragon_hist.json: {"YYYY-MM-DD": {code: {...}}}
断点续传: 已完成的交易日写入 progress 文件, 重启自动跳过。
"""
import json, time, requests, urllib3, sys, os
urllib3.disable_warnings()

BASE = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
TEMP = BASE + r'\temp'
DST = TEMP + r'\dragon_hist.json'
PROG = TEMP + r'\dragon_progress.txt'
FIELDS = ['TRADE_DATE', 'SECURITY_CODE', 'SECURITY_NAME_ABBR', 'CLOSE_PRICE', 'CHANGE_RATE',
          'BILLBOARD_NET_AMT', 'BILLBOARD_BUY_AMT', 'BILLBOARD_SELL_AMT', 'DEAL_AMOUNT_RATIO',
          'CHANGE_TYPE', 'EXPLANATION']

sess = requests.Session()
sess.verify = False
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                     'Referer': 'https://data.eastmoney.com/'})


def fetch_day(date):
    """返回该交易日主板龙虎榜记录列表"""
    rows = []
    page = 1
    while True:
        r = sess.get('https://datacenter-web.eastmoney.com/api/data/v1/get',
                     params={'reportName': 'RPT_DAILYBILLBOARD_DETAILSNEW', 'columns': 'ALL',
                             'filter': f"(TRADE_DATE='{date}')", 'pageNumber': page, 'pageSize': 2000,
                             'sortColumns': 'TRADE_DATE', 'sortTypes': '-1'}, timeout=20)
        j = r.json()
        res = j.get('result')
        if not res:
            break
        data = res.get('data') or []
        if not data:
            break
        for row in data:
            code = str(row.get('SECURITY_CODE', ''))
            if code.startswith(('60', '00')) and not code.startswith(('30', '68')):
                rows.append({f: row.get(f) for f in FIELDS})
        total = res.get('count') or 0
        if page * 2000 >= total or len(data) < 2000:
            break
        page += 1
        time.sleep(0.1)
    return rows


def main():
    # 交易日列表: 从 v2 缓存取
    with open(TEMP + r'\kline_day_long_v2.json', encoding='utf-8') as f:
        data = json.load(f)
    # 取一只股票的全部日期近似交易日(用002438, 它覆盖全期)
    dates = [b['date'] for b in data.get('002438') or data[list(data.keys())[0]]]
    dates = sorted(set(dates))
    dates = [d for d in dates if d >= '2022-01-01']
    print('交易日数:', len(dates))

    hist = {}
    if os.path.exists(DST):
        hist = json.load(open(DST, encoding='utf-8'))
    done = set(hist.keys())
    fail = []
    t0 = time.time()
    for i, d in enumerate(dates):
        if d in done:
            continue
        try:
            rows = fetch_day(d)
            if rows:
                hist[d] = {r['SECURITY_CODE']: r for r in rows}
            else:
                hist[d] = {}
            done.add(d)
        except Exception as e:
            fail.append((d, str(e)[:50]))
        if (i + 1) % 100 == 0:
            print(f'进度 {i+1}/{len(dates)} 完成{len(done)} 失败{len(fail)} 耗时{time.time()-t0:.0f}s', flush=True)
            with open(DST, 'w', encoding='utf-8') as f:
                json.dump(hist, f, ensure_ascii=False)
            with open(PROG, 'a', encoding='utf-8') as f:
                f.write(f'{i+1} done={len(done)} fail={len(fail)}\n')
        time.sleep(0.12)

    with open(DST, 'w', encoding='utf-8') as f:
        json.dump(hist, f, ensure_ascii=False)
    print(f'完成: 交易日{len(dates)} 覆盖{len(done)} 失败{len(fail)} 示例{fail[:5]}')
    print('输出:', DST)


if __name__ == '__main__':
    main()
