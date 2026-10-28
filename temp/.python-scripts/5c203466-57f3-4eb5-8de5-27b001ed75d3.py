import re, ast, builtins
s = open(r'C:\Users\Administrator\.codex\skills\a-stock-data\SKILL.md', encoding='utf-8').read()
blocks = re.findall(r'```python\n(.*?)```', s, re.S)
def_blocks = [b for b in blocks if re.search(r'^\s*(def|class)\s+\w+', b, re.M)]

# 预收集定义：imports + def/class + 不含Call且字面量的Assign目标（分两轮）
def collect_pre(tree):
    names = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for a in node.names: names.add((a.asname or a.name).split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            for a in node.names: names.add(a.asname or a.name)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)
    return names

def assign_keep(node, defined):
    """Assign 保留规则：目标是 Name；值无 Call 且引用名已定义；或含 Call 但目标名以_或大写开头(会话/配置初始化)"""
    if not all(isinstance(t, ast.Name) for t in node.targets):
        return False
    tgt = node.targets[0].id
    has_call = any(isinstance(n, ast.Call) for n in ast.walk(node.value))
    if has_call:
        return tgt[0] in '_ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    # 无 Call：引用名必须已定义
    for n in ast.walk(node.value):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in defined:
            return False
    return True

defined = set(dir(builtins)) | {'__name__', '__file__', '__doc__', '__package__', 'None', 'True', 'False'}
# 第一轮：收集所有 def/class/import 名
for b in def_blocks:
    try: tree = ast.parse(b)
    except SyntaxError: continue
    defined |= collect_pre(tree)

# 第二轮：遍历时对每个 Assign 判断，保留目标加入 defined（供后续引用）
kept_nodes = []
for b in def_blocks:
    try: tree = ast.parse(b)
    except SyntaxError: continue
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef, ast.Try)):
            kept_nodes.append(node)
        elif isinstance(node, ast.Assign) and assign_keep(node, defined):
            for t in node.targets:
                if isinstance(t, ast.Name): defined.add(t.id)
            kept_nodes.append(node)

mod_tree = ast.Module(body=kept_nodes, type_ignores=[])
mod_src = ast.unparse(mod_tree)
out = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py'
open(out, 'w', encoding='utf-8').write(mod_src)
print('重建完成，字符数:', len(mod_src))