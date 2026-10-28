import json
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
codes = json.load(open(base + r'\temp\backtest_codes.json'))
print('总数:', len(codes))
# 按前缀分类
from collections import Counter
c = Counter(str(x)[:1] for x in codes)
print(c)
# 查看是否含 3 开头(创业板) 4/8(北交所)
import pandas as pd
df = pd.read_csv(base + r'\temp\backtest_enriched.csv')
print(df['code'].astype(str).str[:1].value_counts().to_dict())