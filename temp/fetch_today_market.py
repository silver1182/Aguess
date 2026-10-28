# -*- coding: utf-8 -*-
"""今日A股实时市场概况 2026-10-27"""
import json, time
from thsdk import THS

OUT = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\today_market_20261027.json'

result = {}
with THS() as ths:
    # 1. 主要指数
    idx_codes = {
        '上证指数': 'USHI000001', '深证成指': 'USZI399001', '创业板指': 'USZI399006',
        '科创50': 'USHI000688', '沪深300': 'USHI000300', '中证500': 'USHI000905',
        '上证50': 'USHI000016',
    }
    # 中证A500 解析
    try:
        resp = ths.search_symbols('中证A500')
        a500 = [s for s in resp.data if s.get('Name') == '中证A500' or '中证A500' in s.get('Name', '')]
        if a500:
            idx_codes['中证A500'] = a500[0]['THSCODE']
    except Exception as e:
        print('A500 search err:', e)

    idx_rows = []
    for name, code in idx_codes.items():
        try:
            resp = ths.market_data_index(code)
            if resp and not resp.df.empty:
                row = resp.df.iloc[0]
                idx_rows.append({'指数': name, '点位': round(float(row['价格']), 2),
                                 '涨幅%': round(float(row['涨幅']), 2),
                                 '涨跌': round(float(row['涨跌']), 2),
                                 '成交额(亿)': round(float(row['总金额']) / 1e8, 1) if row.get('总金额') else None})
            else:
                idx_rows.append({'指数': name, 'error': str(resp.error) if resp else 'empty'})
        except Exception as e:
            idx_rows.append({'指数': name, 'error': str(e)})
        time.sleep(0.3)
    result['index'] = idx_rows

    # 2. 行业板块排名
    ind_rows = []
    try:
        resp = ths.ths_industry()
        sectors = resp.data
        for s in sectors[:90]:
            code = s['代码']
            name = s['名称']
            try:
                br = ths.market_data_block(code, '基础数据')
                if br and not br.df.empty:
                    r = br.df.iloc[0]
                    ind_rows.append({'板块': name, '涨幅%': round(float(r['涨幅']), 2),
                                     '上涨家数': int(r['上涨家数']), '下跌家数': int(r['下跌家数']),
                                     '领涨股': r.get('领涨股', '')})
            except Exception:
                pass
            time.sleep(0.15)
    except Exception as e:
        print('industry err:', e)
    ind_rows.sort(key=lambda x: x.get('涨幅%', -99), reverse=True)
    result['industry'] = ind_rows

    # 3. 涨跌家数（问财）
    try:
        resp = ths.wencai_nlp('今日沪深京A股上涨家数，下跌家数，平盘家数')
        result['advance_decline'] = resp.df.to_dict('records')[:5] if resp and not resp.df.empty else []
    except Exception as e:
        result['advance_decline_err'] = str(e)

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print('saved', OUT)
print(json.dumps({'index_top': result['index'][:9]}, ensure_ascii=False, indent=1)[:2000])
