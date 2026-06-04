---
name: decomposer
kind: service
---

### Description

分解服务，负责：
1. 将研究主题按 MECE 原则分解为 3-8 个聚焦子问题
2. 若为加宽模式，在现有子问题基础上增加新维度

### Requires

- `topic`: 研究之主题
- `depth`: 研究之深度
- `existing_subquestions`: 现有子问题（可选，用于迭代模式）
- `iteration`: 迭代模式（可选，默认为「初始」）

### Ensures

- `subquestions`: 子问题之列表
- `coverage_gaps`: 覆盖之空白

### Strategies

- 按 MECE 原则分解主题，确保子问题互斥且全面
- 子问题数量：
 - 深度为「浅」：3-5 个
 - 深度为「常」：5-10 个
 - 深度为「深」：10-20 个
- **若 `iteration: 加宽`**：
 - 在 `existing_subquestions` 基础上，增加 **1-3 个新维度**
 - 确保新维度与现有子问题 **互斥且全面**
- **若 `iteration: 修复` 或 `加深`**：
 - 保持现有子问题不变，仅优化表述

### Shape

- `self`: 分解研究主题，生成子问题列表
- `prohibited`: 修改用户提供的 `topic`
