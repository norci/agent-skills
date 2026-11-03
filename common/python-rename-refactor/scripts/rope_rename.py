"""批量 rope 语义改名驱动。

用法:
    uv run --with rope python rope_rename.py tasks.json

tasks.json 之形:
    [["futures/x.py", "    sgn: int  # ...", "sgn", "direction"], ...]
    每项 = [文件路径(相对 project 根), anchor 唯一子串, 旧名, 新名]
    anchor 须唯一, 且含旧名; 脚本以其偏移定位符号定义处, 调 rope Rename。

要点:
  - 一个 Project 会话跑完所有任务 (索引一次, 快)。
  - ignored_resources 排除 .venv / results / 缓存目录, 免索引他物。
  - rope 不覆盖 dataclass 合成 __init__ 之关键字实参与推断不达之跨模块属性,
    故改毕须跑 pyright, 漏网以词边界替换补齐 (通用短名不可批量替换)。
"""

import json
import sys

from rope.base.project import Project
from rope.refactor.rename import Rename

ROOT = "."  # 项目根 (含包之父目录)
IGNORE = [".venv", "results", "__pycache__", "*.duckdb", "*.parquet", ".git"]


def main(tasks_path: str) -> None:
    tasks = json.load(open(tasks_path))
    project = Project(ROOT, ignored_resources=IGNORE)
    for path, anchor, old, new in tasks:
        resource = project.get_resource(path)
        text = resource.read()
        pos = text.index(anchor) + anchor.index(old)
        changes = Rename(project, resource, pos).get_changes(new)
        project.do(changes)
        touched = sorted({str(c.resource.path) for c in changes.changes})
        print(f"{path}: {old} -> {new}  [{', '.join(touched)}]", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
