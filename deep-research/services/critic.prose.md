---
name: critic
kind: service
---

### Description

审查服务，负责：
1. 检查报告质量（证据链、可信度、结构、数据）
2. 生成问题清单（`issues.md`）
3. 若为迭代模式，生成具体修复指令（`improvements`）

### Requires

- `report`: 综合之报告
- `findings`: 搜索之结果
- `iteration`: 迭代模式（可选，默认为「初始」）

### Ensures

- `verdict`: 审查之结果，或「可」或「修」或「弃」
- `issues`: 发现之问题列表，存放于 `{vault}/.deep-research/{topic}/workspace/critic/issues.md`
- `improvements`: 修复建议（仅当 `verdict: 修` 时生成）

### Strategies

- 检查源覆盖：是否使用五源以上
- 检查证据可信度：是否优先引用官方报告、权威媒体
- 检查结构完整性：是否包含所有维度
- 检查开放性问题：是否存在未解之重要问题
- 检查证据链完整：每个事实性陈述必有来源
- 检查争议显性化：矛盾是否明确标注
- 若 `iteration: 修复`，重点检查 `issues.md` 中的高优先级问题是否已解决
- 若 `verdict: 修`，生成具体的 `improvements` 指令（如：补充证据链、统一可信度标记）
- 诚实给出「可」，不强行找问题

### Shape

- `self`: 审查报告质量，生成问题清单与修复建议
- `prohibited`: 修改报告内容
