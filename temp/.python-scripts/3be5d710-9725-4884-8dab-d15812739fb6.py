import re
s = open(r'C:\Users\Administrator\.codex\skills\a-stock-data\SKILL.md', encoding='utf-8').read()
blocks = re.findall(r'```python\n(.*?)```', s, re.S)
for i, b in enumerate(blocks):
    if 'recent_20 = data[-20:]' in b:
        print(f'命中 block {i}, 长度 {len(b)}')
        print(b[:4000])
        break