---
name: batch-processing
description: 把一条任务链的全部操作写进一个 Lisp 程序，一次调用走完取证据、判据、再取、动作、复核。需要多次取数、改文件或对多个目标做同一件事时用。
---

# 一个程序即一条链

一条链就是一份 Lisp 程序：先写步骤清单，一步一行标出输入与产出，再把整份清单落进同一个程序，一次发出。

## 判据：一轮只发这一个 tool call

本轮要做的事能否写成程序？

- 能，就只发这一份，中途不回头看输出。
- 不能，说明缺的是哪一步的语言判断（用户意图、代码语义、审美取舍）。把该判断说清，并在同一轮里把判断之后的动作一并写进程序。

## 清单写进程序

```text
读 A               -> 文本
判 A 是否含 X      -> 布尔
若 否: 读 A'       -> 文本
写 A'              -> 退出码
复核 A' 是否含 X   -> 布尔
```

清单留在这一轮的推理里，不另发 tool call 确认它。`let*` 里前面的绑定就是后面的输入，步骤先后不需要轮次。

## 读数只回结论与红项

程序返回 `(:conclusion ... :evidence ...)`：结论是每条判据的布尔结果，证据只放红项的原始输出。逐条读原始输出是重复劳动，红项自带它需要被看见的原文。

## 失败与重算留在程序里

命令失败时捕获错误字符串，记进该项，继续下一条；判据不通过时在同一程序里换判据或换输入重算。返回时仍有红项，下一轮从红项起步。

## 并发

无依赖的段落同批派出，用 `sb-thread:make-thread` + `sb-thread:join-thread`，只改变同一程序内部那一段的形状。

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
