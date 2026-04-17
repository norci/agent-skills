---
name: archiver
kind: service
---

### Requires

- `report`: 最终之报告
- `verdict`: 审查之结果
- `topic`: 研究之主题
- `vault`: Obsidian 之库路径

### Ensures

- `saved_path`: 报告之存放路径
- `moc_updated`: MOC 是否已更新

### Strategies

- 主报告保存至 `{vault}/{category}/{topic}.md`
- YAML frontmatter 必含：title, date, tags, category, source, status
- 创建或更新 MOC（Map of Content）
- 创建追踪文件至 `{vault}/.deep-research/{topic}/status.json`
- 清理临时状态文件
