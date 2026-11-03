# serena 坑

## 返回 `[]` 不是工具坏了

`find_symbol` 没命中回 `[]`，不抛错。常见原因是 name_path 写法不对。

| 写法 | 结果 |
|---|---|
| `Foo/bar` | 命中（类名 + 斜杠 + 成员名） |
| `Foo.bar` | `[]`，点号不认 |
| `bar` | `[]`，方法要在类名下才命中 |
| `Foo` | 命中，只回类本身 |

改法：点换斜杠；去 `relative_path` 全库搜；加 `substring_matching: true`。

## 参数名写错报的是必填项缺失

把 `name_path_pattern` 写成 `name_path`：

```text
Invalid arguments for extensions.mcp__serena__find_symbol: must have required properties name_path_pattern
```

这是参数名问题，不是 MCP 不可用。照参数表重发即可。

## 未激活也可能查得到

部分工具在没 `activate_project` 时仍能返回结果，所以「能查」不代表会话已就绪；`No active project` 只在部分工具上出现。新会话一律先走握手三步，别靠试。

## `session` 只给 `activate_project`

其余工具传 `session` 会被当未知参数。`initial_instructions` 的正文很长，只取 `session id is \`...\`` 那一段。

## `relative_path` 相对 project 根

不带前导 `/`，不写绝对路径。传目录即搜该目录。写错时表现为空结果，不是报错。

## 干净文件回 `{}`

`get_diagnostics_for_file` 无错时回 `{}`，不是空字符串。语言服务器未就绪时也可能回 `{}`，此时先 `get_current_config` 看 `Active language servers`。

## 一次失败不等于不可用

第一次调用失败就退回 grep 是错的。先按上表改参数重试一次；第二次仍失败才换手段，并在回复里写出换的原因。
