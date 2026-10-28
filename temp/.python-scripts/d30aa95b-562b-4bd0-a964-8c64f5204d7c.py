import re, ast
s = open(r'C:\Users\Administrator\.codex\skills\a-stock-data\SKILL.md', encoding='utf-8').read()
blocks = re.findall(r'```python\n(.*?)```', s, re.S)
def_blocks = [b for b in blocks if re.search(r'^\s*(def|class)\s+\w+', b, re.M)]

# 用 AST 过滤：只保留 import/def/class/常量Assign/Try，剔除示例调用(Expr/For/If/带Call的Assign)
kept_nodes = []
for b in def_blocks:
    try:
        tree = ast.parse(b)
    except SyntaxError:
        continue
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef, ast.Try)):
            kept_nodes.append(node)
        elif isinstance(node, ast.Assign):
            has_call = any(isinstance(n, ast.Call) for n in ast.walk(node.value))
            if not has_call:
                kept_nodes.append(node)
        # 其余(Expr/For/If/With等)丢弃

mod_tree = ast.Module(body=kept_nodes, type_ignores=[])
mod_src = ast.unparse(mod_tree)
out = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py'
open(out, 'w', encoding='utf-8').write(mod_src)
print('重建完成，字符数:', len(mod_src))