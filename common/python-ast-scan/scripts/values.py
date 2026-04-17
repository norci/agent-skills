"""不执行模块地列出模块级赋值的有效值。

依赖由调用方注入：uvx --from astroid python <此脚本> <模块路径> [名字…]
不传名字时列出所有大写名字。推断不出的值返回「<未知>」。
"""

from __future__ import annotations

import pathlib
import sys

import astroid
from astroid import exceptions
from astroid.bases import UninferableBase


def render(value: object) -> str:
    if isinstance(value, UninferableBase):
        return "<未知>"
    try:
        return value.as_string()
    except (AttributeError, exceptions.AstroidError):
        return "<未知>"


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2

    module_path = pathlib.Path(argv[1])
    names = argv[2:]
    module = astroid.MANAGER.ast_from_file(str(module_path))
    if not names:
        names = sorted(name for name in module.locals if name.isupper())

    for name in names:
        if name not in module.locals:
            print(f"{name} = <未知>")
            continue
        try:
            values = [render(value) for value in module.igetattr(name)]
        except exceptions.AstroidError:
            values = ["<未知>"]
        print(f"{name} = {', '.join(values)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
