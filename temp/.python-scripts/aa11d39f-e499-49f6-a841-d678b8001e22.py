import re, ast
s = open(r'C:\Users\Administrator\.codex\skills\a-stock-data\SKILL.md', encoding='utf-8').read()
blocks = re.findall(r'```python\n(.*?)```', s, re.S)
def_blocks = [b for b in blocks if re.search(r'^\s*(def|class)\s+\w+', b, re.M)]
assign_targets = {}
for bi, b in enumerate(def_blocks):
    try: tree = ast.parse(b)
    except SyntaxError: continue
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    has_call = any(isinstance(n, ast.Call) for n in ast.walk(node.value))
                    assign_targets.setdefault(t.id, []).append((bi, has_call, node.value.__class__.__name__))
# 打印每个顶层Assign目标（含Call的标记）
for k, v in sorted(assign_targets.items()):
    print(f'{k}: {v}')