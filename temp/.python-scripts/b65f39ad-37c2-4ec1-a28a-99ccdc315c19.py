import importlib.util, warnings, time, json
import pandas as pd
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

out = {}
# 1. 行业板块资金流 top15
try:
    bf = m.board_fund_flow(board_type='industry', period='today', top_n=15)
    rows = bf.get('rows', [])
    df = pd.DataFrame(rows)
    out['行业资金流'] = df
    print('=== 今日行业资金流 top15 ===')
    print(df.head(15).to_string())
except Exception as e:
    print('board_fund_flow ERR', repr(e)[:150])
time.sleep(0.4)

# 2. 同花顺热点
try:
    ths = m.ths_hot_reason()
    if ths is not None:
        out['同花顺热点'] = ths
        print('\n=== 同花顺热点概念(前12) ===')
        print(ths.head(12).to_string())
except Exception as e:
    print('ths_hot ERR', repr(e)[:150])
time.sleep(0.4)

# 3. 龙虎榜
try:
    dt = m.daily_dragon_tiger(min_net_buy=1e8)
    if isinstance(dt, dict):
        rows = dt.get('rows', dt.get('data', []))
        d = pd.DataFrame(rows) if rows else None
        if d is not None and len(d):
            out['龙虎榜'] = d
            print('\n=== 龙虎榜净买>1亿(前10) ===')
            print(d.head(10).to_string())
        else:
            print('\n龙虎榜: 无数据')
except Exception as e:
    print('dragon ERR', repr(e)[:150])

with pd.ExcelWriter(r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\market_pulse.xlsx') as w:
    for k, v in out.items():
        v.to_excel(w, sheet_name=k[:28], index=False)
print('\nsaved market_pulse.xlsx')