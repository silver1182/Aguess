
import thsdk
from datetime import datetime
from zoneinfo import ZoneInfo
import json

tz = ZoneInfo('Asia/Shanghai')
thsdk.auth()

names = ["贵州茅台","宁德时代","比亚迪","中际旭创","寒武纪","东方财富","招商银行","长江电力","工商银行","中国平安","立讯精密","北方华创"]

def resolve_stock(name):
    df = thsdk.search_symbols(name)
    if df is None or df.empty:
        return None
    # 选沪A/深A股票（market USHA/USZA 或 code 6位数字）
    for _, row in df.iterrows():
        m = row.get('market','')
        if m in ('USHA','USZA') or (str(row.get('code','')).isdigit() and len(str(row.get('code','')))==6):
            return row['full_code'], row['name']
    return None

results = []
for nm in names:
    r = resolve_stock(nm)
    if not r:
        print(f"[{nm}] NOT RESOLVED")
        continue
    code, disp = r
    try:
        df = thsdk.klines(code, start_time=datetime(2026,7,1,tzinfo=tz),
                          end_time=datetime(2026,10,23,tzinfo=tz), interval='day')
        df = df[['close']].copy()
        df['d'] = df.index.date
        df = df.sort_values('d').reset_index(drop=True)
        last = df.iloc[-1]
        idx = df.index[df['d'] >= datetime(2026,7,23).date()]
        i = idx[0]; bi = i-1 if i>0 else i
        base = float(df.iloc[bi]['close'])
        chg = float(last['close'])/base - 1
        results.append({"股票": disp, "代码": code, "现价": round(float(last['close']),2), "近3月%": round(chg*100,2), "日期": str(last['d'])})
    except Exception as e:
        print(f"[{nm}] ERR {repr(e)}")

results.sort(key=lambda x: x["近3月%"], reverse=True)
print(json.dumps(results, ensure_ascii=False, indent=2))
