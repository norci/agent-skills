(cl:defpackage #:cl-mcp-smoke-runner
  (:use #:cl)
  (:export #:run))

(in-package #:cl-mcp-smoke-runner)

(defun smoke ()
  (ql:quickload :cl-mcp-server)
  (format t "=== cl-mcp-server loaded ===~%")

  (let* ((server (cl-mcp:make-server :name "smoke" :version "0.3.0"))
         (session (cl-mcp-server.session:make-session))
         (registry nil))

    (cl-mcp-server.session:with-session (session)
      (cl-mcp-server.tools:define-builtin-tools server session)
      (setf registry (cl-mcp:mcp-server-tools server))

      (format t "[evaluate-lisp] => ")
      (let ((result (cl-mcp.tools:call-tool registry "evaluate-lisp" (list (cons "code" "(+ 1 2 3)")))))
        (dolist (blk result)
          (format t "~S~%" (cdr (assoc "text" blk :test #'string=))))
        (terpri))

      (format t "[validate-syntax] => ")
      (let ((result (cl-mcp.tools:call-tool registry "validate-syntax" (list (cons "code" "(+ 1 2 (")))))
        (dolist (blk result)
          (format t "~S~%" (cdr (assoc "text" blk :test #'string=))))
        (terpri))

      (format t "[match-paren] => ")
      (let ((result (cl-mcp.tools:call-tool registry "match-paren" (list (cons "code" "(+ 1 2)") (cons "line" 1) (cons "column" 0)))))
        (dolist (blk result)
          (format t "~S~%" (cdr (assoc "text" blk :test #'string=))))
        (terpri))

      (format t "[get-usage-guide] => ")
      (let* ((result (cl-mcp.tools:call-tool registry "get-usage-guide" nil))
             (block (first result))
             (text (cdr (assoc "text" block :test #'string=))))
        (format t "len=~D first=~S~%" (length text) (subseq text 0 (min 60 (length text))))
        (terpri))

      (format t "[describe-symbol] => ")
      (let ((result (cl-mcp.tools:call-tool registry "describe-symbol" (list (cons "name" "CAR") (cons "package" "CL")))))
        (dolist (blk result)
          (format t "~S~%" (cdr (assoc "text" blk :test #'string=))))
        (terpri))

      (format t "[list-local-systems] => ")
      (let ((result (cl-mcp.tools:call-tool registry "list-local-systems" nil)))
        (dolist (blk result)
          (format t "~S~%" (cdr (assoc "text" blk :test #'string=))))
        (terpri))

      (format t "[configure-limits] => ")
      (let ((result (cl-mcp.tools:call-tool registry "configure-limits" nil)))
        (dolist (blk result)
          (format t "~S~%" (cdr (assoc "text" blk :test #'string=))))
        (terpri)))

    (format t "=== all smoke tools returned ===~%")))
