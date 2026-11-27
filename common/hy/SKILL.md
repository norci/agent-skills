---
name: hy
description: 写或测 Hy 代码时：用现成宏与读器，按 Python 语义落笔。
---

## 先查现成写法

先看下文接口清单。清单里有名字，就用那个名字。清单里没有，才写 helper。

- 造 dict 写 `dfor`，造 list 写 `lfor`，造 set 写 `sfor`，造迭代器写 `gfor`。`lfor`、`sfor`、`gfor` 的值可写 `#* ITERABLE`；`dfor` 的最后一项可写 `#** MAPPING`。
- 条件写 `cond`（分支成对，默认支写 `True`）、`when`、`match`；`case` 与 `branch` 的默认支写 `else`；比较链写 `chainc`。
- 提前跳出写 `block` 加 `block-ret`，跨块跳出写 `block-ret-from`。
- 尾递归写 `loop` 加 `recur`，绑定表每项写 `[名字 初值]`，如 `[[x 0] [acc 1]]`。自递归函数不手写。
- 局部解构写 `let+ setv+ defn+ fn+`，绑定项是「模式 值」对。核心 `setv` 和 `let` 只按位置解构，按键名取值要用 Hyrule 的模式。
- 多维索引写 `ncut`，如 `(ncut df.loc : ["B"])`。逐层取 dict 写 `(.get (.get m k1) k2)`。
- 原地改集合写 `assoc`；返回链式结果写 `doto`。
- 跨模块调函数写 `hy.I`，调宏写 `hy.R`；模块路径中的点写斜杠，如 `hy.I.os/path.basename`。
- `defreader` 收掉重复外壳之前，先确认 `defmacro` 做不到。

## 接口清单

核心宏自动可用。Hyrule 名字从顶层取：`(require hyrule * :readers *)` 与 `(import hyrule *)`。下列各行按模块分组。

### Hy 核心

- 基础与定义：`do`、`do-mac`、`eval-and-compile`、`eval-when-compile`、`py`、`pys`、`pragma`、`setv`、`setx`、`let`、`global`、`nonlocal`、`del`、`annotate`、`deftype`、`defn`、`fn`、`defmacro`、`defreader`、`defclass`、`import`、`require`、`export`、`get-macro`、`local-macros`。
- 引用与展开：`quote`、`quasiquote`、`unquote`、`unquote-splice`、`.`、`unpack-iterable`、`unpack-mapping`、`hy.macroexpand`、`hy.macroexpand-1`。
- 控制与运算：`if`、`when`、`cond`、`while`、`break`、`continue`、`for`、`lfor`、`dfor`、`gfor`、`sfor`、`with`、`match`、`raise`、`try`、`return`、`yield`、`await`、`chainc`、`assert`。
- 占位宏：`else`、`except`、`except*`、`finally`。`try` 的 `except` 子句和 `while` 的 `else` 由外层宏解释。
- 读器糖：`'` 为 `quote`，`` ` `` 为 `quasiquote`，`~` 为 `unquote`，`~@` 为 `unquote-splice`，`#^` 为 `annotate`，`#*` 为 `unpack-iterable`，`#**` 为 `unpack-mapping`。

### Hy 模块

- 函数：`hy.read`、`hy.read-many`、`hy.eval`、`hy.repr`、`hy.repr-register`、`hy.mangle`、`hy.unmangle`、`hy.macroexpand`、`hy.macroexpand-1`、`hy.gensym`、`hy.as-model`。
- 对象与读器：`hy.I`、`hy.R`、`hy.HyReader`、`hy.Reader`、`hy.PrematureEndOfInput`。`hy.R` 是编译器语法糖。
- 模型类型：`hy.models.Object`、`String`、`Bytes`、`Symbol`、`Keyword`、`Integer`、`Float`、`Complex`、`Sequence`、`FComponent`、`FString`、`List`、`Dict`、`Expression`、`Set`、`Tuple`、`Lazy`。
- Python 运算符：`+`、`-`、`*`、`**`、`/`、`//`、`%`、`@`、`<<`、`>>`、`&`、`|`、`^`、`bnot`、`<`、`>`、`<=`、`>=`、`=`、`!=`、`and`、`or`、`not`、`is`、`is-not`、`in`、`not-in`、`get`、`cut`。作为函数用 `(import hy.pyops *)`；宏名优先。Python 的 `==` 写作 `=`，`~` 写作 `bnot`。

### Hyrule

- `hyrule.anaphoric`：读器 `%`（`#%`），宏 `ap-if`、`ap-each`、`ap-each-while`、`ap-map`、`ap-map-when`、`ap-filter`、`ap-reject`、`ap-dotimes`、`ap-first`、`ap-last`、`ap-reduce`、`ap-when`、`ap-with`。`#%` 用 `%1`、`%2`、`%*` 和 `%**`；`ap-*` 用 `it`。
- `hyrule.argmove`：宏 `->`、`->>`、`as->`、`some->`、`doto`。
- `hyrule.collections`：函数 `assoc`，宏 `ncut`，读器 `s`（`#s`）。
- `hyrule.control`：宏 `block`、`branch`、`case`、`cfor`、`defmain`、`do-n`、`ebranch`、`ecase`、`lif`、`list-n`、`loop`、`unless`；类 `recur`；`block` 专用形式 `block-ret`、`block-ret-from`。
- `hyrule.db`：函数 `sqlite-db`、`sqlq`，类 `AttributeRow`，宏 `sqlexec`。
- `hyrule.destructure`：宏 `defn+`、`dict=:`、`fn+`、`let+`、`setv+`。
- `hyrule.iterables`：函数 `butlast`、`coll?`、`distinct`、`drop-last`、`flatten`、`rest`、`thru`。
- `hyrule.macrotools`：读器 `/`（`#/`），宏 `def-gensyms`、`defmacro-kwargs`、`defmacro!`，函数 `macroexpand-all`、`map-hyseq`、`map-model`、`match-fn-params`。
- `hyrule.oop`：宏 `meth`、`ameth`。
- `hyrule.hypprint`：类 `PrettyPrinter`，函数 `pformat`、`pp`、`pprint`、`readable?`、`recursive?`、`saferepr`。
- `hyrule.sequences`：类 `Sequence`，宏 `seq`、`defseq`，函数 `end-sequence`。
- `hyrule.misc`：宏 `comment`、`of`、`pun`、`smacrolet`，函数 `constantly`、`dec`、`inc`、`import-path`、`parse-args`、`sign`、`xor`，读器 `__`（`#__`）。

## 互操作

Python 侧先 `import hy` 才能导入 `.hy` 模块。在包的 `__init__.py` 写 `import hy`，调用方照常 `from pkg.mod import fn`。
- Hy 编译到 Python AST。对象、异常、迭代按 Python 语义求值。

宏跨模块传递用 `require`，不用 `import`。`import` 在运行期执行，宏在编译期展开。

`(require mod :readers *)` 只引入读器，不把 `mod` 绑进调用方命名空间。调用方要同时 `(import mod)` 才能取模块内对象。

线程宏 `->`、`->>`、`doto` 不在 Hy 核心，来自 Hyrule。每个用到它的模块自己 `(require hyrule [->])`。

## 宏

`defmacro` 的参数只接受 symbol、`[symbol default]`、`/`、`#* args`。keyword 作为字面 Keyword model 传入，不是函数的关键字参数。

模板用 quasiquote：`~` 求值插入一项，`~@` 拼接可迭代值到父级顺序 model。宏在编译期收到 model，收不到运行期对象；要生成对象，就让展开式写出构造它的代码。

宏体引用的普通函数必须在展开时已存在。把这类 helper 包进 `eval-when-compile`（只编译期用）或 `eval-and-compile`（运行期也用）。

同一模块里，宏定义必须出现在调用它的顶层 form 之前。

宏体里 `import` 的模块在调用处不可见。展开式里写模块全路径，例如 `(hy.I.os/path.basename "x")`。

重复插入实参或需要临时变量时用 `hy.gensym` 生成名字。

## 读器

`defreader` 用 `(.parse-one-form &reader)` 读一个 form，返回值必须是 model 或 `None`。读器不能在定义它的同一个顶层 form 里使用。

模型字面量用 `hy.models`：`Expression`、`Symbol`、`String`、`Tuple`、`Integer`。`Symbol` 拒收点号，横线合法；要写带模块路径的全名，用 `hy.read` 读出表达式当调用头。

要给运行期一个模型而不是一层调用，就把它包成 `(quote model)`。`'` 是读取期语法糖，读出的模型与手写 `(quote ...)` 相等。

`HyReader` 提供 `parse`、`parse_one_form`、`parse_forms_until` 等方法，没有 `read`。装载带自定义读器的源码用 `(hy.read-many source :reader reader)`；`reader` 必须用关键字传，位置参数会被当作文件名。

## 求值与时序

函数实参会被求值。要让一段代码留到运行期再算，就显式 quote。

判两个模型是否同形用相等比较。`hy.repr` 给可回读的源码形式，`str` 给调试形式，两者都不是源码原文。

`(try ...)` 是表达式，可直接放在调用实参、`print` 或 `(setx ...)` 里。

`hy.compile` 不存在，用 `hy.compiler.hy_compile`。`hy2py` 会执行编译期代码，只用来核展开，不作构建步骤。

## Hy 语法要点
- 真值写 `True` 与 `False`。`t` 与 `nil` 不是 Hy 真值。
- 标识符参与 mangle，`top-k` 编译为 `top_k`。字符串不参与 mangle。字典键与 `getattr` 参数写外部 Python 名。
- 动态键写 `(dict out #** {name value})`。
- 构造表达式后先绑定实例，再调用方法。

- 属性访问写 `obj.attr` 或 `(. obj attr)`。`(.attr obj)` 是方法调用。
- 取默认值写 `(.get mapping key default)`。`(get mapping key default)` 不是取默认值。
- 切片取尾段写 `(cut seq 1 None)`。`(cut seq 1)` 取的是单个下标。
- `#(...)` 是元组字面量，不是调用。`(tuple a b)` 不接受两个实参，元组写 `#(a b)`。
- 不等写 `(!= a b)`。`not=` 不是 Hy 的运算符。
- 赋值目标可用 `#(a b)` 或 `[a b]`；两种写法都按位置解构。
- 推导式头部的 `[...]` 是子句列表。取值子句写 `value iterable`。`value` 可写 `[a b]` 或 `#(a b)`，如 `(lfor #(a b) items ...)`。
- 方法装饰器写在 `defn` 之后、返回标注之前：`(defn [staticmethod] #^ str f [] ...)`。返回标注写在名字之前：`(defn #^ None method [self] ...)`。
- 泛型标注写 `(get typing.ClassVar str)`。
- 方法调用的实参位置可用 `#*`：`(.format "{}" #* [1])`。
- 链式表达式里用运算符代替 Python 特殊方法：`(/ (mod.col "x") 2)`；幂用 `(.pow expr 2)`。
- f-string 的格式规格前留空格：`f"{value :.1f}"`、`f"{1 :.1f}"` 都成立。Hy 在插值里只读取一个 form。
- `dfor` 末尾写 `#** MAPPING` 可直接展开映射，例如 `(dfor x [{1 10} {2 20}] #** x)`。
- `__name__` 已是字符串，不要加括号调用。

## 可读性

判据：读到某一行时，不必先把读写样板翻译回业务概念。业务顺序就是代码顺序，算式在字面上就是算式。

线性数据变换用 `->` 竖排，一步一行。集合运算、树形求和、条件内嵌改用嵌套形式；`->` 把一行摊成三层的地方不要用。

重复的垂直样板收进 `defmacro`：逐列同一变换、每组同一折叠、字段与渲染串本属一处。宏的参数写业务名，body 写算式，展开式里不留样板。

宏内临时名一律 `hy.gensym`，避免撞调用方的同名局部变量。

外壳也能由读器收掉。例如图规格里每个节点都要 `(fn [依赖...] ...)`，就让 `#dag` 读器按依赖名补形参，节点体只写算式；显式 `fn` 原样保留，留给形参改名之处。

一个宏只收一种形态。宏名读出来就是动作，不要靠注释解释。

改完用 `hy2py` 看展开：展开式应比原式短，且不含多余局部名。

## 改 .hy 后的缓存

`.hy` 模块的字节码缓存在 `__pycache__`。读器宏的展开结果已写进缓存时，删掉源文件里的宏再跑测试仍会拿到旧展开，表现为断言莫名失败而源码看着对。

改 `.hy` 模块或读器宏之后，先删仓库内 `__pycache__`（避开 `.venv`）再跑测试。

## 测试

被测模块是 `.hy`、测试是 `.py` 时不需要收集钩子。包入口写 `import hy` 后，pytest 照常收集 `.py` 测试。

测试文件本身是 `.hy` 时，在仓库根 `conftest.py` 加官方钩子：

```python
from pathlib import Path
import hy, pytest

TESTS = Path.cwd() / "tests"

def pytest_collect_file(file_path, parent):
    if (
        file_path.suffix == ".hy"
        and TESTS in file_path.parents
        and file_path.name != "__init__.hy"
    ):
        return pytest.Module.from_parent(parent, path=file_path)
```

按目录收集，不要把单个 `.hy` 文件直接传给 pytest。直接点名会触发断言改写并报 SyntaxError。必须点名时加 `--assert=plain`。

`.hy` 测试文件同时写 `(import mod)` 与 `(require mod :readers *)`：前者取模块内对象，后者取读器。

断言异常类型前先确认抛在哪一层。读器内抛出的违例是 `LexException`（`SyntaxError` 的子类），不是 `ValueError`；被调用函数抛出的按函数自己的类。

## 覆盖率

coverage.py 采集 `.hy` 的行到数据文件，但报告阶段用 Python 解析器解析 `.hy` 失败，静默跳过该文件。`.hy` 不进报告，也不进 `--cov-fail-under` 的分母。

把生产模块改成 `.hy` 等于让这些模块退出覆盖率守门。动手前先确认这个盲区是否被接受。不接受就写 coverage file tracer 插件；否则不要把「覆盖率绿」当成通过。

`tests/*` 已在 coverage omit 中的项目，测试夹具改 `.hy` 不增加新盲区。

## Python 到 Hy 的初稿

py2hy 按 Python AST 生成 Hy 初稿。初稿保留 `for`、`while`、`return` 与连续 `setv`，并丢弃注释和风格信息。把初稿当语法词典和手改起点，按本文准则改成 `let`、`cond`、`loop/recur` 与推导式。翻译器未实现节点时直接手写对应 Hy 形式。已有 Hy 代码直接按本文重构。用装齐 `hy`、`hyrule`、`packaging` 的解释器运行翻译器。

## 探查不熟语法与项目行为

优先用 hy 自带入口当场求值，不写临时探针文件。短表达式用 `hy -c CMD`；多行表达式用 `hy -` 从标准输入读，二者都自带项目解释器与依赖。一次只问一个判据，只打印结论与关键值。

有 hy-repl MCP 时先启动项目 worker，再调用 eval；未启动时 eval 会拒绝。启动参数传项目根，worker 的工作目录就是项目根。eval 的表达式写 Hy 形式，可一次放多个 form；变量跨 eval 保留。stdout 与 stderr 分开返回，把判据和关键值打印到 stdout。worker 必须能导入项目依赖；若 `import pandas` 报 `ModuleNotFoundError`，先重启 MCP 服务。

同一形状第二次失败时，回本文找该形状，不猜第二个写法。

## 核对

改 `.hy` 前的基线：跑通全量测试，记下通过数与覆盖率。改完后用同一组测试对照行为，重点核宏展开产出的表达式、dataclass 字段与渲染串、夹具数据逐位等价。宏展开可用 `hy2py` 或 `hy.macroexpand-1` 核对。
