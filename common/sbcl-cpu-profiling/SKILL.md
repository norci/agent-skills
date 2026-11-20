---
name: sbcl-cpu-profiling
description: 给 Lisp 镜像做 CPU 归因时：统计采样定位自身耗时最高的函数。
---

# 采样归因回路

## 判据

SBCL 的统计采样器只有 sb-sprof；CPU 归因先加载该模块再采样。

采样只针对症状所在的镜像。agent 把活动镜像与一次性 worker 分开时，空闲占用属于活动镜像，不属于 worker。

采样窗口内症状正在发生。空闲占用用开采样、睡一段、停采样的窗口覆盖，症状落在窗口之外时样本不指向它。

sb-sprof:report 的布局关键字是 :type，取 :graph 或 :flat；报告写进字符串输出流才能取回文本。

## 步骤序列

```lisp
(require :sb-sprof)
(sb-sprof:start-profiling)
(sleep 5)
(sb-sprof:stop-profiling)
(with-output-to-string (stream)
  (sb-sprof:report :stream stream :type :flat))
```

读报告的 Self 列找自身耗时最高的函数，Total 列含被调用者耗时，用来追调用链。
