
import thsdk
from datetime import datetime
from zoneinfo import ZoneInfo
import json

tz = ZoneInfo('Asia/Shanghai')
thsdk.auth()

targets = [
    ("纳指ETF国泰(513100)", "USHJ513100"),
    ("标普500ETF博时(513500)", "USHJ513500"),
]

results = []
for name, code in targets:
    try:
        df = thsdk.klines(code, start_time=datetime(2026,7,1,tzinfo=tz),
                          end_time=datetime(2026,10,23,tzinfo=tz), interval='day')
        df = df[['close']].copy()
        df['d'] = df.index.date
        df = df.sort_values('d').reset_index(drop=True)
        last = df.iloc[-1]
        # 近1月/近3月/7月初以来/2026至今
        def ret_since(sd):
            s = datetime(sd.year,sd.month,sd.day).date()
            idx = df.index[df['d'] >= s]
            if len(idx)==0: return None
            i = idx[0]; bi = i-1 if i>0 else i
            return float(last['close'])/float(df.iloc[bi]['close'])-1.0
        results.append({
            "标的": name, "现价": round(float(last['close']),3), "日期": str(last['d']),
            "近1月%": round((ret_since(datetime(2026,9,23)) or 0)*100,2),
            "近3月%": round((ret_since(datetime(2026,7,23)) or 0)*100,2),
            "7月初以来%": round((ret_since(datetime(2026,7,1)) or 0)*100,2),
            "2026至今%": round((ret_since(datetime(2026,1,1)) or 0)*100,2),
        })
    except Exception as e:
        print(f"[{name}] ERR: {repr(e)}")

print(json.dumps(results, ensure_ascii=False, indent=2))
