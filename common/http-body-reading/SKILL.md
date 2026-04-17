---
name: http-body-reading
description: 写 HTTP 客户端或读响应体前：从网络流读出响应体时的字节边界与截断判据。
---

# 响应体的字节边界

## 不变量

连接关闭之前已经交付的字节属于响应体。只有关闭本身表示输入结束；读取中途抛错不等于「没有数据」。

## 所属层

体是否读完由读体的那一层判定。TLS 层只有关闭事件，没有长度概念；把截断判定放在 TLS 层就看不到声明长度。

## 读完整个体

缓冲读一次取几千字节时，读取中途抛条件会让整次调用失败，已交付的字节随之丢失，调用方看到的是空体。逐单位读、每次读各自接条件，已交付部分才留下：

```lisp
(loop for octet = (handler-case (read-byte stream nil nil)
                    (unclean-close (condition)
                      (if (unclean-close-p condition) nil (error condition))))
      while octet
      do (vector-push-extend octet octets 8192))
```

`nil` 是唯一的结束信号。条件只在确认为关闭时折成 `nil`，其余原样抛出。

## 无 close_notify 的关闭

对端发完响应直接断 TCP、不发 TLS close_notify 时，OpenSSL 3 把它当错误而不是流结束，报 `error:0A000126:SSL routines::unexpected eof while reading`。判据是这个条件出现在流已给出全部字节之后，而不是出现在首次读取。

## 长度校验

声明长度与实际读到的字节数不等时抛协议错误，错误里带两个数字。声明长度缺失时不校验，此时只有体解析器的失败能发现截断。

## 替身要走中途抛错

用返回短计数的替身模拟连接中断测不出上面的缺陷：缓冲读正常返回，已交付字节不丢。判据是替身的读取方法在同一次调用里先写入部分字节、再抛那个条件，且此后不再交付数据。
