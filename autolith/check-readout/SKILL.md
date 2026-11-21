---
name: check-readout
description: 读检查结果时：判据取退出码与可判读数。
---

## 读数决策

- 写完判据先拿已知为坏的输入调 `judge-red`。
- 退出码用 `run-check` 取，子集跑前先关掉项目级门槛。
- 命令连续几次停在同一秒数，`stuck-p` 为真就先答这一层为什么每次停在这里，不重发同一条命令。
- clause 形状是 `(条件类型 (变量) 形式...)`，`handler-clause-p` 判；「无错即 ok」写成 `(progn (expr) (list :k :ok))`。
- 求值末尾抛类型错误且 `type-error-after-value-p` 为真时先看返回值。
- 要在一轮里等后台作业，用 `job.wait` 带真实超时，`real-timeout` 拒收非正超时。
- 预计超过一分钟的命令调 `slow-command`，按返回值选执行工具。
- 结论写在 `lisp.eval` 最后一个形式里。
- `lisp.scratchpad-run` 的结论用 `report` 写进 `defparameter` 再打印。
- 结论里的字面串用 `literal-from` 从文件取。

## 判定函数

```lisp
(defpackage :check-readout
  (:use :cl)
  (:export #:judge-red #:stuck-p #:handler-clause-p
           #:type-error-after-value-p #:real-timeout #:slow-command))
(in-package :check-readout)

(defun judge-red (form)
  (when (eval form) (error "judge stayed true on the known-bad input"))
  t)

(defun stuck-p (durations)
  (and durations
       (> (length durations) (length (remove-duplicates durations)))
       t))

(defun handler-clause-p (clause)
  (and (consp clause) (symbolp (first clause)) (listp (second clause))
       (every #'identity (cddr clause))))

(defun type-error-after-value-p (condition)
  (typep condition 'type-error))

(defun real-timeout (seconds)
  (when (<= seconds 0) (error "wait needs a real timeout, got ~a" seconds))
  seconds)

(defun slow-command (seconds)
  (if (> seconds 60) :lisp.eval :shell.run))

(in-package :cl-user)
```

## 读数实现

```lisp
(in-package :check-readout)

(defun run-check (command)
  (multiple-value-bind (output ignored code)
      (uiop:run-program command :output :string :error-output :output
                        :ignore-error-status t)
    (declare (ignore ignored))
    (values code output)))

(defun literal-from (path anchor)
  (or (find-if (lambda (line) (search anchor line))
               (uiop:split-string (uiop:read-file-string path) :separator '(#\Newline)))
      (error "no line contains ~a in ~a" anchor path)))

(defmacro report (name &body body)
  `(progn
     (defparameter ,name (progn ,@body))
     (format t "~&REPORT ~a ~s~%" ',name ,name)
     ,name))

(in-package :cl-user)
```
