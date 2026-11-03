---
name: serena-code-navigation
description: 用 serena 语义工具读代码、查引用、改符号、取类型错。凡需定位函数/类/方法、看调用方、跨文件改名、查 LSP 诊断时用。
---

# serena 代码分析

分析代码先走 serena，不以 grep 起手。`rg` 只用于非代码文本、跨文件字面量、以及 serena 看不见的按名调用（`getattr`、字符串拼出的属性名、模板渲染）；用 rg 时在回复里写一句为什么 serena 覆盖不到。

| 任务 | 工具 |
|---|---|
| 文件里有什么 | `get_symbols_overview` |
| 某个类/函数/方法在哪、长什么样 | `find_symbol`（`include_body: true`） |
| 谁用了这个符号 | `find_referencing_symbols` |
| 这行调用指向哪个定义 | `find_declaration` |
| 这个文件有没有类型错 | `get_diagnostics_for_file` |
| 改一个函数的实现 | `replace_symbol_body` |
| 在符号前后插入 | `insert_after_symbol` / `insert_before_symbol` |
| 跨文件改名 | `rename_symbol` |

## 握手

新会话第一次用 serena 走这三步。`session` 只传给 `activate_project`，其余工具不收。

```ts
const { text } = await extensions.mcp__serena__initial_instructions({});
const session = text.match(/session id is `([^`]+)`/)![1];
await extensions.mcp__serena__activate_project({ project: '/abs/path/to/project', session });
```

`project` 传绝对路径或已注册名。成功回 `The project with name 'xxx' at /path is activated.`，并列出 `Active language servers`。

## 常用调用

参数名：`name_path_pattern`、`relative_path`、`include_body`、`depth`、`substring_matching`。

```ts
// 文件结构：类名 + 子节点
await extensions.mcp__serena__get_symbols_overview({ relative_path: 'src/foo.py' });
// -> {"Class": ["Foo"]}

// 类 + 直接成员（方法名与行号），不取函数体
await extensions.mcp__serena__find_symbol({ name_path_pattern: 'Foo', relative_path: 'src/foo.py', depth: 1 });

// 方法 + 函数体：name_path 用斜杠，不用点
await extensions.mcp__serena__find_symbol({ name_path_pattern: 'Foo/bar', relative_path: 'src/foo.py', include_body: true });
// -> body: "def bar(self, x: int) -> int: ..."

// 不知道全名时按子串搜
await extensions.mcp__serena__find_symbol({ name_path_pattern: 'bar', relative_path: 'src/foo.py', substring_matching: true });
// -> Foo/bar

// 全库搜：不传 relative_path
await extensions.mcp__serena__find_symbol({ name_path_pattern: 'Foo' });

// 谁引用了这个类：按文件分组，含引用行上下文与所在函数
await extensions.mcp__serena__find_referencing_symbols({ name_path: 'Foo', relative_path: 'src/foo.py' });
// -> {"src/other.py": {"File": [...], "Method": [{"name_path": "Bar/__init__", ...}]}}

// 类型错：干净文件回 {}
await extensions.mcp__serena__get_diagnostics_for_file({ relative_path: 'src/foo.py' });
```

行号 0 起。`find_symbol` 的 `relative_path` 传目录即搜该目录。返回值是 `{ content, text, details }`，正文取 `text`。

## 改代码

先取函数体确认边界，再整块替换；改完同一程序里取诊断。

```ts
await extensions.mcp__serena__replace_symbol_body({
  name_path: 'Foo/bar',
  relative_path: 'src/foo.py',
  body: 'def bar(self, x: int) -> int:\n    ...',
});
const diag = await extensions.mcp__serena__get_diagnostics_for_file({ relative_path: 'src/foo.py' });
```

`body` 含签名行；`replace_symbol_body` 只换一个符号，跨文件改名用 `rename_symbol`。

## 一步一程序

一次 `fabric_exec` 里把「结构 → 符号 → 引用 → 改 → 诊断」走完，不把中间结果带回对话。

```ts
const root = '/abs/path/to/project';
const { text } = await extensions.mcp__serena__initial_instructions({});
const session = text.match(/session id is `([^`]+)`/)![1];
await extensions.mcp__serena__activate_project({ project: root, session });

const [overview, refs, diag] = await Promise.all([
  extensions.mcp__serena__get_symbols_overview({ relative_path: 'src/foo.py' }),
  extensions.mcp__serena__find_referencing_symbols({ name_path: 'Foo', relative_path: 'src/foo.py' }),
  extensions.mcp__serena__get_diagnostics_for_file({ relative_path: 'src/foo.py' }),
]);
return [overview.text, refs.text, diag.text].map((t) => t.slice(0, 800)).join('\n---\n');
```

参数写错、返回空、`No active project` 等情形见同目录 `pitfalls.md`。
