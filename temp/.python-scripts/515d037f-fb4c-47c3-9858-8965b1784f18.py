import sys, json, time, requests, datetime as dt
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
sys.path.insert(0, base + r'\temp')
import a_stock_data as a

# 已有旧池合并
old = json.load(open(base + r'\temp\limitup_pools.json'))
all_pools = dict(old['pools'])

# 拉取 2026-07-01 ~ 2026-10-23 每个工作日
start = dt.date(2026,7,1); end = dt.date(2026,10,23)
d = start
new_dates = []
while d <= end:
    if d.weekday() < 5:
        ds = d.strftime('%Y%m%d')
        try:
            pool = a.ths_limit_up_pool(ds)
        except Exception as e:
            pool = []
            print('ERR', ds, e)
        if pool:
            all_pools[ds] = pool
            new_dates.append(ds)
        time.sleep(0.35)
    d += dt.timedelta(days=1)

dates = sorted(all_pools.keys())
print('交易日池:', len(dates), '首尾:', dates[0], dates[-1])
total = sum(len(v) for v in all_pools.values())
print('总涨停记录:', total)
json.dump({'dates': dates, 'pools': all_pools}, open(base + r'\temp\limitup_pools_ext.json','w',encoding='utf-8'), ensure_ascii=False)
print('saved')