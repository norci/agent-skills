---
name: batch-processing
description: 把多个独立操作合并进一个 Lisp 程序，一个程序走完取证据、判据、续取、动作、复核，只返回结论和证据。
---

# 用 Lisp 批处理

一个程序即一步之全部。取证据、判判据、按判据续取、落动作、复核，都在同一个 Lisp 表单里走完。程序只返回结论和证据，不返回原始输出。

## 什么时候用

- 多条互不依赖的 shell 命令。
- 同一条命令作用在多个文件、仓库或 PR 上。
- 读、判断、写属于同一件事。
- 需要按结果分流、逐项比对、反复重跑的动作。

## 结构

一个程序分五段：

1. **取证据**：把要查的东西列成列表。
2. **判据**：用谓词判断每条证据。
3. **续取**：判据不通过时，换判据或换输入重算。
4. **动作**：对通过判据的项执行写操作。
5. **复核**：重新读一遍，确认动作生效。

返回 `(:conclusion ... :evidence ...)`，结论是判据的结果，证据是支撑结论的原始数据。

## 并发

无依赖的任务同批派出，用 `sb-thread:make-thread` + `sb-thread:join-thread`。有依赖的任务串行。

```lisp
(defun run-concurrently (tasks)
  (mapcar #'sb-thread:join-thread
          (mapcar (lambda (task)
                    (sb-thread:make-thread
                     (lambda ()
                       (handler-case
                           (funcall task)
                         (error (e) (list :error (format nil "~a" e)))))))
                  tasks)))
```

`lparallel` 在 worker 里不可用，`bordeaux-threads` 和 `sb-thread` 可用。

## 判据与重算

判据是谓词，不通过时在同一个程序里换判据重算，不要退出程序再发一轮。

```lisp
(labels ((check (criterion)
           (or (funcall criterion)
               (check (lambda () (funcall criterion))))))
  ...)
```

## 例子

### 多条 shell 命令并发

```lisp
(let* ((commands '(("git" "status" "--short")
                   ("git" "log" "--oneline" "-3")))
       (results (mapcar #'sb-thread:join-thread
                        (mapcar (lambda (command)
                                  (sb-thread:make-thread
                                   (lambda ()
                                     (handler-case
                                         (list :command command
                                               :output (uiop:run-program command :output :string :error-output :output :ignore-error-status t))
                                       (error (e) (list :command command :error (format nil "~a" e)))))))
                                commands))))
  (list :conclusion (mapcar (lambda (result)
                              (list :command (getf result :command)
                                    :passed (and (getf result :output)
                                                 (not (string= (getf result :output) "")))))
                            results)
        :evidence results))
```

### 同一条命令作用在多个 PR 上

```lisp
(let* ((raw (uiop:run-program
             '("gh" "search" "prs" "--author" "@me" "--state" "open"
               "--json" "number,repository"
               "--jq" ".[] | [.repository.nameWithOwner, .number] | @tsv")
             :output :string :error-output :output :ignore-error-status t))
       (lines (remove-if (lambda (line) (string= line ""))
                         (uiop:split-string raw :separator '(#\Newline))))
       (tasks (mapcar (lambda (line)
                        (destructuring-bind (repo number)
                            (uiop:split-string line :separator '(#\Tab))
                          (lambda ()
                            (list :repo repo
                                  :number number
                                  :output (uiop:run-program
                                           (list "gh" "pr" "view" number "--repo" repo
                                                 "--json" "comments,reviews")
                                           :output :string :error-output :output :ignore-error-status t)))))
                      lines))
       (results (mapcar #'sb-thread:join-thread
                        (mapcar (lambda (task)
                                  (sb-thread:make-thread
                                   (lambda ()
                                     (handler-case (funcall task)
                                       (error (e) (list :error (format nil "~a" e)))))))
                                tasks))))
  (list :conclusion (mapcar (lambda (result)
                              (list :repo (getf result :repo)
                                    :number (getf result :number)
                                    :has-comments (not (string= (getf result :output) ""))))
                            results)
        :evidence results))
```

## 规则

- 互不依赖的命令不要一轮一条。
- 不要读文件、改文件、再读文件分三轮；一个程序做完。
- 命令失败时捕获错误字符串，继续下一条。
- 判据不通过时在同一个程序里换判据重算，不要退出程序再发一轮。
- 返回 `(:conclusion ... :evidence ...)`，不返回原始输出。
