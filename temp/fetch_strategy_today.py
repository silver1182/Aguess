# -*- coding: utf-8 -*-
"""补拉: 深证综指成交额 + v9持仓Top5今日行情, 输出 strategy_today_20261027.json"""
import json, time, thsdk, traceback

OUT = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\strategy_today_20261027.json'

def get_code(name_or_code):
    try:
        df = thsdk.search_symbols(str(name_or_code))
        if df.empty:
            return None
        cand = df[df['name'] == str(name_or_code)]
        src = cand if not cand.empty else df
        for _, row in src.iterrows():
            mkt = str(row['market'])
            if mkt.startswith('USHA') or mkt.startswith('USZA') or mkt.startswith('USHI') or mkt.startswith('USZI'):
                return row['full_code']
        return src.iloc[0]['full_code']
    except Exception:
        return None

def main():
    thsdk.auth()
    out = {'date': '2026-10-27'}
    # 深证综指总成交
    try:
        code = get_code('深证综指')
        if code:
            k = thsdk.get_price(code, frequency='daily', count=1)
            out['sz_composite'] = {'code': str(code), 'close': round(float(k.iloc[-1]['close']), 2),
                                   'amount_yi': round(float(k.iloc[-1]['turnover']) / 1e8, 1)}
        else:
            out['sz_composite'] = {'error': 'code not found'}
    except Exception as e:
        out['sz_composite'] = {'error': str(e)}
    time.sleep(0.3)
    # v9 Top5 今日行情
    tops = ['605255', '603050', '603530', '002847', '000935']
    rows = []
    for c in tops:
        try:
            code = get_code(c)
            if not code:
                rows.append({'code': c, 'error': 'not found'})
                continue
            k = thsdk.get_price(code, frequency='daily', count=2)
            last = k.iloc[-1]
            prev = k.iloc[-2]
            chg_pct = (last['close'] / prev['close'] - 1) * 100
            rows.append({'code': c, 'full_code': str(code),
                         'close': round(float(last['close']), 2),
                         'chg_pct': round(float(chg_pct), 2),
                         'open': round(float(last['open']), 2),
                         'high': round(float(last['high']), 2),
                         'low': round(float(last['low']), 2),
                         'prev_close': round(float(prev['close']), 2)})
        except Exception as e:
            rows.append({'code': c, 'error': str(e)})
        time.sleep(0.3)
    out['v9_top5'] = rows
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return json.dumps(out, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    try:
        print(main())
    except Exception:
        with open(r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\err_strategy.log', 'w', encoding='utf-8') as f:
            f.write(traceback.format_exc())
        print('ERROR_WRITTEN')
