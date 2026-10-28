
import thsdk
thsdk.auth()

# 问财换简单问法测试
for q in ["近3月涨幅排名", "2026年涨幅最大的股票"]:
    try:
        df = thsdk.query_wencai(query=q, limit=10)
        print(f"=== {q} ===")
        print("cols:", list(df.columns))
        print(df.head(10).to_string() if len(df) else "EMPTY")
        print()
    except Exception as e:
        print(f"{q} ERR:", repr(e))
