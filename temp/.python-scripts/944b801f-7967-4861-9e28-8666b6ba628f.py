from thsdk import api
import time
api.auth()
for name, code in [('上证指数','USHI000001'), ('深证成指','USZI399001'), ('创业板指','USZI399006'), ('沪深300','USHI000300'), ('中证500','USHI000905')]:
    try:
        df = api.get_price(code, frequency='daily', count=7)
        if df is not None and len(df):
            print(name)
            print(df.tail(6)[['close']].to_string())
        else:
            print(name, 'empty')
    except Exception as e:
        print(name, 'err', str(e)[:80])
    time.sleep(0.3)
