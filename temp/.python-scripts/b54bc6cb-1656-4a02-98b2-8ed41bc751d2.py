import time
from thsdk import THS
with THS() as ths:
    for name, code in [('上证指数','USHI000001'), ('深证成指','USZI399001'), ('创业板指','USZI399006'), ('沪深300','USHI000300')]:
        try:
            resp = ths.market_data_index(code)
            if resp and not resp.df.empty:
                row = resp.df.iloc[0]
                print(name, '点位', round(float(row['价格']),2), '涨幅%', round(float(row['涨幅']),2))
            else:
                print(name, 'empty', resp.error if resp else None)
        except Exception as e:
            print(name, 'err', str(e)[:80])
        time.sleep(0.3)
