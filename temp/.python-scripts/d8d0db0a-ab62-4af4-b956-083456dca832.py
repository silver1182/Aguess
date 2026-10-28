import re, ast
s = open(r'C:\Users\Administrator\.codex\skills\a-stock-data\SKILL.md', encoding='utf-8').read()
blocks = re.findall(r'```python\n(.*?)```', s, re.S)
for i, b in enumerate(blocks):
    # 判断块性质：是否有 def/class 定义
    has_def = bool(re.search(r'^\s*(def|class)\s+\w+', b, re.M))
    try:
        tree = ast.parse(b)
        tops = [n.__class__.__name__ for n in tree.body]
        # 提取顶层函数名
        fnames = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    except Exception as e:
        tops = [f'PARSE_ERR:{e}']
        fnames = []
    print(f'block {i:2d} def={has_def} len={len(b):6d} tops={tops} fnames={fnames[:6]}')