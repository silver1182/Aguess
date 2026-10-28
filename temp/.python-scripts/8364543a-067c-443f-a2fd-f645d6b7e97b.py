
import thsdk
from datetime import datetime
from zoneinfo import ZoneInfo
import json

tz = ZoneInfo('Asia/Shanghai')
thsdk.auth()

for code, label in [("USHJ515080","中证红利ETF招商"), ("USHJ515890","红利ETF博时")]:
    try:
        df = thsdk.klines(code, start_time=datetime(2025,12,1,tzinfo=tz),
                          end_time=datetime(2026,10,23,tzinfo=tz), interval='day')
        if df is None or df.empty:
            print(f"[{label}] NO DATA")
            continue
        df = df[['close']].copy()
        df['d'] = df.index.date
        df = df.reset_index(drop=True)
        last = df.iloc[-1]
        def ret_since(sd):
            s = datetime(sd.year,sd.month,sd.day).date()
            idx = df.index[df['d'] >= s]
            if len(idx)==0: return None
            i = idx[0]; bi = i-1 if i>0 else i
            return float(last['close'])/float(df.iloc[bi]['close'])-1.0
        print(json.dumps({
            "指数": label, "代码": code, "点位": round(float(last['close']),2), "日期": str(last['d']),
            "近1月%": round((ret_since(datetime(2026,9,23)) or 0)*100,2),
            "近3月%": round((ret_since(datetime(2026,7,23)) or 0)*100,2),
            "7月初以来%": round((ret_since(datetime(2026,7,1)) or 0)*100,2),
            "2026至今%": round((ret_since(datetime(2026,1,1)) or 0)*100,2),
        }, ensure_ascii=False))
        break
    except Exception as e:
        print(f"[{label}] ERR: {repr(e)}")
