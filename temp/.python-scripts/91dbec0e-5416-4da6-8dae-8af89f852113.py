
import thsdk
thsdk.auth()

# 尝试 sort_securities 看个股涨幅排序（func_period 近3月）
try:
    df = thsdk.sort_securities(sort_begin=0, sort_count=20, sort_id="近3月涨幅", func_period="近3月")
    print("=== sort_securities 近3月 ===")
    print("cols:", list(df.columns))
    print(df.head(20).to_string())
except Exception as e:
    print("ERR:", repr(e))
