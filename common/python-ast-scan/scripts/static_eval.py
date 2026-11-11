"""静态求值: 不执行模块, 算出模块级赋值的有效值

用途 — 配置散在字典、类属性、跨模块导入里, 读源码看不出值, 而 import 会触发联网、
读凭证、写文件。ast 只读语法树, 副作用为零。

用法一 (命令行):

    python static_eval.py <模块路径>            # 列出全部模块级赋值
    python static_eval.py <模块路径> 名字 [名字…]  # 只列指定名字

用法二 (被别的脚本导入):

    import sys; sys.path.insert(0, "<本目录>")
    from static_eval import module_env, ev, UNKNOWN

    env = module_env("config.py")
    print(env["CONFIG"]["datahub"]["floor_window"])

求不出的值返回 UNKNOWN, 不静默给错值。求不出的两类: 引用了运行期才知道的东西
(环境变量、函数返回、datetime.now()), 以及本求值器不认识的节点类型。
"""

from __future__ import annotations

import ast
import pathlib
import sys

BUILTINS = {
    "range": range, "list": list, "tuple": tuple, "dict": dict, "set": set,
    "frozenset": frozenset, "sorted": sorted, "len": len, "min": min, "max": max,
    "sum": sum, "abs": abs, "round": round, "str": str, "int": int, "float": float,
    "bool": bool, "zip": zip, "enumerate": enumerate,
}

OPERATORS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
    ast.Pow: lambda a, b: a**b,
}


class _Unknown:
    """求不出的值 — 与任何东西比较皆不相等, 且不吞掉调用方的判断"""

    def __repr__(self) -> str:
        return "<未知>"

    def __bool__(self) -> bool:
        return False


UNKNOWN = _Unknown()


def ev(node: ast.AST, env: dict[str, object]) -> object:
    """求一个表达式节点之值; 任何一环求不出即整棵返回 UNKNOWN"""
    try:
        return _evaluate(node, env)
    except Exception:
        return UNKNOWN


def _evaluate(node: ast.AST, env: dict[str, object]) -> object:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return env.get(node.id, UNKNOWN)
    if isinstance(node, ast.Dict):
        out: dict[object, object] = {}
        for key, value in zip(node.keys, node.values):
            if key is None:
                merged = ev(value, env)
                if isinstance(merged, dict):
                    out.update(merged)
                continue
            out[ev(key, env)] = ev(value, env)
        return out
    if isinstance(node, ast.List):
        return [ev(element, env) for element in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(ev(element, env) for element in node.elts)
    if isinstance(node, ast.Set):
        return {ev(element, env) for element in node.elts}
    if isinstance(node, ast.BinOp):
        operate = OPERATORS.get(type(node.op))
        return operate(ev(node.left, env), ev(node.right, env)) if operate else UNKNOWN
    if isinstance(node, ast.UnaryOp):
        value = ev(node.operand, env)
        if isinstance(node.op, ast.USub):
            return -value
        if isinstance(node.op, ast.UAdd):
            return +value
        if isinstance(node.op, ast.Not):
            return not value
        return UNKNOWN
    if isinstance(node, ast.Subscript):
        return ev(node.value, env)[ev(node.slice, env)]
    if isinstance(node, ast.Attribute):
        return getattr(ev(node.value, env), node.attr, UNKNOWN)
    if isinstance(node, ast.IfExp):
        return ev(node.body, env) if ev(node.test, env) else ev(node.orelse, env)
    if isinstance(node, ast.Call):
        function = ev(node.func, env)
        arguments = [ev(argument, env) for argument in node.args]
        keywords = {kw.arg: ev(kw.value, env) for kw in node.keywords if kw.arg}
        return function(*arguments, **keywords) if callable(function) else UNKNOWN
    return UNKNOWN


def module_env(path: str | pathlib.Path, seen: set[pathlib.Path] | None = None) -> dict[str, object]:
    """逐条执行模块级赋值 — from x import y 递归到被导入模块之 __all__ 与赋值"""
    target = pathlib.Path(path)
    seen = seen if seen is not None else set()
    if target in seen:
        return {}
    seen.add(target)
    tree = ast.parse(target.read_text(encoding="utf-8"))
    env: dict[str, object] = dict(BUILTINS)
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported = _resolve(node.module, target.parent)
            if imported is not None:
                nested = module_env(imported, seen)
                for alias in node.names:
                    if alias.name in nested:
                        env[alias.asname or alias.name] = nested[alias.name]
        elif isinstance(node, ast.Assign):
            value = ev(node.value, env)
            for assignee in node.targets:
                if isinstance(assignee, ast.Name):
                    env[assignee.id] = value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            if isinstance(node.target, ast.Name):
                env[node.target.id] = ev(node.value, env)
    return env


def _resolve(module: str, near: pathlib.Path) -> pathlib.Path | None:
    relative = pathlib.Path(*module.split("."))
    for candidate in (near / relative.with_suffix(".py"), relative.with_suffix(".py")):
        if candidate.exists():
            return candidate
    return None


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    env = module_env(argv[1])
    names = argv[2:] or [key for key in env if key not in BUILTINS]
    for name in names:
        print(f"{name} = {env.get(name, UNKNOWN)!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
