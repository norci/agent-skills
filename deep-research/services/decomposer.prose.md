---
name: decomposer
kind: service
---

### Requires

- `topic`: 研究之主题
- `depth`: 研究之深度
- `existing_research`: 已有之研究（如有）

### Ensures

- `subquestions`: 三至八个聚焦之子问题
- `coverage_gaps`: 已被覆盖之领域

### Strategies

- 依 MECE 之理，分而治之
- 避宽泛之问，如「何为某物」当改为「某物如何运作」
- 优先补已有研究之空白
- 结果存放于 `{vault}/.deep-research/{topic}/subquestions.json`
