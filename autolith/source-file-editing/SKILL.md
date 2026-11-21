---
name: source-file-editing
description: 改源码文件前：定位锚点、整份写入、失败恢复。
---

## 编辑决策

- 锚点取最短且唯一的代码片段：`anchor-clean-p` 判形状，`locate` 判唯一性；`locate` 回行号表时改用按行定位。
- 改函数体某一行先调 `defun-line`，在这个函数的行范围内找锚点；缩进调 `indent-of`，替换区间从 `outer-line` 起。
- 整份写入用 `write-lines`，按行替换用 `edit-lines`。
- 验证排在写盘之后，两处读写同一个文本变量，`write-before-check-p` 判次序。
- 编辑失败调 `restore-file` 恢复再重来。
- 目标文件报不存在时先调 `deleted-p`，按删除标记和路径写错分流。
- 同名文件跨 worktree 时调 `confirm-file`，取值为假就停下核对路径。

## 判定函数

```lisp
(defpackage :source-file-editing
  (:use :cl)
  (:export #:anchor-clean-p #:locate #:write-before-check-p
           #:deleted-p #:confirm-file))
(in-package :source-file-editing)

(defun anchor-of (text anchor)
  (let ((first (search anchor text)))
    (cond ((null first) nil)
          ((search anchor text :start2 (1+ first)) :ambiguous)
          (t first))))

(defun locate (text anchor)
  (let ((at (anchor-of text anchor)))
    (cond ((eq at :ambiguous)
           (list :lines (loop for line in (uiop:split-string text :separator '(#\Newline))
                              for i from 0
                              when (search anchor line) collect i)))
          (at (list :anchor at))
          (t nil))))

(defun anchor-clean-p (anchor)
  (and (stringp anchor)
       (plusp (length anchor))
       (not (find (char anchor 0) '(#\Space #\Tab)))
       (not (find #\Newline anchor))
       (not (search (format nil "~c~c" #\Newline #\Newline) anchor))))

(defun write-before-check-p (steps)
  (let ((w (position :write steps)) (c (position :check steps)))
    (and w c (< w c))))

(defun deleted-p (path)
  (let ((out (uiop:run-program
              (list "git" "status" "--short" "--"
                    (file-namestring (pathname path)))
              :directory (directory-namestring (pathname path))
              :output :string :ignore-error-status t)))
    (and (search " D " out) t)))

(defun confirm-file (path branch marker)
  (and (search branch
               (uiop:run-program
                (list "git" "-C" (directory-namestring (pathname path))
                      "rev-parse" "--abbrev-ref" "HEAD")
                :output :string))
       (search marker (uiop:read-file-string path))
       t))

(in-package :cl-user)
```

## 编辑实现

```lisp
(in-package :source-file-editing)

(defun defun-line (text name)
  (loop for line in (uiop:split-string text :separator '(#\Newline))
        for i from 0
        when (search (format nil "(defun ~a" name) line) return i))

(defun indent-of (line)
  (subseq line 0 (or (position-if-not
                      (lambda (c) (member c '(#\Space #\Tab))) line)
                     (length line))))

(defun outer-line (text line)
  (let ((lines (uiop:split-string text :separator '(#\Newline))))
    (loop for i downfrom line to 0
          when (zerop (length (indent-of (nth i lines)))) return i)))

(defun write-lines (path lines)
  (let* ((text (format nil "~{~a~%~}" (copy-list lines)))
         (tmp (format nil "~a.tmp" path)))
    (with-open-file (s tmp :direction :output :if-exists :supersede)
      (write-string text s))
    (rename-file tmp path)
    (length lines)))

(defun edit-lines (lines index new)
  (let ((copy (copy-list lines)))
    (setf (nth index copy) new)
    copy))

(defun restore-file (path)
  (uiop:run-program
   (list "git" "checkout" "HEAD" "--" (file-namestring (pathname path)))
   :directory (directory-namestring (pathname path))
   :output :string :error-output :output))

(in-package :cl-user)
```
