"""全仓结构化清点 — 用语法树回答「有哪些」，不用逐个读文件

五个子命令, 各答一类问题:

    constants  <根>   模块级常量: 名字、值、行号 (哪个模块写死了数字)
    calls      <根>   调用实参: 谁给哪些函数传了什么 (窗长/阈值/超时从哪来)
    numbers    <根>   函数内的数字字面量, 按作用域归类 (哪个函数里藏了魔数)
    imports    <根>   模块级导入边 (改模块位置前看谁依赖谁)
    duplicates <根>   同名顶层定义出现两处以上 (同一职责是否已有第二份实现)

每个子命令都接受 --skip 目录前缀与 --filter 正则; 缺省跳过 .venv/.git/构建产物与测试文件。

用法:

    python scan.py constants . --filter 'period|window|margin'
    python scan.py calls . --filter 'rolling_|upto'
    python scan.py numbers . --filter 'flow'
    python scan.py duplicates .
"""

from __future__ import annotations

import argparse
import ast
import pathlib
import re
import sys
from collections import defaultdict

DEFAULT_SKIP = {
    ".venv", "venv", ".git", "node_modules", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "build", "dist", "site-packages",
}


def sources(root: str, skip: set[str], include_tests: bool) -> list[pathlib.Path]:
    paths = []
    for path in sorted(pathlib.Path(root).rglob("*.py")):
        if set(path.parts) & skip:
            continue
        name = path.name
        if not include_tests and (name.endswith("_test.py") or name == "conftest.py"):
            continue
        paths.append(path)
    return paths


def is_number(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    )


def command_constants(paths: list[pathlib.Path], pattern: re.Pattern[str] | None) -> None:
    """模块级赋值里值为数字或是短容器的常量"""
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            target = value = None
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target, value = node.targets[0], node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                target, value = node.target, node.value
            if not isinstance(target, ast.Name):
                continue
            if not (is_number(value) or isinstance(value, (ast.Dict, ast.List, ast.Tuple))):
                continue
            if pattern and not pattern.search(target.id):
                continue
            try:
                rendered = ast.literal_eval(value)
            except ValueError:
                rendered = ast.unparse(value)
            print(f"{path}:{node.lineno}  {target.id} = {rendered!r}")


def command_calls(paths: list[pathlib.Path], pattern: re.Pattern[str] | None) -> None:
    """每个调用点: 被调名、位置实参、关键字实参"""
    for path in paths:
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            function = node.func
            if isinstance(function, ast.Name):
                name = function.id
            elif isinstance(function, ast.Attribute):
                name = function.attr
            else:
                name = ast.unparse(function)
            if pattern and not pattern.search(name):
                continue
            arguments = [ast.unparse(argument) for argument in node.args]
            keywords = [f"{kw.arg}={ast.unparse(kw.value)}" for kw in node.keywords]
            rendered = ", ".join(arguments + keywords)
            print(f"{path}:{node.lineno}  {name}({rendered})")


def command_numbers(paths: list[pathlib.Path], pattern: re.Pattern[str] | None) -> None:
    """函数体内的数字字面量, 按 文件:函数 归组; 0 与 1 不列"""
    for path in paths:
        if pattern and not pattern.search(str(path)):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for function in ast.walk(tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            numbers = sorted(
                {
                    node.value
                    for node in ast.walk(function)
                    if is_number(node) and node.value not in (0, 1)
                }
            )
            if numbers:
                print(f"{path}:{function.lineno}  {function.name}  {numbers}")


def command_imports(paths: list[pathlib.Path], pattern: re.Pattern[str] | None) -> None:
    """模块级导入边: 被导入模块出现于哪些文件"""
    edges: dict[str, set[str]] = defaultdict(set)
    for path in paths:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                edges[node.module].add(str(path))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    edges[alias.name].add(str(path))
    for module, dependents in sorted(edges.items()):
        if pattern and not pattern.search(module):
            continue
        print(f"{module}  <- {len(dependents)} 处: {', '.join(sorted(dependents))}")


def command_duplicates(paths: list[pathlib.Path], pattern: re.Pattern[str] | None) -> None:
    """同名顶层定义出现在两个以上模块 — 同一职责可能已有第二份实现"""
    site: dict[str, list[str]] = defaultdict(list)
    for path in paths:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if pattern and not pattern.search(node.name):
                    continue
                site[node.name].append(f"{path}:{node.lineno}")
    for name, locations in sorted(site.items()):
        if len(locations) > 1:
            print(f"{name}  ->  {', '.join(locations)}")


COMMANDS = {
    "constants": command_constants,
    "calls": command_calls,
    "numbers": command_numbers,
    "imports": command_imports,
    "duplicates": command_duplicates,
}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=sorted(COMMANDS))
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--filter", default=None, help="只报匹配此正则的行")
    parser.add_argument("--skip", default="", help="额外跳过的目录前缀, 逗号分隔")
    parser.add_argument("--include-tests", action="store_true")
    options = parser.parse_args(argv)
    skip = DEFAULT_SKIP | {part for part in options.skip.split(",") if part}
    paths = sources(options.root, skip, options.include_tests)
    pattern = re.compile(options.filter) if options.filter else None
    COMMANDS[options.command](paths, pattern)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
