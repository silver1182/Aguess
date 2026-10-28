import json, requests, urllib3, hashlib
urllib3.disable_warnings()
sess = requests.Session()
sess.verify = False
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

# 财联社电报 - 参考 a_stock_data 里的实现
import importlib.util
spec = importlib.util.spec_from_file_location('asd', r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
asd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asd)

# 用 asd.cls_telegraph 测试
try:
    rows = asd.cls_telegraph(page_size=50)
    print('条数:', len(rows))
    for r in rows[:3]:
        print('•', r['title'][:50], '|', r['time'])
except Exception as e:
    print('asd.cls_telegraph err:', e)

# 也试 wallstreetcn_lives
try:
    rows = asd.wallstreetcn_lives(limit=10)
    print('\n华尔街见闻条数:', len(rows))
    for r in rows[:3]:
        print('•', str(r)[:80])
except Exception as e:
    print('wallstreetcn err:', e)
