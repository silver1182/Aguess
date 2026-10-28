import sys, json, time
sys.path.insert(0, r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp')
import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
TEMP = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
LONG = TEMP + r'\kline_day_long_v2.json'
t0=time.time()
data = json.load(open(LONG, encoding='utf-8'))
print('股票数', len(data), '载入秒', round(time.time()-t0,1))
# 抽样日期范围
for c in ['600519','000001','002438','001221']:
    bars = data.get(c) or []
    if bars: print(c, len(bars), bars[0]['date'], bars[-1]['date'])
    else: print(c, 'empty')
# 市况分层
import mkt_state_daily as msd
mkt_df = msd.build_index(data)
print('市况标签:', mkt_df['depth'].value_counts().to_dict())
print('日期范围', mkt_df['date'].min(), mkt_df['date'].max())
# 按年-深度
mkt_df['ym'] = mkt_df['date'].str[:4]
print(pd.crosstab(mkt_df['ym'], mkt_df['depth']).to_string())
