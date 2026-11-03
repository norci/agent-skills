## HTTP 重试模式（素直版）

### 緣起
cl-agent `call-api` 調用 NVIDIA API 時，一次 `429` 即導致整個 `chat-repl` 退出，無自動重試。

### 修訂要點（`src/api.lisp`）
原單次 `dexador:request` 失敗即拋出，被 `chat-repl` 的 `handler-case` 捕獲後印出錯誤並退出。

修訂後以 `labels ((do-request (attempt) ...)` 包住 HTTP 調用，捕獲錯誤後打印、`(sleep 10)` 秒，遞歸重試，最多 5 次：

```lisp
(labels ((do-request (attempt)
           (handler-case
               (dexador:request url :method :post :headers headers
                                 :content body :want-stream t :force-binary t
                                 :keep-alive nil)
             (error (e)
               (format t "[HTTP ~A] retrying in 10s (attempt ~A)~%" e attempt)
               (sleep 10)
               (when (< attempt 5)
                 (return-from do-request
                   (do-request (1+ attempt))))
               (error e))))))
  (do-request 1))
```

### 注意
- 間隔固定 **10 秒**，非指數退避
- 實際是否觸發取決於 `dexador` 在 429 時是否拋 `error`
- 超過最大嘗試次數後，仍由 `chat-repl` 捕獲並退出，不會 endless loop