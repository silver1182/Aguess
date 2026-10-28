import re, ast, builtins
s = open(r'C:\Users\Administrator\.codex\skills\a-stock-data\SKILL.md', encoding='utf-8').read()
blocks = re.findall(r'```python\n(.*?)```', s, re.S)
def_blocks = [b for b in blocks if re.search(r'^\s*(def|class)\s+\w+', b, re.M)]

defined = set(dir(builtins)) | {'__name__', '__file__', '__doc__', '__package__'}
all_assign_targets = set()
for b in def_blocks:
    try: tree = ast.parse(b)
    except SyntaxError: continue
    for node in tree.body:
        if isinstance(node, ast.Import):
            for a in node.names: defined.add((a.asname or a.name).split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            for a in node.names: defined.add(a.asname or a.name)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name): all_assign_targets.add(t.id)
defined |= all_assign_targets

kept_nodes = []
for b in def_blocks:
    try: tree = ast.parse(b)
    except SyntaxError: continue
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef, ast.Try)):
            kept_nodes.append(node)
        elif isinstance(node, ast.Assign):
            has_call = any(isinstance(n, ast.Call) for n in ast.walk(node.value))
            if not has_call:  # 含函数调用的Assign视为示例执行，丢弃
                kept_nodes.append(node)

mod_tree = ast.Module(body=kept_nodes, type_ignores=[])
mod_src = ast.unparse(mod_tree)
out = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py'
open(out, 'w', encoding='utf-8').write(mod_src)
print('重建完成，字符数:', len(mod_src))