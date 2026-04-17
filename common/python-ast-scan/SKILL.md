---
name: python-ast-scan
description: 清点 python 代码时：用现成工具成批回答仓库级问题。
---

# 全仓事实清点

## 边界

符号定义、引用与改名波及交给 `agent-lsp-navigation`。本技能只输出事实清单。

每条扫描输出 `文件:行号:命中文本`。一次跑出全表，再按名字筛；筛使用 `grep -E`，不改写查询模式重扫。

工具由 `bunx` 与 `uvx` 现取，可执行文件用 `--package @ast-grep/cli ast-grep` 指定。

## 赋值与值

```sh
bunx --yes --package @ast-grep/cli ast-grep run -p '$NAME = $VALUE' --lang python <根>
uvx --from astroid python <技能目录>/scripts/values.py <模块路径> [名字…]
```

`values.py` 输出 `名字 = 值`，不传名字时列出全部大写名字。推断不出的值写 `<未知>`。出现 `<未知>` 时，在项目里执行一次那行代码取值。

## 调用与字面量

```sh
bunx --yes --package @ast-grep/cli ast-grep run -p '$FUNC($$$ARGS)' --lang python <根>
bunx --yes --package @ast-grep/cli ast-grep run --kind integer --lang python <根>
bunx --yes --package @ast-grep/cli ast-grep run --kind float --lang python <根>
uvx ruff check --select PLR2004 --output-format concise <根>
```

`ruff` 的 `PLR2004` 只报比较里的魔数；退出码非零表示命中。

## 导入边与依赖图

```sh
bunx --yes --package @ast-grep/cli ast-grep run -p 'import $MOD' --lang python <根>
bunx --yes --package @ast-grep/cli ast-grep run -p 'from $MOD import $$$NAMES' --lang python <根>
uvx pydeps --show-deps --no-show --noshow <包>
```

`pydeps` 输出 JSON，含 `imports` 与 `imported_by`。

## 同名定义

函数和类各扫一次，按名字去重。输出的是候选，读回源码后才判是否同一职责。

```sh
bunx --yes --package @ast-grep/cli ast-grep run --kind function_definition --lang python <根> \
  | grep -E '^[^:]+:[0-9]+:(async )?def ' \
  | sed -E 's/^.*:[[:space:]]*(async )?def ([A-Za-z_][A-Za-z0-9_]*).*$/\2/' | sort | uniq -d

bunx --yes --package @ast-grep/cli ast-grep run --kind class_definition --lang python <根> \
  | grep -E '^[^:]+:[0-9]+:class ' \
  | sed -E 's/^.*:[[:space:]]*class ([A-Za-z_][A-Za-z0-9_]*).*$/\1/' | sort | uniq -d
```
