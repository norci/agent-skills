---
name: deep-research
kind: system
services: [verifier, decomposer, researcher, synthesizer, critic, archiver]
---

### Requires

- `topic`: 研究之主题
- `depth`: 研究之深度，或「浅」或「常」或「深」（默认为「常」)
- `vault`: Obsidian 之库路径（默认为用户之库）

### Ensures

- `report`: 结构化之研究报告，含发现、争议与出处
- `verdict`: 审查之结果，或「可」或「修」或「弃」
- `saved_path`: 报告之存放路径

### Strategies

- 深度为「浅」：搜索1轮，不做深读
- 深度为「常」：搜索2轮，深读 4 源以上
- 深度为「深」：搜索4轮，深读 16 源以上
- 收到 critic 之 verdict 为「修」：按 issues.md 修复后重新执行 synthesizer 与 critic，最多迭代 8 次
- 收到 critic 之 verdict 为「弃」：放弃当前研究
- researcher 若来源不足：触发第二轮搜索
- verifier 若实体验证不果：展宽范围继续
- 状态统一存放于 `{vault}/.deep-research/{topic}/`
- 使用 delegate_task 并发执行同层级任务
