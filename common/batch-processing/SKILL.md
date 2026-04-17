---
name: batch-processing
description: 连发多条工具调用前：把一条任务链并进一次批处理。
---

规则分三段：文本写何时调用与工具行为，判定函数返回结论，流程代码可直接抄。函数体里不写触发条件，文本里不写判定逻辑。

## 文本：何时调用、工具行为、坑

### 入口

- 发第一个 tool call 前调 `gate`：清单一步一行，标出输入与产出；载体是 `:program` 或 `:chain`；判据写成代码里能求值的表达式。
- 本轮只能因用户决定、缺输入、缺授权三件事结束，`end-turn-p` 判。

### 工具选择

- 从源码取事实先调 `source-fact-tool`。
- 起手写 shell 文本处理前先调 `shell-script-p`。

### 载体

- 能写成程序的写成一份 Lisp 程序；由工具调用构成的，把整条链列出来，无依赖的并发、有依赖的串行，用 `chain-order` 判。
- 程序写进 scratchpad 文件：`resource.edit` 整份覆盖 `scratchpad:NAME.lisp`，再 `lisp.scratchpad-run`，同一轮里做完。失败只改文件的一处。
- 并发用 `pmap`；每个线程体自己捕获。
- 中间结果不进入对话；要看某一步的结果，把判据写进链里，让它只回结论。

### 契约

- 参数与 schema 用 `args-ok-p` 比，返回值形状用 `shape-ok-p` 判。
- 同一调用连续两次因形状失败，`dead-loop-p` 为真，先读契约再一次发出。

### 拆链

- 主链超过约 20 行或同一段逻辑第二次出现，`split-needed-p` 为真，先定义小函数再在主链里调用。
- 一轮里第二次同类调用、参数取决于第一次返回，`chain-twice-p` 为真，停止串联，把剩余步骤写成程序。
- 要重放的链自包含，`self-contained-p` 为真；持久 REPL 里的定义只是缓存。

### 编辑

- 锚点取最短且唯一的代码片段：形状由 `anchor-clean-p` 判（无缩进、无空行），唯一性由 `locate` 判，出现两次时返回 `:lines`，改用按行定位。
- 改函数体里的某一行，先调 `defun-line`，再在这个函数的行范围内找锚点；缩进调 `indent-of`；替换区间从 `outer-line` 起。
- 整份写入用 `write-lines`，按行替换用 `edit-lines`。
- 写盘语句排在依赖它的验证之前，`write-before-check-p` 为真；验证读写盘用的同一个文本变量。
- 编辑失败后调 `restore-file` 恢复再重来。
- 目标文件报不存在时先调 `deleted-p`；` D path` 说明文件被删了，不是路径写错。
- 多个 worktree 里有同名文件时调 `confirm-file`；取值为 NIL 时判据兜底。

### 判据

- 判据先拿已知为坏的输入调 `judge-red`。
- 判据取子进程退出码，不取「没有报错」，用 `run-check`。
- 子集跑会把项目级门槛算进退出码；先关掉这些门槛（如 `--no-cov`），再读退出码。
- 命令连续几次停在同一个秒数，`stuck-p` 为真，先答「这一层为什么每次都停在这里」，不重发同一条命令。
- `handler-case` 的 clause 是 `(条件类型 (变量) 形式...)`，`handler-clause-p` 判；「无错即 ok」写成 `(progn (expr) (list :k :ok))`。
- 重定义带 `declaim` 返回类型的函数，求值末尾可能抛 type error；`type-error-after-value-p` 为真时先看返回值。
- 后台作业刚发出时 `job.get` 只回 `RUNNING`；要在一轮里等，用 `job.wait` 带真实超时，`real-timeout` 拒收 0。
- `lisp.eval` 只回最后一个形式的返回值；结论写在最后一个形式里。
- `lisp.scratchpad-run` 回的是 `load` 的返回值，不是文件里最后一个形式；结论用 `report` 写进 `defparameter` 再打印。
- 预计超过 60 秒的命令调 `slow-command`，按返回值选 `shell.run` 或 `lisp.eval`。
- 结论里的字面串用 `literal-from` 从文件取，不手打。

### 写回

- 本会话出现现有 skill 未写的可复用坑或长程操作，结束前 `skill.load skill-writing-guidance`；坑写成判据，长程操作写成步骤序列。

## 判定：调用返回结论

```lisp
(defpackage :batch
  (:use :cl)
  (:export #:gate #:end-turn-p #:source-fact-tool #:shell-script-p
           #:chain-order #:args-ok-p #:shape-ok-p #:dead-loop-p
           #:split-needed-p #:chain-twice-p #:self-contained-p
           #:anchor-clean-p #:locate #:write-before-check-p
           #:deleted-p #:confirm-file #:judge-red #:stuck-p
           #:handler-clause-p #:type-error-after-value-p
           #:real-timeout #:slow-command
           #:defun-line #:indent-of #:outer-line #:literal-from
           #:write-lines #:edit-lines #:pmap #:run-check
           #:restore-file #:report))

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

(defun source-fact-tool (answer-kind)
  (ecase answer-kind
    ((:symbol-location :callers :signature :field :call-graph :blast-radius) :lsp)
    (:other :script)))

(defun shell-script-p (one-call-answers)
  (if one-call-answers :use-that-call :script))

(defun chain-order (calls)
  (if (some #'second calls) :serial :parallel))

(defun args-ok-p (args schema)
  "ARGS is a plist; SCHEMA is ((key type) ...)."
  (and (evenp (length args))
       (= (/ (length args) 2) (length schema))
       (null (set-difference (loop for (key nil) on args by #'cddr collect key)
                             (mapcar #'first schema)))))

(defun shape-ok-p (value schema)
  (ecase schema
    (:string (stringp value))
    (:list (listp value))
    (:integer (integerp value))
    (:hash-table (hash-table-p value))
    (:boolean (or (eq value t) (null value)))))

(defun dead-loop-p (failures)
  (>= failures 2))

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

(defun chain-twice-p (attempts)
  (let ((names (mapcar #'first attempts)))
    (and (> (length names) (length (remove-duplicates names)))
         (some #'second attempts)
         t)))

(defun self-contained-p (defined used)
  (null (set-difference used defined)))

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
       (let ((first (char anchor 0)))
         (not (or (char= first (code-char 32)) (char= first (code-char 9)))))
       (not (find (code-char 10) anchor))
       (not (search (format nil "~c~c" (code-char 10) (code-char 10)) anchor))))

(defun write-before-check-p (steps)
  (let ((w (position :write steps)) (c (position :check steps)))
    (and w c (< w c))))

(defun deleted-p (path)
  (let ((out (uiop:run-program (list "git" "status" "--short" "--" (file-namestring path))
                               :directory (directory-namestring path)
                               :output :string :ignore-error-status t)))
    (and (search " D " out) t)))

(defun confirm-file (path branch marker)
  (and (search branch (uiop:run-program
                       (list "git" "-C" (directory-namestring path)
                             "rev-parse" "--abbrev-ref" "HEAD")
                       :output :string))
       (search marker (uiop:read-file-string path))
       t))

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
```

## 流程：可直接抄的代码

```lisp
(defun defun-line (text name)
  (loop for line in (uiop:split-string text :separator '(#\Newline))
        for i from 0
        when (search (format nil "(defun ~a" name) line) return i))

(defun indent-of (line)
  (subseq line 0 (or (position-if-not (lambda (c) (member c '(#\Space #\Tab))) line)
                     (length line))))

(defun outer-line (text line)
  (let ((lines (uiop:split-string text :separator '(#\Newline))))
    (loop for i downfrom line to 0
          when (zerop (length (indent-of (nth i lines)))) return i)))

(defun literal-from (path anchor)
  (or (find-if (lambda (line) (search anchor line))
               (uiop:split-string (uiop:read-file-string path) :separator '(#\Newline)))
      (error "no line contains ~a in ~a" anchor path)))

(defun write-lines (path lines)
  (let* ((text (format nil "~{~a~%~}" (copy-list lines)))
         (tmp  (format nil "~a.tmp" path)))
    (with-open-file (s tmp :direction :output :if-exists :supersede)
      (write-string text s))
    (rename-file tmp path)
    (length lines)))

(defun edit-lines (lines index new)
  (let ((copy (copy-list lines)))
    (setf (nth index copy) new)
    copy))

(defun pmap-one (fn item)
  (sb-thread:make-thread
   (lambda ()
     (handler-case (progn (funcall fn item) :ok)
       (error (e) (list :failed (princ-to-string e)))))))

(defun pmap (fn items)
  (let ((threads (loop for item in items collect (pmap-one fn item))))
    (mapcar #'sb-thread:join-thread threads)))

(defun run-check (command)
  (multiple-value-bind (output ignored code)
      (uiop:run-program command :output :string :error-output :output
                        :ignore-error-status t)
    (declare (ignore ignored))
    (values code output)))

(defun restore-file (path)
  (uiop:run-program (list "git" "checkout" "HEAD" "--" (file-namestring path))
                    :directory (directory-namestring path)
                    :output :string :error-output :output))

(defmacro report (name &body body)
  `(progn
     (defparameter ,name (progn ,@body))
     (format t "~&REPORT ~a ~s~%" ',name ,name)
     ,name))

(in-package :cl-user)
```
