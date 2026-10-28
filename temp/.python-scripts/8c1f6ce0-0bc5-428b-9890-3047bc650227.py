import importlib.util, warnings, time
import pandas as pd
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ths = m.ths_hot_reason()
cands = ths[~ths['名称'].str.contains('ST', na=False)].copy()
extra = pd.DataFrame({'代码':['300031','688111','003006','601857'], '名称':['宝通科技','金山办公','百亚股份','中国石油']})
merged = pd.concat([cands[['代码','名称']], extra]).drop_duplicates('代码').reset_index(drop=True)
print('候选池数量:', len(merged))

# 拉K线，逐只拉取，观察返回结构
code = merged['代码'].iloc[0]
k = m.tencent_kline(code, period='day', count=80)
print(type(k), k.shape if hasattr(k,'shape') else k)
print(k.tail(3).to_string())