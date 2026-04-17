---
name: verifier
kind: service
---

### Requires

- `topic`: 待验证之研究主题

### Ensures

- `verification`: 实体与验证结果之映射
- `unknown_entities`: 无法验证之实体列表

### Strategies

- 搜索主题中每一实体
- 新事物新概念，少结果不等于不存在
- 报所得，不报所失
- 结果存放于 `{vault}/.deep-research/{topic}/entities.json`
