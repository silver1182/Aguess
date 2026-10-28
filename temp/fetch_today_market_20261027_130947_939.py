# -*- coding: utf-8 -*-
"""今日A股实时市场概况 2026-10-27: 指数行情 + 行业板块强弱 + 全市场涨跌家数"""
import json, time, requests, thsdk

OUT = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\today_market_20261027.json'

result = {"date": "2026-10-27"}

# ---------- 1) 主要指数行情 (thsdk) ----------
thsdk.auth()
index_names = ["上证指数", "深证成指", "创业板指", "沪深300", "中证500", "中证1000", "科创50", "北证50"]
index_rows = {}
for nm in index_names:
    try:
        df = thsdk.search_symbols(nm)
        # 优先取指数类型: 名称完全匹配且 market 为指数市场(USHI/USZI 等)
        cand = df[df["name"] == nm]
        if cand.empty:
            cand = df
        code = None
        for _, row in cand.iterrows():
            mkt = str(row["market"])
            if mkt.startswith("USHI") or mkt.startswith("USZI") or mkt.startswith("USZH"):
                code = row["full_code"]
                break
        if not code:
            code = cand.iloc[0]["full_code"]
        k = thsdk.get_price(code, frequency="daily", count=2)
        last = k.iloc[-1]
        prev = k.iloc[-2]
        chg_pct = (last["close"] / prev["close"] - 1) * 100
        index_rows[nm] = {
            "code": str(code),
            "close": round(float(last["close"]), 2),
            "chg_pct": round(float(chg_pct), 2),
            "open": round(float(last["open"]), 2),
            "high": round(float(last["high"]), 2),
            "low": round(float(last["low"]), 2),
            "amount_yi": round(float(last["turnover"]) / 1e8, 1),
        }
    except Exception as e:
        index_rows[nm] = {"error": str(e)}
    time.sleep(0.2)
result["indexes"] = index_rows

# ---------- 2) 东财行业板块涨跌幅排名 ----------
s = requests.Session()
s.trust_env = False
HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def em_clist(fs, pz=100, fid="f3", po=1):
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {"pn": 1, "pz": pz, "po": po, "np": 1, "fltt": 2, "invt": 2,
              "fid": fid, "fs": fs, "fields": "f2,f3,f4,f12,f14"}
    r = s.get(url, params=params, headers=HDRS, timeout=15)
    d = r.json()
    diff = (d.get("data") or {}).get("diff") or []
    if isinstance(diff, dict):
        diff = list(diff.values())
    return diff

try:
    ind_up = em_clist("m:90+t:2", pz=120, fid="f3", po=1)   # 行业涨幅榜
    ind_dn = em_clist("m:90+t:2", pz=120, fid="f3", po=0)   # 行业跌幅榜
    result["industry_top"] = [{"name": x["f14"], "chg_pct": x["f3"], "price": x["f2"]}
                              for x in ind_up[:8] if x.get("f3") is not None]
    result["industry_bottom"] = [{"name": x["f14"], "chg_pct": x["f3"], "price": x["f2"]}
                                 for x in ind_dn[:8] if x.get("f3") is not None]
except Exception as e:
    result["industry_err"] = str(e)

# ---------- 3) 全市场涨跌家数 ----------
try:
    all_a = em_clist("m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81", pz=7000, fid="f12", po=1)
    up = dn = flat = paused = 0
    for x in all_a:
        f3 = x.get("f3")
        if f3 is None or f3 == "-":
            paused += 1
        elif f3 > 0:
            up += 1
        elif f3 < 0:
            dn += 1
        else:
            flat += 1
    result["breadth"] = {"up": up, "down": dn, "flat": flat, "paused": paused,
                         "total": len(all_a)}
    # 涨停/跌停(±9.9% 近似) 主板口径
    limit_up = sum(1 for x in all_a if isinstance(x.get("f3"), (int, float)) and x["f3"] >= 9.9)
    limit_down = sum(1 for x in all_a if isinstance(x.get("f3"), (int, float)) and x["f3"] <= -9.9)
    result["breadth"]["limit_up_approx"] = limit_up
    result["breadth"]["limit_down_approx"] = limit_down
except Exception as e:
    result["breadth_err"] = str(e)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(json.dumps(result, ensure_ascii=False, indent=2))
