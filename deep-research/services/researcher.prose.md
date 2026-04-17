---
name: researcher
kind: service
---

### Requires

- `subquestions`: 子问题之列表
- `depth`: 研究之深度
- `previous_findings`: 先前之发现（如有）

### Ensures

- `findings`: 结构化之发现，含来源与可信度
- `gaps`: 信息之空白

### Strategies

- 先广搜以收关键词之池
- 关键页面以 browser_navigate 深读
- 优先官方报告、权威媒体、企业白皮书
- 可信度分四级：🟢 主要来源，🟡 权威媒体，🟠 一般来源，🔴 低可信
- 记录来源间之矛盾
- 去重依 URL 或事实
- 结果存放于 `{vault}/.deep-research/{topic}/findings/`
