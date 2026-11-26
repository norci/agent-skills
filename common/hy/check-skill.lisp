;;;; Check that SKILL.md names every public directive listed in Hy and Hyrule docs.
;;;; Usage: sbcl --script check-skill.lisp SKILL_MD HY_API_RST HYRULE_INDEX_RST
;;;; Exit 0: all names present. Exit 1: some names missing. Exit 2: bad arguments.

(defparameter *skill-directive-markers*
  '(".. hy:macro:: "
    ".. hy:automacro:: "
    ".. hy:autofunction:: "
    ".. hy:autoclass:: "
    ".. hy:automodule:: "
    ".. hy:autotag:: "
    ".. hy:class:: "
    ".. hy:data:: "
    ".. autoexception:: "
    ".. autoclass:: "))

(defun skill-file-text (path)
  (with-open-file (stream path :direction :input)
    (let ((out (make-string-output-stream)))
      (loop for line = (read-line stream nil)
            while line do (write-line line out))
      (get-output-stream-string out))))

(defun skill-first-token (text)
  (let* ((trimmed (string-trim " ()" text))
         (end (position #\Space trimmed)))
    (if end (subseq trimmed 0 end) trimmed)))

(defun skill-normalize-name (name)
  (let ((prefix "hy.core.macros."))
    (if (and (>= (length name) (length prefix))
             (string= name prefix :end1 (length prefix)))
        (subseq name (length prefix))
        name)))

(defun skill-directive-name (line)
  (dolist (marker *skill-directive-markers* nil)
    (let ((start (search marker line)))
      (when start
        (return
          (skill-normalize-name
            (skill-first-token
              (subseq line (+ start (length marker))))))))))

(defun skill-document-names (path)
  (with-open-file (stream path :direction :input)
    (loop for line = (read-line stream nil)
          while line
          for name = (skill-directive-name line)
          when name collect name)))

(defun skill-public-names (hy-api hyrule-index)
  (remove-duplicates
    (append (skill-document-names hy-api)
            (skill-document-names hyrule-index))
    :test #'string=))

(defun skill-missing-names (names skill-text)
  (remove-if (lambda (name) (search name skill-text)) names))

(defun skill-main ()
  (let ((args (rest sb-ext:*posix-argv*)))
    (if (/= (length args) 3)
        (progn
          (format *error-output*
                  "Usage: sbcl --script check-skill.lisp SKILL_MD HY_API_RST HYRULE_INDEX_RST~%")
          (sb-ext:exit :code 2))
        (destructuring-bind (skill-path hy-api hyrule-index) args
          (let* ((skill-text (skill-file-text skill-path))
                 (names (skill-public-names hy-api hyrule-index))
                 (missing (skill-missing-names names skill-text)))
            (format t "names=~D missing=~D~%" (length names) (length missing))
            (dolist (name missing)
              (format t "~A~%" name))
            (sb-ext:exit :code (if missing 1 0)))))))

(skill-main)
