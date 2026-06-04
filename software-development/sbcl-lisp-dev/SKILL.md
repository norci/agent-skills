---
name: sbcl-lisp-dev
description: AI agent 使用 SBCL 开发 Common Lisp 程序。核心为 REPL-Driven Development——逐一定义、即时求值、增量验证。涵盖心法、工具集成、操作規律、五步測試、調試診斷、跨邊界陷阱。触发条件：涉及 Lisp/SBCL 编码、S-expression 求值、REPL 会话、Quicklisp 包管理、CLOS 设计。
tags:
 - lisp
 - sbcl
 - repl-driven
 - common-lisp
 - incremental-development
---

# SBCL Lisp 開發之道

## 第一戒 勿走批次徑

> ❌ 生成一大段程式 → 寫入檔案 → 執行一次 → 出錯 → 修改 → 再執行

凡「生成大段程序 → 写入文件 → sbcl --script 执行 → 出错再改」此径，皆 C/Python 之思维误植于 Lisp 之境。

**此徑於批次語言尚可，於 REPL 環境則為惡疾**：
1. 每次執行皆從零開始，前序調適結果不可累積
2. 錯誤定位困難（全量輸出煙霧彈）
3. Lisp 之多層次系統（macro → function → method）無法逐層驗證

Lisp 程序之开发，当以 **REPL 为唯一运行时**，而非把 Lisp 當批次腳本語言用。

### 正確路徑

```text
定義 → 求值 → 測試 → 微調 → （循環）
```

每次僅產生單一 S-expression（一函數、一巨集、一變量綁定），賦值為定義即求值，觀察回饋，再進下一步。絕非一口氣生成數百行程式、寫入檔案、執行一次、出錯再改。

### Agent Imperative Checklist

- **每次**僅輸出一至兩個 S-expression（function definition / macro / test）
- 於 REPL 會話中施用 `(eval ...)` 或調用 SBCL stdin 逐節傳入
- 觀察返回值、錯誤條件、副作用，確認後再進下一步
- 若出錯，不下結論「邏輯有誤」，先診斷是定義層面還是測試層面
- 階段性收束時，方將已調妥之 definition 彙入 `.lisp` 檔案保存

## 第二戒 極小步進

每次僅處理一個 S-expression：

- 单一定义：`(defun foo (x) ...)`、`(defmacro bar ...)`、`(defvar *x* ...)`
- 單一測試：`(foo 42)`
- 單一導入：`(ql:quickload :some-package)`

輸入後即刻觀察返回值、錯誤信號、副作用。確認無誤，方進下一步。

## 第三戒 增量覆蓋

Lisp 允許同一名稱重複定義。新定義自動取代舊定義，REPL 內存儲狀態不丟失。Agent 應當利用此特性：

```lisp
(defun helper (x) 0) ; 初版
; 求值測試 OK
(defun helper (x) (* x 2)) ; 二版 — 直接覆蓋，無需刪除舊碼
; REPL 狀態已更新
```

## 第四戒 狀態持久化策略

SBCL 內存 heap 中所有定義可傾dump為核心映像：

```lisp
(save-lisp-and-die "my-app.core")
```

下次啟動：

```bash
sbcl --core my-app.core
```

避免每次啟動重載全盤。亦可將已調妥之 definition 按 package/模組分文件保存，用 `(load "file.lisp")` 增量加載。

### SBCL Core Image 適用場景

花長時間組裝之大環境（大量 macro、package、load 的 library）尤其適合。開發中途若新增依賴，於 REPL 中直接 `(ql:quickload :new-dep)`，無需重啟。

## 第五戒 工具擇選

| 工具 | 用途 | 對應 Agent 操作 |
|------|------|-----------------|
| SBCL REPL (直接) | 已啟動的交互會話 | `sbcl` 後續以 `--eval` 或 stdin 逐節傳入 |
| SLIME (Emacs) | `C-c C-c` 傳送段落至 REPL 求值 | 若環境有 SLIME，優先透較其 swank 接口互動 |
| SLY | SLIME 替代品，API 類似 | 同上 |
| cl-mcp-server | Agent 透過 36 項具名工具與持久 REPL 互動 | 見下方「工具集成」章節 |
| Quicklisp | 套件管理 | `(ql:quickload :pkg-name)` |

### Emacs + SLIME/SLY 數據流

| 操作 | SLIME 鍵 | SLY 鍵 |
|------|----------|--------|
| 傳送前一個 definition | `C-c C-c` | `C-c C-c` |
| 傳送區域 | `C-c C-r` | `C-c C-r` |
| 跳到前一個定義 | `C-c C-u` | — |
| 跳到 REPL | `C-c C-z` | `C-c C-z` |

**要點**：SLIME/SLY 傳送的是 definition 層級，而非檔案層級。Agent 若透過工具鏈操作，須**按 definition 粒度**逐次求值。

## 五步測試法

每定義一函數，至少跑五 Regiment：

1. **典型輸入**：正常使用情境
2. **邊界值**：空 list、零、負數、極大值
3. **錯誤輸入**：類型錯誤、nil、不符合前提條件者
4. **與既有函數的組合呼叫**：验证不破壞既有逻辑
5. **巨集**：驗證 macroexpansion 結果

### Immediate Inline Test

```lisp
(defun reverse-list (lst)
 (reduce (lambda (acc x) (cons x acc)) lst :initial-value nil))

; Agent 立即驗證
(reverse-list '(1 2 3)) ; => (3 2 1)
(reverse-list '()) ; => NIL
```

## 調試與診斷

出錯時，**先查定義層面**（語法、作用域、macro expansion）→ 再查測試層面（呼叫參數、前提條件）。

### 診斷工具

```lisp
; 看巨集實際展開為何
(macroexpand-1 '(my-macro args ...))

; 察看上一個錯誤詳情
(describe-last-error) ; via cl-mcp tool

; 取得調用堆疊
(get-backtrace :max-frames 10) ; via cl-mcp tool
```

### SBCL 命令行中的等效作法

若無 SLIME/SLY，可用 `--non-interactive --eval` 逐條傳送：

```bash
sbcl --non-interactive --noinform \
 --eval '(load "init.lisp")' \
 --eval '(defun square (x) (* x x))' \
 --eval '(format t "~a~%" (square 5))'
```

但此仍為批次模式。交互式開發優先用 `rlwrap sbcl` 或 SLIME/SLY。

## REPL 代碼風格指南

- 每行以一個 S-expression 為單位
- 定義與其測試**不混寫**：定義行後直接跟上測試呼叫
- 使用 `#+sbcl` read-time conditional 隔絕實現特定代碼
- 用 `defparameter` / `defvar` 建立可視狀態；用 `defconstant` 固定不會變之物
- `defmacro` 之後**務必** macroexpand 驗證

## 與其它工具之邊界

**`mcp_lisp_*` 工具與 `terminal` 之 SBCL 各自獨立，互不共享定義**：

- `mcp_lisp_load_file` 載入之 package、函數、巨集，於 `terminal` 另起的 SBCL 程序中**完全不存在**
- 反之，`terminal` 中定義之物，亦不見於 `mcp_lisp_*` 會話

**同一 session 內混用二者會導致「已載入但查無符號」之幻覺式錯誤**。

### 策略

- 擇一使用
- 若有必要切換，先於新實例中 `load` 同一批 `.lisp` 檔
- 發現 `"symbol not external in package"` 或 `"undefined function"` 時，優先檢視是否跨了工具邊界，而非繼續調試邏輯

## MCP Server Programmatic Testing (cl-mcp-server)

When testing an MCP server built on `cl-mcp` from SBCL, use the registry API directly instead of stdio JSON-RPC:

```lisp
(let* ((server (cl-mcp:make-server :name "test" :version "0.3.0"))
 (session (cl-mcp-server.session:make-session)))
 (cl-mcp-server.session:with-session (session)
 (cl-mcp-server.tools:define-builtin-tools server session)
 (let ((registry (cl-mcp:mcp-server-tools server)))
 ;; 3-arg: registry, name (string), args (alist)
 (cl-mcp.tools:call-tool registry "evaluate-lisp"
 (list (cons "code" "(+ 1 2 3)"))))))
```

### Pitfalls

- `cl-mcp.tools:call-tool` is exactly **3 arguments**: registry, string name, args-alist. Omitting name causes UNDEFINED-FUNCTION at dispatch, not a clean arity error.
- `cl-mcp.tools:list-tools` returns tool **definition structs**, not strings. Use `(mapcar #'tool-name (list-tools registry))` to enumerate names.
- `cl-mcp:mcp-server-tools` extracts the registry from a server object — it is not globally accessible; pass explicitly.
- In non-interactive mode, use `cl-mcp:run-server` with `:input` and `:output` streams for full JSON-RPC protocol testing (see integration-tests.lisp pattern).
- For quick smoke tests, wrap tool calls in `with-session` and terminate with `(sb-ext:exit :code 0)`.

## Agent 實操 Protocol

```text
1. 啟動 SBCL REPL（非腳本模式）
2. 生成第一個 S-expression（通常為 import/defvar）
3. 經由 terminal/stdin 送入 REPL
4. 解析輸出：nil / 錯誤信號 / 實際返回值
5. 若錯誤：診斷是語法錯誤、未定義符號、還是邏輯錯誤 → 修正後重送同一 expression
6. 若成功：生成下一個 expression（下一函數或測試）
7. 回到 3
```

## 禁忌

- **不一次性生成超出一函數**：函數可以互相呼叫，但應分開定義和求值
- **不把 REPL 作為日誌**：每步求值結果都應被觀察和處理，而非覆蓋后曠棄
- **不寫完再跑**：缺少「定義 → 求值 → 測試」循環的 Lisp 程序，等於未經編譯的 C 源碼

## 與其它 Agent 框架之差異

編譯型語言（Go、Rust）或批次語言（Python）可「生成→運行一次→修改」是因編譯錯誤分離且運行時隔離。**Lisp 之特性正在打破此壁壘**：REPL 即運行時，定義即執行。AI Agent 工作流必須與此特性對齊，而非輾壓特性去適配舊有批次流程。

## 將 cl-mcp-server 接入 Hermes Agent

Hermes 透過 `config.yaml` 內 `mcp_servers.<name>` 鍵組裝 stdio MCP server。對 cl-mcp-server 而言，只有 **`args` 必須是 YAML list** 這一條約束。

### 正確的 Hermes config snippet

```yaml
mcp_servers:
 lisp:
  command: sbcl
  args:
   - "--script"
   - "/home/josephx/code/cl-mcp-server/run-server.lisp"
  timeout: 120
```

### 關鍵約束

- `mcp_servers.<name>.args` **必須是 list**，不可寫成 `'[ "--script", "..." ]'`（單字串）。違反時 Hermes MCP 載入器會拋出 `Input should be a valid list [type=list_type, input_type=str]`，工具全部無法發現。
- Hermes preferred CLI 路徑為 `hermes mcp add lisp --command sbcl --args --script /path/to/run-server.lisp`；但 Hermes v0.15.1 的 `mcp test` 子命令有 bug（`servers[name]` 在 key 存在時仍回傳 None），**目前以直接改 YAML 再 `hermes mcp test` 驗證最可靠**。

### 驗證方法

```bash
hermes mcp test lisp # 預期：Connected + 'Tools discovered: 37'
hermes mcp list # 檢查表格中出現 lisp / sbcl / all / enabled
```

### 第一次使用時的安全限制

- Hermes 拒絕以 `patch` 直接修改 `~/.hermes/config.yaml`，必須用 `sed` / Python / `hermes config set`。路徑確定時短腳本改 YAML 比 `hermes config set mcp_servers.lisp.args` 可靠。
- 任何 config 改動後，`hermes mcp test` 或新 session 才會生效，不需要重啟 gateway。

## Key Tool Signatures

| Tool | Required args | Optional args |
|------|--------------|---------------|
| `evaluate-lisp` | `code: string` | `package: string`, `capture-time: bool` |
| `compile-form` | `code: string` | — |
| `validate-syntax` | `code: string` | — |
| `describe-symbol` | `name: string` | `package: string` |
| `apropos-search` | `pattern: string` | `package: string`, `type: string` |
| `configure-limits` | — | `timeout: integer`, `max-output: integer` |
| `quickload` | `system: string` | — |
| `load-system` | `system: string` | — |
| `load-file` | `path: string` | `compile: bool` |
| `profile-code` | `code: string` | `mode: string` (cpu/wall/alloc) |
| `get-backtrace` | — | `max-frames: integer` |
| `telos-feature-intent` | `feature: string` | — |
| `time-execution` | `code: string` | `package: string` |

## Common Patterns

### PATTERN-001: Validate Before Evaluate

Use `validate-syntax` before saving code to files:

```lisp
; via cl-mcp tool call
{"code": "(defun foo (x)\n (* x x))"}
→ "Syntax OK"
```

Does not evaluate — safe for untrusted/large code.

### PATTERN-002: Incremental Definition

```lisp
; Step 1
(defun square (x) (* x x)) → "=> SQUARE"
; Step 2
(square 7) → "=> 49"
; Step 3: only write to file when working
```

### PATTERN-003: Debug Last Error

When evaluation returns `[ERROR]`:

```lisp
; via cl-mcp tool
describe-last-error → detailed error with restarts
get-backtrace :max-frames 10 → stack trace
```

### PATTERN-004: Load External System

```lisp
; Check if available
(quicklisp-search :pattern "alexandria")
; Load it
(quickload :system "alexandria") → "Successfully loaded: ALEXANDRIA"
; Verify
(alexandria:flatten '(1 (2 3) (4 (5)))) → "=> (1 2 3 4 5)"
```

### PATTERN-005: Profile Hot Code

```lisp
(time-execution :code "(loop repeat 1000000 sum 1)")
→ "Real time: 0.012s, GC time: 0.000s, Bytes: 0"
; For deeper profiling
(profile-code :code "(loop repeat 1000000 sum 1)" :mode "cpu")
```

## 常見陷阱速查

| 陷阱 | 症狀 | 處理 |
|------|------|------|
| Stale session | 既有工作查無符號 | `reset-session` |
| No timeout | 無窮迴圈掛起 | `configure-limits {"timeout": 30}` |
| Large output | 回應被截斷 | `configure-limits {"max-output": 50000}` |
| Missing package | `No package error` | `evaluate-lisp` 附 `"package": "cl-user"` |
| `load-system` vs `quickload` | System not found | 用 `quickload` 載 Quicklisp 系統；`load-system` 僅限 ASDF-registered |
| Telos tools on unloaded system | 空結果 | 先 load 該系統；telos 在系統未載入時返回空 |
| Macro redefinition | 調用處使用舊展開 | 巨集變更後，重載相依檔案 |
| **跨工具邊界** | `mcp_lisp_*` 與 `terminal` SBCL 定義互不可見 | 擇一使用；切換時先 `load` 同一批 `.lisp` |

## 目錄組織之律

- **源碼根**：`~/code/<project>/`
- **Quicklisp 本地項目**：`~/quicklisp/local-projects/` 內以 symlink 指向 `~/code/<project>/`
- **Quicklisp 本體**：`~/quicklisp/`（上游預設 layout，不動）
- **禁令**：`~/` 下不得散落 `.lisp`、`.sexp`、`setup.lisp`、`asdf.lisp` 等 Quicklisp 安裝臨時文件，安裝完成後一律清凈

### 四庫 Symlink 範例

```bash
git clone https://github.com/quasi/opsis.git ~/code/opsis
git clone https://github.com/quasi/telos.git ~/code/telos
git clone https://github.com/quasi/cl-mcp.git ~/code/cl-mcp
git clone https://github.com/quasi/cl-mcp-server.git ~/code/cl-mcp-server

ln -sf ~/code/opsis ~/quicklisp/local-projects/opsis
ln -sf ~/code/telos ~/quicklisp/local-projects/telos
ln -sf ~/code/cl-mcp ~/quicklisp/local-projects/cl-mcp
ln -sf ~/code/cl-mcp-server ~/quicklisp/local-projects/cl-mcp-server
```

驗證：`sbcl --load ~/quicklisp/setup.lisp --eval "(ql:quickload :cl-mcp-server :silent t)"`

## cl-mcp-server 結構速查

| 檔案 | 行數 | 角色 |
|------|------|------|
| `src/packages.lisp` | ~210 | 6 個子 package 定義 |
| `src/server.lisp` | 12 | 膠水：`make-server` → `define-builtin-tools` → `run-server` |
| `src/tools.lisp` | ~870 | 36 個 MCP tool 的 register-tool 調用 |
| `src/evaluator.lisp` | ~380 | 核心 REPL：output capture / timeout / result struct |
| `src/session.lisp` | ~110 | 有狀態 session（definitions / loaded-systems / last-error） |
| `src/introspection.lisp` | ~700 | describe-symbol / apropos / class-info / macroexpand |
| `src/asdf-tools.lisp` | ~350 | ASDF / Quicklisp 整合 |
| `src/profiling-tools.lisp` | ~280 | sb-sprof / deterministic profiling |
| `src/telos-tools.lisp` | ~400 | Telos feature / intent 查詢 |
| `src/paren-tools.lisp` | ~350 | 括號配對查找 |
