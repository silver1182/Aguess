
import thsdk
from datetime import datetime
from zoneinfo import ZoneInfo

tz = ZoneInfo('Asia/Shanghai')

# 认证（自动恢复已有会话/临时账户）
ok = thsdk.auth()
print("auth:", ok)

# 基础指数
base_indexes = {
    "上证指数": "USHI000001",
    "沪深300": "USHI000300",
    "中证500": "USHI000905",
    "创业板指": "USZI399006",
}

def resolve(name):
    try:
        df = thsdk.search_symbols(name)
        if df is None or df.empty:
            return None
        # 看列
        cols = list(df.columns)
        code_col = 'THSCODE' if 'THSCODE' in cols else cols[0]
        name_col = 'Name' if 'Name' in cols else (cols[1] if len(cols)>1 else None)
        for _, row in df.iterrows():
            code = str(row[code_col])
            nm = str(row[name_col]) if name_col else ''
            if code.startswith(('USHI','USZI')) or '指数' in nm:
                return code
        return str(df.iloc[0][code_col])
    except Exception as e:
        print(f"resolve {name} err: {e}")
        return None

extra = {}
for name in ["中证A500", "中证红利"]:
    c = resolve(name)
    if c:
        extra[name] = c
        print(f"resolve {name} -> {c}")

indexes = dict(base_indexes); indexes.update(extra)
print("INDEXES:", indexes)

rows = []
for name, code in indexes.items():
    try:
        df = thsdk.klines(code, start_time=datetime(2025,12,1,tzinfo=tz),
                          end_time=datetime(2026,10,23,tzinfo=tz), interval='day')
        if df is None or df.empty:
            print(f"[{name}] NO DATA")
            continue
        df = df.copy()
        # 确定时间列
        tcol = '时间' if '时间' in df.columns else df.columns[0]
        ccol = '收盘价' if '收盘价' in df.columns else ('close' if 'close' in df.columns else None)
        if ccol is None:
            print(f"[{name}] cols={list(df.columns)}")
            continue
        dcol = df[tcol].apply(lambda x: x.date() if hasattr(x,'date') else x)
        df = df.assign(d=dcol).sort_values('d').reset_index(drop=True)
        last = df.iloc[-1]
        latest_date = last['d']; latest_close = float(last[ccol])

        def ret_since(start_date):
            idx = df.index[df['d'] >= start_date]
            if len(idx) == 0: return None
            i = idx[0]
            bi = i-1 if i>0 else i
            return latest_close / float(df.iloc[bi][ccol]) - 1.0

        rows.append({
            "指数": name, "点位": round(latest_close,2), "日期": str(latest_date),
            "近1月%": round((ret_since(datetime(2026,9,23).date()) or 0)*100,2),
            "近3月%": round((ret_since(datetime(2026,7,23).date()) or 0)*100,2),
            "2026至今%": round((ret_since(datetime(2026,1,1).date()) or 0)*100,2),
        })
    except Exception as e:
        print(f"[{name}] ERR: {e}")

import json
print(json.dumps(rows, ensure_ascii=False, indent=2))
