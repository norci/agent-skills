---
name: researcher
kind: service
---

### Description

研究服务，负责：
1. 根据子问题进行多轮搜索
2. 若为迭代模式，支持加宽（新维度）或加深（更深入）

### Requires

- `subquestions`: 子问题之列表
- `depth`: 研究之深度
- `previous_findings`: 先前之发现（可选，用于迭代模式）
- `iteration`: 迭代模式（可选，默认为「初始」）

### Ensures

- `findings`: 结构化之发现，含来源与可信度，存放于 `{vault}/.deep-research/{topic}/findings/`
- `gaps`: 信息之空白

### Strategies

- 先广搜以收关键词之池
- 关键页面以 browser_navigate 深读
- 优先官方报告、权威媒体、企业白皮书
- 可信度分四级：🟢 主要来源，🟡 权威媒体，🟠 一般来源，🔴 低可信
- 记录来源间之矛盾
- 去重依 URL 或事实
- **若 `iteration: 加宽`**：
 - 在现有子问题基础上，增加 **1-3 个新维度**（如：多模态推理、伦理争议）
 - 为新维度生成独立的 `findings` 文件
- **若 `iteration: 加深`**：
 - 对现有子问题进行 **更深入的研究**（增加搜索轮次、深读更多来源）
 - 补充现有 `findings` 中的空白
- 若 `previous_findings` 存在，在其基础上 **增量更新**

### Shape

- `self`: 搜索与深读，提取结构化发现
- `prohibited`: 修改原始数据或报告
