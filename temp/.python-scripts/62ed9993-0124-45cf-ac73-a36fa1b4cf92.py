import importlib.util, warnings, time
import pandas as pd
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# 1. 同花顺热点全量
ths = m.ths_hot_reason()
print('热点股数量:', len(ths))
print(ths.columns.tolist())
print(ths[['代码','名称']].head(50).to_string())

# 2. 行业资金流龙头
bf = m.board_fund_flow(board_type='industry', period='today', top_n=30)
rows = bf.get('rows', [])
leaders = [(r['name'], r.get('leader','')) for r in rows if r.get('leader')]
print('\n行业龙头:', leaders[:15])