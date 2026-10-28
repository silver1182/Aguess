import importlib.util, json
TEMP = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
spec = importlib.util.spec_from_file_location('asd', TEMP + r'\a_stock_data.py')
asd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asd)
rows = asd.cls_telegraph(page_size=100)
print('条数:', len(rows))
# 打印今天所有电报标题, 检查是否有个股
for r in rows[:30]:
    print('•', r['title'][:60])
