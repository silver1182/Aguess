
import thsdk
thsdk.auth()

# 近3月涨幅榜
try:
    df = thsdk.query_wencai(query="近3个月涨幅最大的股票 前20", limit=20)
    print("=== 涨幅榜 ===")
    print("cols:", list(df.columns))
    print(df.head(20).to_string())
except Exception as e:
    print("涨幅榜 ERR:", repr(e))
