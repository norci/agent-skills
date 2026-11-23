---
name: lisp-repl-stepwise
description: 用 lisp REPL 做多步工作时：一次一 form、读回返回值再走下一步。
---

## 一步一读

每个 form 的返回值只取 REPL 返回的文本，未收到返回文本的 form 不产生可引用的值。

一次调用发一个 form，读到返回值再发下一个。下一步的输入取上一步的返回值。

命名 REPL 跨调用保留定义与绑定，后一步直接引用前一步定义的名字。

一个 form 要看多个量时用 `values` 一并返回。

## 先样本后批量

变换写成函数。定义函数后紧接一次样本调用，读到期望值才用到整批。

样本取能一眼读出期望值的最小输入，批量输入与样本同形。

## 失败只改当前 form

form 报错时只重写那个 form 再发，已通过的 form 不重发。

报错指出某个上下文无绑定时，先判这个上下文在 worker 里有没有绑定，再判逻辑。

## 流程

```lisp
(defparameter *items* '("a foo b" "foo = 1" "no token"))
```

```lisp
(defun count-token (text token)
  (let ((count 0) (start 0))
    (loop for hit = (search token text :start2 start)
          while hit
          do (incf count) (setf start (+ hit (length token))))
    count))
```

```lisp
(mapcar (lambda (s) (count-token s "foo")) *items*)
```

```lisp
(equal (mapcar (lambda (s) (count-token s "foo")) *items*) '(1 1 0))
```
