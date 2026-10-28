import sys, os, json
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
sys.path.insert(0, base + r'\temp')
# 先看 a_stock_data 是否有 kline 长历史接口
import importlib.util
spec = importlib.util.spec_from_file_location('asd', base + r'\temp\a_stock_data.py')
asd = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(asd)
    print('模块加载成功')
    funcs = [f for f in dir(asd) if not f.startswith('_')]
    print('函数数量:', len(funcs))
    # 找kline相关
    kline_funcs = [f for f in funcs if 'kline' in f.lower() or 'daily' in f.lower() or 'history' in f.lower()]
    print('K线相关函数:', kline_funcs)
except Exception as e:
    print('模块加载失败:', e)
    # 列出temp下文件
    print(os.listdir(base + r'\temp'))