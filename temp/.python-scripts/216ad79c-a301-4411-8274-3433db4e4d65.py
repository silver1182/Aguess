import re
s = open(r'C:\Users\Administrator\.codex\skills\a-stock-data\SKILL.md', encoding='utf-8').read()
blocks = re.findall(r'```python\n(.*?)```', s, re.S)
# 只取含 def/class 定义的块
def_blocks = [b for b in blocks if re.search(r'^\s*(def|class)\s+\w+', b, re.M)]
print('定义块数量:', len(def_blocks))
mod = '\n\n'.join(def_blocks)
out = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py'
open(out, 'w', encoding='utf-8').write(mod)
print('已写出:', out, '字符数:', len(mod))