
from datetime import datetime
from zoneinfo import ZoneInfo
from thsdk import THS

tz = ZoneInfo('Asia/Shanghai')

# 基础指数（直接可用的 THSCODE）
base_indexes = {
    "上证指数": "USHI000001",
    "沪深300": "USHI000300",
    "中证500": "USHI000905",
    "创业板指": "USZI399006",
}

def resolve(name):
    """搜索指数代码，优先返回指数（USHI/USZI前缀）"""
    with THS() as ths:
        resp = ths.search_symbols(name)
        if not resp:
            return None
        for s in resp.data:
            code = s.get('THSCODE','')
            disp = s.get('MarketDisplay','')
            if code.startswith(('USHI','USZI')) or '指数' in disp:
                return code, s.get('Name','')
        # 兜底取第一条
        return resp.data[0].get('THSCODE'), resp.data[0].get('Name','')

extra = {}
for name in ["中证A500", "中证红利"]:
    r = resolve(name)
    if r:
        extra[name] = r[0]
        print(f"resolve {name} -> {r}")

indexes = dict(base_indexes)
indexes.update(extra)
print("FINAL:", indexes)

with THS() as ths:
    rows = []
    for name, code in indexes.items():
        resp = ths.klines(code, interval="day",
                          start_time=datetime(2025,12,1,tzinfo=tz),
                          end_time=datetime(2026,10,23,tzinfo=tz))
        if not resp or resp.df.empty:
            print(f"[{name}] NO DATA: {resp.error if resp else 'empty'}")
            continue
        df = resp.df.copy()
        # 时间列转 date
        df['d'] = df['时间'].apply(lambda x: x.date() if hasattr(x,'date') else x)
        df = df.sort_values('d').reset_index(drop=True)
        last = df.iloc[-1]
        latest_date = last['d']
        latest_close = float(last['收盘价'])

        def ret_since(start_date):
            # 找到 >= start_date 的第一行索引，期初用前一根收盘（若无则用该行）
            idx = df.index[df['d'] >= start_date]
            if len(idx) == 0:
                return None
            i = idx[0]
            base_i = i - 1 if i > 0 else i
            base = float(df.iloc[base_i]['收盘价'])
            return latest_close / base - 1.0

        r1m = ret_since(datetime(2026,9,23).date())
        r3m = ret_since(datetime(2026,7,23).date())
        r_ytd = ret_since(datetime(2026,1,1).date())
        rows.append({
            "指数": name, "最新点位": round(latest_close,2),
            "数据日期": str(latest_date),
            "近1月%": round(r1m*100,2) if r1m is not None else None,
            "近3月%": round(r3m*100,2) if r3m is not None else None,
            "2026至今%": round(r_ytd*100,2) if r_ytd is not None else None,
        })

    import json
    print(json.dumps(rows, ensure_ascii=False, indent=2))
