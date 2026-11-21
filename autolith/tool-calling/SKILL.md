---
name: tool-calling
description: 调用工具前：选工具、验参数与返回形状。
---

## 工具决策

- 事实能从源码取出时用 `source-fact-tool` 选工具。
- 要写 shell 文本处理前调 `shell-script-p`，一次调用能答完就用那次调用，否则写脚本。
- 参数交 `args-ok-p` 比对，返回值交 `shape-ok-p` 判形状。
- 同一调用连续两次因形状失败，`dead-loop-p` 为真就先读契约，再一次发出。

## 判定函数

```lisp
(defpackage :tool-calling
  (:use :cl)
  (:export #:source-fact-tool #:shell-script-p
           #:args-ok-p #:shape-ok-p #:dead-loop-p))
(in-package :tool-calling)

(defun source-fact-tool (answer-kind)
  (ecase answer-kind
    ((:symbol-location :callers :signature :field :call-graph :blast-radius) :lsp)
    (:other :script)))

(defun shell-script-p (one-call-answers)
  (if one-call-answers :use-that-call :script))

(defun args-ok-p (args schema)
  (let ((keys (loop for (key nil) on args by #'cddr collect key)))
    (and (evenp (length args))
         (= (length keys) (length schema))
         (null (set-difference keys (mapcar #'first schema))))))

(defun shape-ok-p (value schema)
  (ecase schema
    (:string (stringp value))
    (:list (listp value))
    (:integer (integerp value))
    (:hash-table (hash-table-p value))
    (:boolean (or (eq value t) (null value)))))

(defun dead-loop-p (failures)
  (>= failures 2))

(in-package :cl-user)
```
