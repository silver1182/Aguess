
import thsdk
thsdk.auth()

for market in ["USHA", "USZA"]:
    try:
        df = thsdk.list_market_securities(market=market, sort_begin=0, sort_count=20, sort_id="近3月涨幅", sort_order="desc", func_period="近3月")
        print(f"=== {market} 近3月涨幅榜 ===")
        print("cols:", list(df.columns))
        print(df.head(20).to_string())
        print()
    except Exception as e:
        print(f"{market} ERR:", repr(e))
