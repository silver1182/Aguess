
import thsdk
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd

tz = ZoneInfo('Asia/Shanghai')
thsdk.auth()

# 1) 探查 search_symbols 返回结构
df = thsdk.search_symbols("沪深300")
print("search_symbols cols:", list(df.columns))
print(df.head(3).to_string())

# 2) 探查 get_price 返回
try:
    p = thsdk.get_price("USHI000300", start_date=datetime(2026,9,1,tzinfo=tz), end_date=datetime(2026,10,23,tzinfo=tz), frequency='daily')
    print("get_price cols:", list(p.columns))
    print(p.tail(2).to_string())
except Exception as e:
    print("get_price err:", repr(e))

# 3) 探查 klines 创业板指返回结构
try:
    k = thsdk.klines("USZI399006", start_time=datetime(2026,9,1,tzinfo=tz), end_time=datetime(2026,10,23,tzinfo=tz), interval='day')
    print("klines cols:", list(k.columns))
    print(k.dtypes.to_string())
    print(k.tail(2).to_string())
except Exception as e:
    print("klines err:", repr(e))
