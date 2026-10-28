
import thsdk
from datetime import datetime
from zoneinfo import ZoneInfo
import json

tz = ZoneInfo('Asia/Shanghai')
thsdk.auth()

assets = [
    ("沪深300",     "USHI1B0300", 0.20),
    ("中证A500",    "USHI1B0510", 0.15),
    ("中证500",     "USHI1B0905", 0.15),
    ("红利(ETF代理)", "USHJ515080", 0.15),
    ("国债ETF",     "USHJ511010", 0.25),
    ("黄金ETF",     "USHJ518880", 0.05),
    ("现金",        None,         0.05),
]

INVEST_DATES = [datetime(2026,7,23).date(), datetime(2026,8,23).date(), datetime(2026,9,23).date()]
NOW_DATE = datetime(2026,10,23).date()
BATCH = 10000 / 3  # 每批总投入

results = []
total_buy = 0.0
total_now = 0.0

for name, code, weight in assets:
    batch_amt = BATCH * weight
    if code is None:
        # 现金：三批各留一部分，现价不变
        results.append({"资产": name, "分批投入": [round(batch_amt,2)]*3, "买入价": ["-"]*3, "当前市值": round(batch_amt*3,2), "涨跌%": 0.0})
        total_buy += batch_amt*3; total_now += batch_amt*3
        continue
    df = thsdk.klines(code, start_time=datetime(2026,7,1,tzinfo=tz),
                      end_time=datetime(2026,10,23,tzinfo=tz), interval='day')
    df = df[['close']].copy()
    df['d'] = df.index.date
    df = df.sort_values('d').reset_index(drop=True)
    last = df.iloc[-1]
    now_price = float(last['close'])
    now_date = str(last['d'])

    shares_total = 0.0
    buy_prices = []
    for d in INVEST_DATES:
        idx = df.index[df['d'] >= d]
        i = idx[0]
        bp = float(df.iloc[i]['close'])
        buy_prices.append(round(bp,4))
        shares_total += batch_amt / bp
    now_val = shares_total * now_price
    chg = now_val / (batch_amt*3) - 1.0
    results.append({"资产": name, "分批投入": [round(batch_amt,2)]*3, "买入价": buy_prices, "当前市值": round(now_val,2), "涨跌%": round(chg*100,2)})
    total_buy += batch_amt*3; total_now += now_val

summary = {
    "总投入": round(total_buy,2),
    "当前总市值": round(total_now,2),
    "总盈亏": round(total_now-total_buy,2),
    "总收益率%": round((total_now/total_buy-1)*100,2),
}
print(json.dumps({"明细": results, "汇总": summary}, ensure_ascii=False, indent=2))
