---
name: lisp-mcp-smoke-test
description: 凡需验证 cl-mcp-server Lisp MCP server 之可用性，或诊察 37 项工具注册状态，即当加载。
version: 0.1.0
---

# Lisp MCP Smoke Test

## 触发

- 启动/重启 Hermes 后验证 `lisp` MCP server 是否就绪
- 诊察 37 项工具是否完整注册
## 排障 `hermes mcp test lisp` 失败时
 
- `Package X does not exist` 很少是括号错误，通常是 `X` 库未在 `.asd` 的 `:depends-on` 中声明。先查 ` SYSTEMS` + `apropos`，不改代码前别断言语法问题。
- 若工具文件引用 `cl-json`、`quri` 等 Quicklisp 库，务必对应在 `.asd` 维护依赖链；缺一项即连带整块引用区失效。
- 远端 `mcp_lisp_*` tool 运行于**隔离 SBCL 会话**，不继承本机 `ASDF` source-registry。`load-system` 可能找不到本地 `.asd` 文件，即使文件真的在磁盘上。`list-local-systems` 返回的列表仅反映该隔离会话所知的系统。
   - 若 `.asd` 已补依赖但 session 仍找不到系统，可写 `~/.config/common-lisp/source-registry.conf` 注册项目根，或在完整本机 REPL 用 `(ql:quickload :your-system)` 验证。

### 10. `split-string` 需引入第三方库

`uiop:split-string` 是 ASDF/UIOP 工具，在非 Quicklisp 环境下可用，但需确保 ASDF 已加载。若无，自行以 `loop` 分拆。

### 11. JSON 解析 — 避免包依赖

在 `evaluate-lisp` 中解析 JSON 时，不要使用 `json:decode` 或 `jzon:parse`，因为 SBCL MCP session 的 Quicklisp 加载状态不可控。用基础字符串搜索解析：
```lisp
(let ((raw "..."))
  (loop for i from 0 below (length raw)
        for c = (char raw i)
        when (and (char= c #\") 
                  (or (zerop i) (char= (char raw (1- i)) #\{) 
                      (char= (char raw (1- i)) #\,)))
        collect ...))
```

### 12. `car (last parts 2)` 取倒数第二元素

`(first (last list n))` 返回从倒数第 n 个元素开始的子列表，而非单个元素。需用 `(first (last list 2))` 取倒数第二，`(car (last list))` 取最后一个。

### 13. `uiop:subdirectories` 返回值与遍历递归

`uiop:subdirectories` 返回路径名列表，可在 `labels` 递归函数中安全使用。递归遍历目录树时，当心 `namestring` 长度截取——`(subseq full (length base))` 可取得相对路径。

### 14. 路径名格式与 `namestring`

`merge-pathnames "SKILL.md" sub` 生成路径名，用 `probe-file` 检查存在性。`namestring` 返回字符串表示。在不同 MCP 调用之间路径名格式保持一致，但注意 trailing `/` 的有无。

## `evaluate-lisp` 增量开发陷阱（重要）

`evaluate-lisp` 每次调用是**独立编译单元**，以下陷阱会导致开发受阻：

### 1. `defstruct` 生成函数不可见

在同一 `evaluate-lisp` 调用中，`defstruct` 生成的 `make-xxx`、`xxx-slot` 函数在编译时不可见。后续代码引用它们会报 `UNDEFINED-FUNCTION`。
- **解决**：将 `defstruct` 定义和使用分到不同 `evaluate-lisp` 调用；或用 plist + 普通函数替代结构体

### 2. `cond` 分支顺序——`vectorp` 在 `stringp` 之前

CL 中字符串是 `(VECTOR CHARACTER)`，`(vectorp "hello")` 返回 `T`。若 `cond` 中 `vectorp/listp` 在 `stringp` 之前，字符串会被误判为 vector 并进入 `dolist` 分支。
- **解决**：`stringp` 分支必须放在 `vectorp`/`listp` 之前

### 3. `format` 字符串中的引号

`evaluate-lisp` 通过 JSON 传递代码，`\"` 在 JSON 中转义后可能被 Lisp 读取器误解。`format stream "~a\"~a\"~%"` 会解析错误。
- **解决**：用 `(code-char 34)` 生成引号字符，`~c` 指令输出：`(format stream "~a~c~a~c~%" prefix (code-char 34) data (code-char 34))`

### 4. `setf` 多参数括号

`(setf (gethash k1 v1) val1 (gethash k2 v2) val2)` 在 `evaluate-lisp` 中可能因括号不匹配报错。
- **解决**：分开写每个 `setf`

### 5. `ql:quickload` / `asdf:load-system` 不可用

在 `evaluate-lisp` 中无法加载 ASDF 系统。
- **解决**：先用 `mcp_lisp_load_system` 在 server 进程中加载，再在 `evaluate-lisp` 中使用。或在同一调用中先 `(load quicklisp-setup)` 再 `ql:quickload`
  - 能用 MCP 确认依赖声明的唯一迹象：`validate-syntax` 返回 *无* `Package X does not exist` 错误。

## 前置

- SBCL 与 Quicklisp 已就绪（`sbcl --load ~/quicklisp/setup.lisp`）
- `~/quicklisp/local-projects/` 软链：`cl-mcp`、`cl-mcp-server`、`opsis`、`telos`
- Hermes `config.yaml` 中 `mcp_servers.lisp.args` 为 YAML 列表，非字符串

## 用法

```bash
cd /home/josephx/code/agent-skills/hermes/lisp-mcp-smoke-test/scripts
sbcl --noinform --load smoke.lisp
```

## 脚本说明

脚本顺序调用 6 项具代表性工具，验证注册、求值与回传：

1. `evaluate-lisp` — 基本求值 `(+ 1 2 3)`
2. `get-usage-guide` — 文档回传
3. `validate-syntax` — 语法检错 `(+ 1 2 (`
4. `match-paren` — 括号匹配
5. `describe-symbol` — 符号内省 `CAR`
6. `configure-limits` — 超时配置查询

全部通过即表示 37 项工具可被 Hermes 正常调用。
