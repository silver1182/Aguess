
import thsdk
from datetime import datetime
from zoneinfo import ZoneInfo
import json

tz = ZoneInfo('Asia/Shanghai')
thsdk.auth()

indexes = {
    "上证指数": "USHI1A0001",
    "沪深300": "USHI1B0300",
    "中证500": "USHI1B0905",
    "中证A500": "USHI1B0510",
    "中证1000": "USHI1B0852",
    "创业板指": "USZI399006",
    "中证红利": "UZZI000922",
}

rows = []
for name, code in indexes.items():
    try:
        df = thsdk.klines(code, start_time=datetime(2025,12,1,tzinfo=tz),
                          end_time=datetime(2026,10,23,tzinfo=tz), interval='day')
        if df is None or df.empty:
            print(f"[{name}] NO DATA")
            continue
        df = df[['close']].copy()
        df['d'] = df.index.date
        df = df.reset_index(drop=True)
        last = df.iloc[-1]
        latest_date = str(last['d']); latest_close = float(last['close'])

        def ret_since(start_date):
            s = datetime(start_date.year, start_date.month, start_date.day).date()
            idx = df.index[df['d'] >= s]
            if len(idx) == 0: return None
            i = idx[0]
            bi = i-1 if i>0 else i
            return latest_close / float(df.iloc[bi]['close']) - 1.0

        rows.append({
            "指数": name, "点位": round(latest_close,2), "日期": latest_date,
            "近1月%": round((ret_since(datetime(2026,9,23)) or 0)*100,2),
            "近3月%": round((ret_since(datetime(2026,7,23)) or 0)*100,2),
            "7月初以来%": round((ret_since(datetime(2026,7,1)) or 0)*100,2),
            "2026至今%": round((ret_since(datetime(2026,1,1)) or 0)*100,2),
        })
    except Exception as e:
        print(f"[{name}] ERR: {repr(e)}")

print(json.dumps(rows, ensure_ascii=False, indent=2))
