
import thsdk
from datetime import datetime
from zoneinfo import ZoneInfo
import json

tz = ZoneInfo('Asia/Shanghai')
thsdk.auth()

# 按调整后配置，1万元分配到 7 类资产
assets = [
    ("沪深300",     "USHI1B0300", 0.20),
    ("中证A500",    "USHI1B0510", 0.15),
    ("中证500",     "USHI1B0905", 0.15),
    ("红利(ETF代理)", "USHJ515080", 0.15),
    ("国债ETF",     "USHJ511010", 0.25),
    ("黄金ETF",     "USHJ518880", 0.05),
    ("现金",        None,         0.05),
]

BUY_DATE = datetime(2026,7,23).date()   # 3个月前买入日
NOW_DATE = datetime(2026,10,23).date()  # 今日

results = []
total_buy = 0.0
total_now = 0.0

for name, code, weight in assets:
    buy_amt = 10000 * weight
    if code is None:  # 现金
        results.append({"资产": name, "买入金额": round(buy_amt,2), "买入价": None, "现价": None, "当前市值": round(buy_amt,2), "涨跌%": 0.0})
        total_buy += buy_amt; total_now += buy_amt
        continue
    df = thsdk.klines(code, start_time=datetime(2026,7,1,tzinfo=tz),
                      end_time=datetime(2026,10,23,tzinfo=tz), interval='day')
    df = df[['close']].copy()
    df['d'] = df.index.date
    df = df.sort_values('d').reset_index(drop=True)
    # 买入价：>= 7/23 的第一根K线收盘（7/23当天或之后最近交易日）
    idx_buy = df.index[df['d'] >= BUY_DATE]
    i_buy = idx_buy[0]
    buy_price = float(df.iloc[i_buy]['close'])
    buy_date = str(df.iloc[i_buy]['d'])
    # 现价：最后一根
    last = df.iloc[-1]
    now_price = float(last['close'])
    now_date = str(last['d'])
    shares = buy_amt / buy_price
    now_val = shares * now_price
    chg = now_val / buy_amt - 1.0
    results.append({"资产": name, "买入金额": round(buy_amt,2), "买入价": round(buy_price,4), "现价": round(now_price,4), "当前市值": round(now_val,2), "涨跌%": round(chg*100,2), "买入日": buy_date, "现价日": now_date})
    total_buy += buy_amt; total_now += now_val

summary = {
    "总投入": round(total_buy,2),
    "当前总市值": round(total_now,2),
    "总盈亏": round(total_now-total_buy,2),
    "总收益率%": round((total_now/total_buy-1)*100,2),
}
print(json.dumps({"明细": results, "汇总": summary}, ensure_ascii=False, indent=2))
