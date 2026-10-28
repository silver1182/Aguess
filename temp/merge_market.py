# -*- coding: utf-8 -*-
"""合并: 行业板块 + 涨跌分布, 输出 today_market_20261027.json"""
import requests, time, json, sys, traceback

OUT = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\today_market_20261027.json'

def main():
    s = requests.Session(); s.trust_env = False
    HDRS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0'}

    def em_clist(fs, pz=120, fid='f3', po=1, tries=4):
        url = 'https://push2.eastmoney.com/api/qt/clist/get'
        params = {'pn': 1, 'pz': pz, 'po': po, 'np': 1, 'fltt': 2, 'invt': 2,
                  'fid': fid, 'fs': fs, 'fields': 'f2,f3,f4,f12,f14'}
        for i in range(tries):
            try:
                r = s.get(url, params=params, headers=HDRS, timeout=15)
                d = r.json(); diff = (d.get('data') or {}).get('diff') or []
                if isinstance(diff, dict):
                    diff = list(diff.values())
                return diff
            except Exception:
                time.sleep(1.0 * (i + 1))
        return None

    out = {'date': '2026-10-27'}
    ind_up = em_clist('m:90+t:2', fid='f3', po=1)
    ind_dn = em_clist('m:90+t:2', fid='f3', po=0)
    out['industry_top'] = [{'name': x['f14'], 'chg_pct': x['f3']} for x in ind_up[:8] if x.get('f3') is not None]
    out['industry_bottom'] = [{'name': x['f14'], 'chg_pct': x['f3']} for x in ind_dn[:8] if x.get('f3') is not None]
    try:
        r = s.get('https://push2ex.eastmoney.com/getTopicZDFenBu',
                  params={'ut': '7eea3edcaed734bea9cbfc24409ed989', 'dpt': 'wz.ztzt'},
                  headers=HDRS, timeout=15)
        fb = r.json()['data']['fenbu']
        up = dn = flat = 0
        for item in fb:
            for k, v in item.items():
                k = int(k)
                if k == 0:
                    flat += v
                elif k > 0:
                    up += v
                else:
                    dn += v
        lu = sum(item.get('10', 0) + item.get('11', 0) for item in fb)
        ld = sum(item.get('-10', 0) + item.get('-11', 0) for item in fb)
        out['breadth'] = {'up': up, 'down': dn, 'flat': flat, 'total': up + dn + flat,
                          'limit_up_approx': lu, 'limit_down_approx': ld}
    except Exception as e:
        out['breadth_err'] = str(e)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return json.dumps(out, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    try:
        print(main())
    except Exception:
        err = traceback.format_exc()
        with open(r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\err_today.log', 'w', encoding='utf-8') as f:
            f.write(err)
        print('ERROR_WRITTEN')
