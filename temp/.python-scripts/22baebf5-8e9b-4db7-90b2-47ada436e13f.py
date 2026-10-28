
import thsdk
from datetime import datetime
from zoneinfo import ZoneInfo
import json

tz = ZoneInfo('Asia/Shanghai')
thsdk.auth()

# 重新解析需要的指数
for name in ["上证指数","沪深300","中证500","中证A500","中证红利","创业板指","上证50","中证1000"]:
    try:
        df = thsdk.search_symbols(name)
        hit = df[(df['market']=='USHI') | (df['market']=='USZI')]
        if len(hit):
            print(name, "->", hit[['full_code','name','code_display','market']].head(3).to_dict('records'))
        else:
            print(name, "-> NO INDEX HIT", df.head(3).to_dict('records'))
    except Exception as e:
        print(name, "ERR", repr(e))
