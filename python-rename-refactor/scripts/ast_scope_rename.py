"""AST 作用域感知改名 (单文件, 不走 rope)。

用法:
    uv run python ast_scope_rename.py tasks.json

tasks.json: [[path, scope, old, new[, kind]], ...]
  scope  null          模块层 (整文件, 含各函数体内的引用)
         "Foo"         类 Foo (其方法体内皆算)
         "Foo.bar"     方法 / 函数 bar
  kind   "name"(缺省)  改 arg / Name / ExceptHandler.name / global / def|class 名
         "attr"        改 obj.x 之 x (含 self.x 与字段用点)

能改 rope 会漏 / 会过界者:
  - 改 keyword 实参之名 (`.sort(key=...)` 之 key) 与字符串绝不相干 —— 本器只动
    Name/arg/Attribute, 故 rope 之「把 key= 也改了」不会发生。
  - global / nonlocal 声明 (名字存于 ast.Global.names, 非 Name 节点)。
  - except ... as e 之 e 与 def / class 之名。
  - 非 ASCII 源文件: ast col_offset 为 **utf-8 字节偏移**, 本器转为字符偏移。

作用域规则: 只在目标作用域内改; 若某外层已绑定 old, 则不再下探「同样绑定 old 之子
作用域」(真遮蔽者不动)。故同一字母在不同函数里各改各名, 互不牵连。

不碰者 (改毕须另 grep): `__all__` 字符串、`TypeVar("T")` 之首参、f-string / URL 里
之 `{d}` 占位、SQL 列名、keyword 参数名本身。
"""
import ast
import json
import re
import sys

SCOPE_NODES = (
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Lambda,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
)

_bind_cache: dict = {}


def _is_scope(node) -> bool:
    return isinstance(node, SCOPE_NODES)


def _add_target(names: set, target) -> None:
    if isinstance(target, ast.Name):
        names.add(target.id)
    elif isinstance(target, ast.Tuple | ast.List):
        for element in target.elts:
            _add_target(names, element)
    elif isinstance(target, ast.Starred):
        _add_target(names, target.value)


def _direct_bindings(scope) -> set[str]:
    """scope 直接绑定之名 (不下探子作用域)。"""
    names: set[str] = set()
    for child in ast.iter_child_nodes(scope):
        if isinstance(child, ast.arg):
            names.add(child.arg)
        elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store | ast.Del):
            names.add(child.id)
        elif isinstance(child, ast.Assign):
            for target in child.targets:
                _add_target(names, target)
        elif isinstance(child, (ast.For, ast.AsyncFor)):
            _add_target(names, child.target)
        elif isinstance(child, ast.comprehension):
            _add_target(names, child.target)
        elif isinstance(child, ast.withitem) and child.optional_vars is not None:
            _add_target(names, child.optional_vars)
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(child.name)
        elif isinstance(child, ast.Import):
            for alias in child.names:
                names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(child, ast.ImportFrom):
            for alias in child.names:
                names.add(alias.asname or alias.name)
        elif isinstance(child, ast.ExceptHandler) and child.name:
            names.add(child.name)
        elif isinstance(child, ast.NamedExpr):
            _add_target(names, child.target)
    return names


def _binds(node, old: str) -> bool:
    key = (id(node), old)
    if key not in _bind_cache:
        _bind_cache[key] = old in _direct_bindings(node)
    return _bind_cache[key]


def _collect(scope, old, kind, out, lines, outer_binds=False) -> None:
    own = _binds(scope, old)
    for child in ast.iter_child_nodes(scope):
        if _is_scope(child):
            if (
                isinstance(
                    child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
                )
                and child.name == old
            ):
                line_text = lines[child.lineno - 1]
                match = re.search(
                    r"(?:def|class)\s+(" + re.escape(old) + r")\b", line_text
                )
                if match:
                    out.append(
                        (
                            child.lineno,
                            len(line_text[: match.start(1)].encode("utf-8")),
                            len(old),
                        )
                    )
            child_binds = _binds(child, old)
            if outer_binds and child_binds:  # 真遮蔽: 子作用域另有绑定, 不动
                continue
            _collect(child, old, kind, out, lines, outer_binds or child_binds)
            continue
        if isinstance(child, ast.Name) and child.id == old:
            out.append((child.lineno, child.col_offset, len(old)))
        elif isinstance(child, ast.arg) and child.arg == old:
            out.append((child.lineno, child.col_offset, len(old)))
        elif isinstance(child, ast.Global | ast.Nonlocal) and old in child.names:
            line_text = lines[child.lineno - 1]
            match = re.search(
                r"\b(?:global|nonlocal)\s+.*?\b" + re.escape(old) + r"\b", line_text
            )
            if match:
                start = line_text.rindex(old, match.start())
                out.append(
                    (child.lineno, len(line_text[:start].encode("utf-8")), len(old))
                )
        elif isinstance(child, ast.ExceptHandler) and child.name == old:
            line_text = lines[child.lineno - 1]
            match = re.search(r"\bas\s+(" + re.escape(old) + r")\b", line_text)
            if match:
                out.append(
                    (child.lineno, len(line_text[: match.start(1)].encode("utf-8")), len(old))
                )
        _collect(child, old, kind, out, lines, outer_binds or own)


def _collect_attrs(scope, old, out, outer_binds=False) -> None:
    own = _binds(scope, old)
    for child in ast.iter_child_nodes(scope):
        if _is_scope(child):
            child_binds = _binds(child, old)
            if outer_binds and child_binds:
                continue
            _collect_attrs(child, old, out, outer_binds or child_binds)
            continue
        if isinstance(child, ast.Attribute) and child.attr == old:
            out.append(child)
        _collect_attrs(child, old, out, outer_binds or own)


def _scopes(tree) -> dict:
    out: dict = {}

    def walk(node, prefix):
        for child in node.body:
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                qualname = f"{prefix}.{child.name}" if prefix else child.name
                out[qualname] = child
                walk(child, qualname)

    walk(tree, "")
    return out


def main(tasks_path: str) -> None:
    tasks = json.load(open(tasks_path))
    for task in tasks:
        path, scope, old, new = task[:4]
        kind = task[4] if len(task) > 4 else "name"
        _bind_cache.clear()
        text = open(path).read()
        lines = text.split("\n")
        tree = ast.parse(text)
        sites: list[tuple[int, int, int]] = []
        if scope is None:
            _collect(tree, old, kind, sites, lines)
        else:
            scopes = _scopes(tree)
            if scope not in scopes:
                raise KeyError(f"{path}: 无作用域 {scope}")
            if kind == "attr":
                attrs: list = []
                _collect_attrs(scopes[scope], old, attrs)
                for node in attrs:
                    segment = ast.get_source_segment(text, node) or node.attr
                    sites.append(
                        (node.lineno, node.col_offset + len(segment) - len(old), len(old))
                    )
            else:
                _collect(scopes[scope], old, kind, sites, lines)
        replacements: list[tuple[int, int, int]] = []
        for lineno, byte_col, length in sites:
            line_text = lines[lineno - 1]
            char_col = len(line_text.encode("utf-8")[:byte_col].decode("utf-8"))
            assert line_text[char_col : char_col + length] == old, (
                f"{path}:{lineno}: {line_text[char_col:char_col+length]!r} != {old}"
            )
            replacements.append((lineno, char_col, length))
        by_line: dict[int, list[tuple[int, int]]] = {}
        for lineno, char_col, length in replacements:
            by_line.setdefault(lineno, []).append((char_col, length))
        for lineno, items in by_line.items():
            line = lines[lineno - 1]
            for char_col, length in sorted(items, reverse=True):
                line = line[:char_col] + new + line[char_col + length :]
            lines[lineno - 1] = line
        open(path, "w").write("\n".join(lines))
        print(f"{path} [{scope}] {old}->{new}  ({len(replacements)} sites)", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
