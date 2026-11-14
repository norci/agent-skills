---
name: batch-processing
description: 把一条任务链放进一次批处理：能用程序表达的写成一份 Lisp 程序；由 MCP 工具构成的，把整条链的调用在同一轮里发完。需要多次取数、改文件或对多个目标做同一件事时用。
---

# 一条链就是一次批处理

一条链先写步骤清单，一步一行标出输入与产出，再整条链一次走完。载体有两种，按链的构成选：

- 能写进程序的，写成一份 Lisp 程序，一次 `lisp.eval` 发出。
- 由 MCP 工具构成的，把整条链的调用在同一轮里发出：无依赖的同批并发，有依赖的按序串行。

## 判据：一轮走完整条链

本轮要做的事能否写成一条链？

- 能，就在这一轮把整条链走完；中途只把上一步的返回值当下一步的输入，不把控制权交回用户。
- 不能，说明缺的是哪一步的语言判断（用户意图、代码语义、审美取舍）。把该判断说清，并在同一轮里把判断之后的动作一并写进链。

「一次发出」指整条链在同一轮交付，不是一次只发一个 tool call。串行调用是链内的次序，不是轮次的边界；一轮可以含任意多个调用。

中间结果不进入对话。要看某一步的结果，就把判据写进链里，让它只回结论；不要为了看原始输出而结束本轮。

## 清单写进程序

```text
读 A               -> 文本
判 A 是否含 X      -> 布尔
若 否: 读 A'       -> 文本
写 A'              -> 退出码
复核 A' 是否含 X   -> 布尔
```

清单留在这一轮的推理里，不另发 tool call 确认它。`let*` 里前面的绑定就是后面的输入，步骤先后不需要轮次。

## 先定义小函数，再拼主链

一条链的程序超过约 20 行，或同一段逻辑第二次出现，先把片段定义成小函数，再在主链里调用。每个 helper 只做一件事，输入输出落在参数与返回值上；主链只写数据与次序。

```lisp
(defun read-text (path) ...)
(defun write-text (path text) ...)
(defun replace-once (text old new) ...)
(defun replace-pairs (text pairs) ...)
(defun edit-pairs (path pairs) ...)
```

helper 与主链同属一条链：第一次用时把 helper 定义和主链放进同一次 `lisp.eval`；helper 已在持久 REPL 里，后续主链直接调用。不要为了复用 helper 把主链拆成多轮。

改一处只重定义那个 helper，不必重写整条链。主链因此只占十几行，生成时不容易漏括号，出错时也只需看一个 helper。

## MCP 链的批法

- 无依赖的查询同批发出。
- 有依赖的查询与改动按序发出，仍在同一轮：拿到上一步的返回值后立刻发下一步，不结束本轮。
- 改状态的调用串行发出，指同一批内不得并发；串行不改变它们同属这一轮。
- 只有需要用户裁决、缺输入或需要授权时，才结束本轮；「想先看一眼结果」不是结束本轮的理由，把要看的东西写成链里的判据。

## 每条链只回结论与红项

程序返回 `(:conclusion ... :evidence ...)`：结论是每条判据的布尔结果，证据只放红项的原始输出。MCP 链与 shell 链同此：只把每条判据的结论写进下一步，不逐条复述原始输出；红项自带它需要被看见的原文。

例如「先看 diff 再决定是否提交」：diff 是否为空、是否含未预期的文件都是判据，写进链里一次返回结论，不要分轮看 status、diff、log。

## 失败与重算留在链里

调用失败时记下错误字符串，记进该项，继续下一条；判据不通过时在同一轮里换判据或换输入重算。返回时仍有红项，下一轮从红项起步。

## 并发

无依赖的段落同批派出。Lisp 程序里用 `sb-thread:make-thread` + `sb-thread:join-thread`；MCP 链里把无依赖的调用放进同一条消息。两者都只改变链内那一段的形状。

`lparallel` 在 worker 里不可用，`bordeaux-threads` 与 `sb-thread` 可用。

## 例子

读仓库状态、判有无改动、有则取差异统计。

```lisp
(let* ((run (lambda (command)
              (handler-case
                  (list :ok (uiop:run-program command :output :string
                                              :error-output :output
                                              :ignore-error-status t))
                (error (e) (list :error (format nil "~a" e))))))
       (status (funcall run '("git" "status" "--short")))
       (dirty (and (eq (first status) :ok)
                   (plusp (length (second status)))))
       (diff (and dirty (funcall run '("git" "diff" "--stat")))))
  (list :conclusion (list :dirty (not (null dirty))
                          :diff-ok (if dirty (eq (first diff) :ok) :skipped))
        :evidence (remove nil
                          (list (unless (eq (first status) :ok)
                                  (cons :status status))
                                (when (and dirty (not (eq (first diff) :ok)))
                                  (cons :diff diff))))))
```

无依赖的段落把中间那一段换成任务列表：逐个 `sb-thread:make-thread` 派出，`mapcar #'sb-thread:join-thread` 收回。
