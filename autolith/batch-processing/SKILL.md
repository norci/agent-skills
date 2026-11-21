---
name: batch-processing
description: 第一个工具调用前：把一条任务链并进一次批处理。
---

## 链的决策

- 把清单、载体、判据交给 `gate`。
- 只有用户决定、缺输入、缺授权才收尾，用 `end-turn-p` 判。
- 调用间有依赖就串行，否则并发，用 `chain-order` 判。
- 程序写进 `scratchpad:NAME.lisp`，用 `resource.edit` 整份覆盖，`lisp.scratchpad-run` 执行，同一轮做完。
- 并发项交给 `pmap`，每个线程体自己捕获异常。
- 中间结果不进对话；要读某一步的结果，把判据写进链里，只回结论。
- 主链超约二十行或同段逻辑重复，`split-needed-p` 为真就先定义函数。
- 同一调用第二次出现且参数依赖第一次返回，`chain-twice-p` 为真就停止串联，余下步骤写成程序。
- 要重放的链交给 `self-contained-p` 判自包含。

## 判定函数

```lisp
(defpackage :batch
  (:use :cl)
  (:export #:gate #:end-turn-p #:chain-order
           #:split-needed-p #:chain-twice-p #:self-contained-p))
(in-package :batch)

(defparameter *end-turn* '(:user-decision :missing-input :authorization))
(defparameter *chain-limit* 20)

(defun step-p (x)
  (and (listp x) (= 3 (length x)) (stringp (first x))
       (every #'identity (rest x))))

(defun criteria-p (form)
  (and form (consp form) (not (stringp (first form)))))

(defun gate (&key checklist carrier criteria)
  (let ((missing (remove nil
                         (list (unless (and checklist (every #'step-p checklist)) :checklist)
                               (unless (member carrier '(:program :chain)) :carrier)
                               (unless (criteria-p criteria) :criteria)))))
    (when missing (error "entry gate missing ~{~a~^, ~}" missing))
    t))

(defun end-turn-p (reason)
  (and (member reason *end-turn*) t))

(defun chain-order (calls)
  (if (some #'second calls) :serial :parallel))

(defun nodes (form)
  (let (acc)
    (labels ((walk (x)
               (push x acc)
               (when (consp x) (mapc #'walk x))))
      (walk form))
    acc))

(defun split-needed-p (form)
  (let* ((all (nodes form))
         (printed (mapcar (lambda (f) (format nil "~s" f))
                          (remove-if-not #'consp all))))
    (or (> (length (remove-if #'consp all)) *chain-limit*)
        (some (lambda (f) (> (count f printed :test #'string=) 1)) printed))))

(defun chain-twice-p (names-and-args)
  (let ((names (mapcar #'first names-and-args)))
    (and (> (length names) (length (remove-duplicates names)))
         t)))

(defun self-contained-p (defined used)
  (null (set-difference used defined)))

(in-package :cl-user)
```

## 并发实现

```lisp
(in-package :batch)

(defun pmap-one (fn item)
  (sb-thread:make-thread
   (lambda ()
     (handler-case (progn (funcall fn item) :ok)
       (error (e) (list :failed (princ-to-string e)))))))

(defun pmap (fn items)
  (let ((threads (loop for item in items collect (pmap-one fn item))))
    (mapcar #'sb-thread:join-thread threads)))

(in-package :cl-user)
```
