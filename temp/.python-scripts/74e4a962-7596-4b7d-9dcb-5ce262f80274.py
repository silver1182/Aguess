import importlib.util, warnings, time, json
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# 用K线推过去一个月的交易日（用上证指数）
import pandas as pd
idx = m.tencent_kline('sh000001', period='day', count=40)
dates = sorted(idx['date'].tolist())
print('近40日K线交易日:', dates[:5], '...', dates[-5:])
print('总交易日数:', len(dates))

# 过去一个月（不含今天）：取最近22个交易日
hist_dates = dates[-23:-1]  # 排除今天10-26，保留前面22个交易日
print('\n回测区间(22个交易日):', hist_dates[0], '~', hist_dates[-1])

# 逐个拉涨停池
pools = {}
for d in hist_dates:
    ds = d.replace('-','')
    try:
        r = m.ths_limit_up_pool(ds)
        pools[d] = r
        time.sleep(0.3)
    except Exception as e:
        pools[d] = []
        print(d, 'ERR', str(e)[:80])
print('\n各日涨停数:', {k: len(v) for k,v in pools.items()})

with open(r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\limitup_pools.json','w',encoding='utf-8') as f:
    json.dump({'dates': hist_dates, 'pools': pools}, f, ensure_ascii=False)
print('\n已保存')