
import thsdk
thsdk.auth()

# 拉A股市场股票列表，看返回结构
try:
    df = thsdk.market_securities("A股", start=0, count=10)
    print("cols:", list(df.columns))
    print(df.head(5).to_string())
    print("attrs:", {k: v for k, v in df.attrs.get('thsdk', {}).items() if k == 'metadata'})
except Exception as e:
    print("ERR:", repr(e))
