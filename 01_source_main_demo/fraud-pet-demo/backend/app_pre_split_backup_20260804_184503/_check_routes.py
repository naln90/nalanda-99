"""Verify the split preserves the exact route table (method + path)."""
import ast
import glob
import os

ROUTE_METHODS = {"get", "post", "put", "delete", "patch", "options"}


def collect_app_routes(path):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    routes = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in node.decorator_list:
                if (
                    isinstance(d, ast.Call)
                    and isinstance(d.func, ast.Attribute)
                    and isinstance(d.func.value, ast.Name)
                    and d.func.value.id == "app"
                    and d.func.attr in ROUTE_METHODS
                ):
                    method = d.func.attr.upper()
                    p = ast.literal_eval(d.args[0])
                    routes.add((method, p))
    return routes


def collect_router_routes(path):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    prefix = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "router":
                    # find APIRouter(prefix=...) call
                    if isinstance(node.value, ast.Call):
                        for kw in node.value.keywords:
                            if kw.arg == "prefix":
                                prefix = ast.literal_eval(kw.value)
    routes = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in node.decorator_list:
                if (
                    isinstance(d, ast.Call)
                    and isinstance(d.func, ast.Attribute)
                    and isinstance(d.func.value, ast.Name)
                    and d.func.value.id == "router"
                    and d.func.attr in ROUTE_METHODS
                ):
                    method = d.func.attr.upper()
                    r = ast.literal_eval(d.args[0])
                    routes.add((method, prefix + r))
    return routes


old = collect_app_routes("main.py.bak")
new = set()
for f in sorted(glob.glob("routers/*.py")):
    if os.path.basename(f) == "__init__.py":
        continue
    new |= collect_router_routes(f)

print("OLD route count:", len(old))
print("NEW route count:", len(new))
missing = old - new
extra = new - old
if missing:
    print("\n!!! MISSING in new (would break demo):")
    for m in sorted(missing):
        print("   ", m)
if extra:
    print("\n!!! EXTRA in new (unexpected):")
    for m in sorted(extra):
        print("   ", m)
if not missing and not extra:
    print("\nOK: route tables are IDENTICAL (method + path).")
