from thsdk import api
api.auth()
# 确认603200名称
try:
    r = api.search_symbols('603200')
    print(r.to_string() if hasattr(r, 'to_string') else r)
except Exception as e:
    print('search err', e)
# 今日主要指数
import time
for name, code in [('上证指数','USHI000001'), ('深证成指','USZI399001'), ('创业板指','USZI399006')]:
    try:
        df = api.get_price(code, frequency='daily', count=6)
        print(name, df.tail(6)[['close']].to_dict('records'))
    except Exception as e:
        print(name, 'err', e)
    time.sleep(0.3)
