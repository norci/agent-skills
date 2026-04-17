---
name: critic
kind: service
---

### Requires

- `report`: 综合之报告
- `findings`: 搜索之结果

### Ensures

- `verdict`: 审查之结果，或「可」或「修」或「弃」
- `issues`: 发现之问题列表

### Strategies

- 检查源覆盖：是否使用五源以上
- 检查证据可信度：是否优先引用官方报告、权威媒体
- 检查结构完整性：是否包含所有维度
- 检查开放性问题：是否存在未解之重要问题
- 检查证据链完整：每个事实性陈述必有来源
- 检查争议显性化：矛盾是否明确标注
- 诚实给出「可」，不强行找问题
- 结果存放于 `{vault}/.deep-research/{topic}/critic_report.json`
