---
name: python-code-style
description: 写 Python 变换代码时：选表达式形态。
---

开发者先判这段变换是否按同一规则映射输入。映射写成 functional 表达式，多分支状态机写成显式语句。

- 开发者用 `map(f, xs, ys)` 逐位映射；短序列由 `map` 自动先尽。
- 开发者用 `[c] * n` 接 `xs[n:]` 给前段补常量。
- 开发者用 `set(a).difference(b)` 或 `set(a).intersection(b)` 处理集合归属。
- 开发者用底层库的批量写法处理表列运算，让列名与操作各出现一次。
- 开发者把复杂规则抽成有名字的工具函数，让主调用点保持映射表达式。

开发者禁止把 `if` 控制流压进表达式。

- 判据是循环变量、迭代源和过滤条件同现于一行。`x for x in xs if C` 属违规；集合归属改用集合算子，其余情形先算集合再用显式语句处理。
- 判据是 `if` 与 `else` 同现于一行，且该行不是 `if`、`elif`、`else` 语句块首行。`A if C else B` 属违规；return 位写成先 `if C: return X` 再 `return Y`，实参位先算出中间变量，推导式元素位改成显式循环与语句。
- 缺值按本义用 `None` 或 `NaN`，不用条件表达式兜底。

```python
def changes(values: list[float | None], gap: int) -> list[float | None]:
    def change_of(current, previous):
        if current is None or previous is None:
            return None
        return current - previous

    return [None] * min(gap, len(values)) + list(map(change_of, values[gap:], values))
```

functional 形式若更长或更难读，开发者用显式语句；逻辑本身是多分支状态机时，开发者用显式语句。
