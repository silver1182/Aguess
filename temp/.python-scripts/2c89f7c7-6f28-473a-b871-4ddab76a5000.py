
import thsdk
from datetime import datetime
from zoneinfo import ZoneInfo
import json

tz = ZoneInfo('Asia/Shanghai')
thsdk.auth()

for name in ["纳斯达克100", "标普500", "纳指ETF"]:
    try:
        df = thsdk.search_symbols(name)
        if df is None or df.empty:
            print(name, "EMPTY")
            continue
        print(f"=== {name} ===")
        print(df[['full_code','name','code_display','market']].head(6).to_string())
        print()
    except Exception as e:
        print(name, "ERR", repr(e))
