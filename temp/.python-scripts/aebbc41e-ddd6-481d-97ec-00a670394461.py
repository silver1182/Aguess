import importlib.util, warnings, time
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# 拉核心指数与ETF近80日日K
targets = {
    '上证指数': ('sh000001', 'idx'),
    '沪深300': ('sh000300', 'idx'),
    '中证500': ('sh000905', 'idx'),
    '创业板指': ('sz399006', 'idx'),
    '红利ETF': ('510880', 'etf'),
    '国债ETF': ('511010', 'etf'),
    '黄金ETF': ('518880', 'etf'),
    '纳指ETF': ('513100', 'etf'),
    '标普500ETF': ('513500', 'etf'),
}
out = {}
for name, (code, typ) in targets.items():
    try:
        df = m.tencent_kline(code, period='day', count=80)
        if df is not None and len(df) > 0:
            cols = ['date','open','high','low','close','volume']
            have = [c for c in cols if c in df.columns]
            out[name] = df[have].copy()
            print(f'{name}({code}): {len(df)}行, 最新收盘 {df[have]["close"].iloc[-1]}')
        else:
            print(f'{name}({code}): 空')
    except Exception as e:
        print(f'{name}({code}) ERR: {repr(e)[:120]}')
    time.sleep(0.3)

import json, os
save = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\kline_data.json'
# 存为CSV更通用
import pandas as pd
with pd.ExcelWriter(save.replace('.json', '.xlsx')) as w:
    for name, df in out.items():
        df.to_excel(w, sheet_name=name[:28], index=False)
print('已保存:', save.replace('.json', '.xlsx'))