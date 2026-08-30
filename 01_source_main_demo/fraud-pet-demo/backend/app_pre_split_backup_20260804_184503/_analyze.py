import ast
src = open("main.py", encoding="utf-8").read()
tree = ast.parse(src)
ROUTE_METHODS = {"get", "post", "put", "delete", "patch", "options"}
rows = []
def walk(node, scope):
    for n in ast.iter_child_nodes(node):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decos = []
            for d in n.decorator_list:
                if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and isinstance(d.func.value, ast.Name) and d.func.value.id == 'app':
                    if d.func.attr in ROUTE_METHODS:
                        p = None
                        try:
                            if d.args:
                                p = ast.literal_eval(d.args[0])
                        except Exception:
                            p = "<nonliteral>"
                        decos.append((d.func.attr, p))
            rows.append((n.lineno, scope, n.name, decos))
            walk(n, scope + '/' + n.name)
        elif isinstance(n, ast.ClassDef):
            rows.append((n.lineno, scope, 'CLASS:' + n.name, []))
            walk(n, scope + '/' + n.name)
        else:
            walk(n, scope)
walk(tree, 'module')
print("=== MODULE-LEVEL defs/classes ===")
for ln, sc, nm, dc in rows:
    if sc == 'module':
        print(f"{ln:5d}  {nm}")
print("\n=== defs nested inside create_app (non-handler helpers) ===")
for ln, sc, nm, dc in rows:
    if sc.startswith('module/create_app') and not dc:
        print(f"{ln:5d}  {nm}")
print("\n=== HANDLERS (decorated with @app.<route>) ===")
handlers = [r for r in rows if r[3]]
print("total handlers:", len(handlers))
for ln, sc, nm, dc in handlers:
    print(f"{ln:5d}  {sc.split('/')[-1]:35s} {dc}")
