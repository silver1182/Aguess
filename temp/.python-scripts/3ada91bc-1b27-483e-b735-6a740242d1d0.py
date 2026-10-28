import re
s = open(r'C:\Users\Administrator\.codex\skills\a-stock-data\SKILL.md', encoding='utf-8').read()
blocks = re.findall(r'```python\n(.*?)```', s, re.S)
print('python 代码块数量:', len(blocks))
print('代码总字符:', sum(len(b) for b in blocks))
for i, b in enumerate(blocks):
    lines = b.splitlines()
    print(f'--- block {i}: {len(b)} chars | 首行: {lines[0][:70] if lines else "(空)"} | 末行: {lines[-1][:70] if lines else "(空)"}')