---
name: deep-research
kind: system
---

### Description

深度研究系统，支持 **迭代模式**：
- **初始**：首次研究，生成基础报告
- **修复**：按 `issues.md` 修复问题，重新审查
- **加宽**：在现有子问题基础上，增加新维度
- **加深**：对现有子问题进行更深入研究

### Services

- verifier
- decomposer
- researcher
- synthesizer
- critic
- fixer
- archiver

### Requires

- `topic`: 研究之主题
- `depth`: 研究之深度，或「浅」或「常」或「深」（默认为「常」）
- `vault`: Obsidian 之库路径（默认为用户之库）
- `iteration`: 迭代模式，或「初始」或「修复」或「加宽」或「加深」（默认为「初始」）

### Ensures

- `report`: 结构化之研究报告
- `verdict`: 审查之结果，或「可」或「修」或「弃」
- `saved_path`: 报告之存放路径
- `iteration_log`: 迭代日志，记录每次修复或扩展之内容

### Strategies

- 深度为「浅」：搜索1轮，不做深读
- 深度为「常」：搜索2轮，深读 4 源以上
- 深度为「深」：搜索4轮，深读 16 源以上
- **迭代模式为「修复」**：
 - 读取 `{vault}/.deep-research/{topic}/workspace/critic/issues.md`
 - 按优先级修复问题（高 > 中 > 低）
 - 重新运行 `synthesizer` 与 `critic`，最多迭代 8 次
- **迭代模式为「加宽」**：
 - 在现有子问题基础上，增加 1-3 个新维度
 - 重新运行 `decomposer`、`researcher`、`synthesizer`、`critic`
- **迭代模式为「加深」**：
 - 对现有子问题进行更深入的研究（增加搜索轮次、深读更多来源）
 - 重新运行 `researcher`、`synthesizer`、`critic`
- 收到 critic 之 verdict 为「修」：按 issues.md 修复后重新执行 synthesizer 与 critic
- 收到 critic 之 verdict 为「弃」：放弃当前研究
- researcher 若来源不足：触发第二轮搜索
- verifier 若实体验证不果：展宽范围继续
- 状态统一存放于 `{vault}/.deep-research/{topic}/`
- 使用 delegate_task 并发执行同层级任务

### Runtime

- `persist`: project
