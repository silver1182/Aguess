import importlib.util, warnings, time, json, os
import pandas as pd, numpy as np
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

with open(r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\backtest_codes.json','r',encoding='utf-8') as f:
    codes = json.load(f)

# 分批拉取K线，存csv，每只存60日（覆盖回测区间+前置指标）
out_dir = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\bk_kline'
os.makedirs(out_dir, exist_ok=True)
done = set(f.replace('.csv','') for f in os.listdir(out_dir) if f.endswith('.csv'))
todo = [c for c in codes if c not in done]
print('待拉:', len(todo), '已完成:', len(done))
errs = []
t0=time.time()
for i, code in enumerate(todo[:150]):
    try:
        k = m.tencent_kline(code, period='day', count=70)
        if k is not None and len(k)>0:
            k.to_csv(os.path.join(out_dir, f'{code}.csv'), index=False)
    except Exception as e:
        errs.append((code,str(e)[:60]))
    if (i+1)%50==0: print(f'  {i+1}/150 用时{time.time()-t0:.0f}s')
print('批次完成，错误:', len(errs), errs[:5])