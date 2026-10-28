import importlib.util, warnings, time
import pandas as pd, numpy as np
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# 交易日判断
import datetime
today = datetime.date(2026,10,26)
print('今日:', today, '星期', today.weekday()+1, '-> 交易日:', today.weekday()<5)

# 1. 热点股池
ths = m.ths_hot_reason()
print('\n热点股池:', len(ths), '只')

# 2. 行业资金流
bf = m.board_fund_flow(board_type='industry', period='today', top_n=8)
rows = bf.get('rows', [])
funds = [(r['name'], r.get('fund_net_inflow') or r.get('net_inflow') or '', r.get('leader','')) for r in rows]
print('行业资金流 top:', funds[:5])