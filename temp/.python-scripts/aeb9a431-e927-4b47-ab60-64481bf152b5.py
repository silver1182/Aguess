
import thsdk
from datetime import datetime
from zoneinfo import ZoneInfo
import json

tz = ZoneInfo('Asia/Shanghai')
thsdk.auth()

# 用 get_price 或更短窗口重试中证红利
try:
    p = thsdk.get_price("UZZI000922", start_date=datetime(2026,6,1,tzinfo=tz),
                        end_date=datetime(2026,10,23,tzinfo=tz), frequency='daily')
    print("get_price cols:", list(p.columns))
    print(p.tail(3).to_string())
    if 'close' in p.columns:
        df = p[['close']].copy()
        df['d'] = df.index.date if hasattr(df.index,'date') else df.index
        df = df.reset_index(drop=True)
        last = df.iloc[-1]
        def ret_since(sd):
            s = datetime(sd.year,sd.month,sd.day).date()
            idx = df.index[df['d'] >= s]
            if len(idx)==0: return None
            i = idx[0]; bi = i-1 if i>0 else i
            return float(last['close'])/float(df.iloc[bi]['close'])-1.0
        print(json.dumps({
            "指数": "中证红利", "点位": round(float(last['close']),2), "日期": str(last['d']),
            "近1月%": round((ret_since(datetime(2026,9,23)) or 0)*100,2),
            "近3月%": round((ret_since(datetime(2026,7,23)) or 0)*100,2),
            "7月初以来%": round((ret_since(datetime(2026,7,1)) or 0)*100,2),
        }, ensure_ascii=False))
except Exception as e:
    print("get_price err:", repr(e))

# 再试一次短窗 klines
try:
    df = thsdk.klines("UZZI000922", start_time=datetime(2026,9,1,tzinfo=tz),
                      end_time=datetime(2026,10,23,tzinfo=tz), interval='day')
    if df is not None and not df.empty:
        print("SHORT KLINE OK", df.tail(2).to_string())
    else:
        print("SHORT KLINE EMPTY")
except Exception as e:
    print("short klines err:", repr(e))
