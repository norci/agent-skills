# 坑与实例

皆出自一次 `futures/`（约 25 文件）全量去缩写重构，配「改前 / 改后逐位对拍」。

## 1 命中字符串 / 占位符

- 真例：URL 模板 `KX_URL = ".../kx{d}.dat"` 里之 `{d}`（日期占位）会被当作变量 `d` 改名而成 `kx{daily}.dat`，坏链接。
- 别例：`("m", "DCE", ...)` 之品种码 `"m"`、词元串 `"s"` / `"b"` —— 词边界仍在引号内成立，`sed` 不辨引号。
- **防**：先 `grep -n "['\"][a-z]['\"]"` 与 `grep -n '{\w}'` 列出字符串内单字符，排入 C 类（不改）或手工保护；或不用 `sed` 改短名。

## 2 改名撞名

- `self.d`（Daily 对象）改 `self.daily`，而 `self.daily` 已是 Variant 之 bool 标志（「含须逐日重估之规则否」）→ 后者须另改 `daily_rules`。
- **防**：改名前 `grep -n "\b<新名>\b"` 查占用。

## 3 语义相近之两名互换（最危险）

- `Ledger` 有绝对额 `W`（圆）与比率 `nav = W / w0`（倍数）。改名定为 `equity`（绝对额）与 `multiple`（倍数）。机械替换 `self.book.W → self.book.equity`、`self.book.nav → self.book.multiple` 时，`_step_rules` 里之 `notional = weight * lev * self.book.W` 被写成 `self.book.multiple`（倍数≈1），于是名义≈1 圆、手数取整为 0、净值近乎不动（vol 0.31%、sharpe −7）。对拍（仅对无该规则之变体）未触此路径而漏。
- **防**：① 对拍输入须触所有被改代码；② 一名一改、改后 `pyright` + `grep 旧名` 逐处核；③ 相似名（绝对 vs 比率）改毕逐处读 diff 确认指同一物；④ 无输入可达之路径，逐行人工过。

## 4 验证覆盖不足

- 反例同上：`run_daily(V_BARE)` 触发不了 `_step_rules`（`V_BARE.daily_rules is False`）。全量回测（含 `vt` 档）方暴露。
- **防**：验收清单列「被改函数 → 触发之输入」，逐一勾；缺者查代码或补输入（如跑一含动态杠杆之变体）。

## 5 类型未标注令静态检查失灵

- `Leg.structure: tuple`（裸 `tuple`）→ `Any`，故 `opt_leg.direction`（实际字段仍是 `sgn`）`pyright` 不报，运行时才 `AttributeError`。
- **防**：给容器加具体类型（`structure: tuple[OptLeg, ...]`）；改名后凡 `.attr` 访问之类型不明者，补注解让 `pyright` 兜底。

## 6 rope 覆盖不全

- 实测：`Rename` 改 dataclass 字段 `scarr → scores` 只落了定义所在文件与一个跨文件引用，漏了另两个模块（类型推断不达）；改 `Leg.sgn → direction` 漏了构造关键字 `sgn=` 与数处属性访问（合成 `__init__`）。
- **防**：rope 起手 + `pyright` 抓漏 + 唯一模式词边界替换收尾；通用短名逐处改。

## 7 持久 schema 之迁移

- 代码改读 `SELECT date, end_date, ...`，而库里列仍名 `d1` → `duckdb.BinderException`（非 `CatalogException`，未被既有 `except` 吞，直接炸）。
- **防**：同批 `ALTER TABLE ... RENAME COLUMN d1 TO end_date`；注意写表用「以既有表 schema 为准，富余列弃、缺列补 NULL」者（如本仓 `store._put`），列名不符会**静默弃列写 NULL** 而非报错 —— 更险。
- pickle 缓存：dataclass 字段改名令旧 pickle 失配（属性名不符）→ 须能自动现算重建；本仓之 `fut_cache` 键含源码 mtime，一改自动作废重算，故安全。

## 8 下游未同步

- 对拍器 / 测试引用旧字段（`d.futpx`、`px_at`、`Leg.sgn`），改名后编译不过。
- **防**：`grep -rn` 旧名于 tests / nt / analysis，同批更新能改者；实验目录（约定不保兼容）点名。

## 9 收尾漏改

- 注释 / docstring 里之指针（`见 engine._labcl`、`vol_a`）未随函数 / 字段改名 → 指向不存在之名。
- **防**：末轮 `grep -rn` 全部旧名，**含注释**，逐一改。

## 10 rope 会过界：改 keyword 实参名 / parser 失败

- 真例：局部名 `key` 改名，`rows.sort(key=lambda r: r[0])` 被 rope 改成 `rows.sort(series=...)` ——
  运行即 `TypeError`。`key=` 是 `ast.keyword.arg`（非 Name 节点），rope 仍按字符串改了它。
- 别例：某源文件 rope 自带 parser 报 `MismatchedTokenError`（`ast` 能正常解析），rename 直接中断。
- **防**：作用域内之局部名改用 `scripts/ast_scope_rename.py`（只动 Name/arg/Attribute）；
  rope 只用于跨模块之全局名。每批改完 `git diff` 看 keyword 实参是否被动过。

## 11 非 Name 载体漏改

- `ast` 与 rope 皆按「符号」改，故下列不会被改，须另 grep：
  `__all__` 里的字符串（`readers.__all__` 曾留 `"num_col"`）、`TypeVar("T")` 之首参、
  `global X` / `nonlocal X`（名字存于 `ast.Global.names`）、`except Exception as e` 之 `e`、
  格式串占位符 `{d}`、SQL 列名。
- **防**：AST 器已覆盖 `global` / `except as` / def 名；余者末轮 `grep -nE "__all__|TypeVar\(|global |\{[a-z]\}"` 逐处核。

## 12 非 ASCII 源：AST 列偏移是 utf-8 字节

- 证状：中文注释 / 变量所在行，用 `ast` 的 `col_offset` 直接当字符列去切片，切偏（若含 `σ β` 等更甚），
  rope 会抛「不可解析」或改到隔壁字符。
- **防**：`char_col = len(line.encode("utf-8")[:byte_col].decode("utf-8"))`；`scripts/ast_scope_rename.py` 已内建。

## 13 dataclass 字段：声明是裸 Name，用是 Attribute

- 证状：`Selector` 的 `long_col: np.ndarray = field(init=False)` 是**裸 Name**，
  而 `self.long_col` 是 **Attribute**。只按 name 改 → 声明未动、用到不存在字段；
  只按 attr 改 → 声明未动，字段变孤儿（pyright 不报，因新名是动态写入）。
- 另：在**方法**作用域里改 `self.x` 是空改（方法若未绑 `x`，符号不在该方法作用域）；
  须以**类**为作用域改 attr。
- **防**：字段改名 = 「类作用域 kind=name」+「类作用域 kind=attr」两条；改后访问该字段处逐一 `grep`。

## 14 改名撞名：撞入既有参数

- 真例：`_next_listed(bars, month: str)` 内 `y, m = int(month[:4]), int(month[4:])`，
  把 `y,m` 改成 `year,month` 后，`month` 既是 str 参数又被赋 int —— pyright 报
  `int is not assignable to str`，运行时也会静默覆盖。
- **防**：撞名检查不只看新名是否已被占用，还要看**本作用域既有参数 / 局部**；
  改名撞入时应改「既有者」（此处把 str 参数改 `year_month`），而非硬塞。

## 15 对拍基线被「已迁移之库」挡住

- 证状：改前代码读旧列名 `d1`，而库已被 `RENAME COLUMN` 迁成 `end_date` →
  `duckdb.BinderException`，无法跑基线。
- **防**：`cp` 一份库，在副本内把列名**反迁**回旧名（`ALTER TABLE t RENAME COLUMN end_date TO d1`）；
  置隔离缓存根（设 `XDG_CACHE_HOME` 之类，令缓存目录与主库皆指向副本）跑改前代码；
  缓存键含 mtime，两树各写各的，互不污染。对拍毕删副本与临时缓存根。

## 16 接管半成品重构

- 证状：工作区已有一轮未提交改名（部分 `git add`、部分未），pyright 报一堆 `Cannot access attribute`，
  且 `store._put` 之「富余列弃、缺列补 NULL」使 `segments` 仍写 `d1` 而库列 `end_date` —— **静默写 NULL**（见 7）。
- **防**：① `pyright` 错误清单即「已改而未及之处」之台账；② `git diff HEAD` 看改名进行到哪一步；
  ③ 先补齐调用点使编译通过，再跑对拍确认未顺手改错；④ 显式核「写端 dict 键 vs 库列名」——别信类型系统。

## 17 缓存 / 序列化之参数名亦属 schema

- 证状：缓存键与 pickle 载荷里存了参数名（如 `key_of(fn=..., win=..., thr=...)`）。
  把参数名改成 `window/threshold`，键全变 → 旧缓存全 miss。
- 影响与处置：本仓键含代码 mtime、miss 即现算，故只是白算一次，安全；
  但若旧缓存不可重建（含外部产物），则参数名须当作持久 schema（见 7）对待，或另留兼容读旧键。

## 18 换表示：只扫消费函数名，漏访问模式

- 真例：合约日线与成交量原为裸元组 `(dates, values)`，加一组自由函数（`price_at` / `volume_at` / `tradable`）
  消费之；重构时归为 `SeriesBook` 类（`last_at` / `exact_at` / `tradable`）。改名时按**函数名** grep、
  改了全部调用点，唯独漏了某处直接下标：`record = books[prefix].get(contract); record[0].searchsorted(...)`
  —— 运行时方炸 `'SeriesBook' object is not subscriptable`（该处只在不常跑之路径上）。
- **防**：换表示先列「旧表示支持、新表示不支持之操作」——`x[0]` / `a, b = x` / `x[key]` / `len(x)` /
  `x in y` / 迭代 —— **逐个 grep 全项目**。函数名只是消费方式之一，不是全集。
- 补：换表示后**重建旧表示之 pickle 缓存**（键含源码 mtime 者自动作废，否则须显式点名）。

## 19 同一概念之第二实现

- 真例：`scores.continuous_close_at`（docstring：「该合约当日或之前之最后收盘价」）与新类之
  `SeriesBook.last_at` 逐行同义，换表示时未扫到 —— 留下两个真相源，改一处不知另一处。
- **防**：换表示时按**语义** grep（docstring 措辞、注释短语），非仅标识符；同义者一并归并。

## 20 静态检查之 include 洞

- 证状：`pyrightconfig.include` 只列 `strategy/futures/common`，而 `nautilus/` 与 `tests/` 从未被查。
  其下两处硬伤（调用点参数类型不匹配）一路不现 —— 每轮「pyright 0 errors」皆真，却与彼二目录无关。
- **防**：改毕先核 `include` 是否覆盖**所有被改目录**；跑 pyright 之目录清单须与 `include` 一致，
  否则「过了」是假象。新增目录即入 `include`。

## 21 删「死」导出破下游

- 真例：`readers.py` 从 `util` 导入 `numeric_column` 纯为再导出（本包内无人用，仅在 `__all__` 里挂着），
  重构时随手清掉 → `analysis/` 下一脚本恰从 `readers` 取它，直接 `ImportError`。
- **防**：删任何导出 / 符号前 `grep -rn` 全项目，**含** analysis / experiments 等「不保兼容」目录；
  「本包内无人用」≠ 无人用；不保兼容者亦须点名交付，不得默删。

## 22 勿为类型检查器扭曲代码

- 证状：pandas DataFrame 过 numpy ufunc（`np.log` / `np.exp`）时，桩推 `ndarray`，
  于是 `df.diff()` 之后继操作报 `Cannot access attribute`。为消此报，易生两种坏改：
  ① `pd.DataFrame(np.log(df.to_numpy()), index=…, columns=…)` 绕 numpy 回转；
  ② `cast(pd.DataFrame, …)` 到处包。二者皆为类型检查器改**运行时无问题**之代码。
- 根因：numpy roadmap 尚未支持 `__array_ufunc__` 之类型推断；`df.pipe(np.log)` 同桩（只是转发，
  返回型由 `np.log` 定）—— 桩层面无解。
- **防**：**上游参数不标**（类型退为 `Unknown`，pyright 不深查），代码保持原样。报错之开关在**链的起点**：
  给起点参数加标注，反把下游 ufunc 之桩缺陷引爆。**代码第一，检查器第二**。
