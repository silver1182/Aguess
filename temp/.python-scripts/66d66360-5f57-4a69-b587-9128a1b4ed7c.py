import importlib.util, warnings, time, json, os
import pandas as pd
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
with open(r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\backtest_codes.json','r',encoding='utf-8') as f:
    codes = json.load(f)
out_dir = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\bk_kline'
done = set(f.replace('.csv','') for f in os.listdir(out_dir) if f.endswith('.csv'))
todo = [c for c in codes if c not in done]
print('剩余待拉:', len(todo))
errs=[]; t0=time.time()
for i, code in enumerate(todo):
    try:
        k = m.tencent_kline(code, period='day', count=70)
        if k is not None and len(k)>0:
            k.to_csv(os.path.join(out_dir, f'{code}.csv'), index=False)
    except Exception as e:
        errs.append((code,str(e)[:60]))
    if (i+1)%100==0: print(f'  {i+1}/{len(todo)} 用时{time.time()-t0:.0f}s')
print('完成，错误:', len(errs), errs[:5])
print('总文件数:', len(os.listdir(out_dir)))