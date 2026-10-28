
import thsdk
from datetime import datetime
from zoneinfo import ZoneInfo
import json

tz = ZoneInfo('Asia/Shanghai')
thsdk.auth()

# 待查标的：黄金ETF、国债ETF
for name in ["黄金ETF", "国债ETF", "十年国债ETF"]:
    try:
        df = thsdk.search_symbols(name)
        hit = df[df['market'].isin(['USHJ','USHI','USZI'])]
        print(name, "->", hit[['full_code','name','code_display','market']].head(4).to_dict('records') if len(hit) else df.head(4).to_dict('records'))
    except Exception as e:
        print(name, "ERR", repr(e))
