---
name: synthesizer
kind: service
---

### Requires

- `findings`: 搜索之结果
- `subquestions`: 子问题之列表

### Ensures

- `report`: 结构化之综合报告
- `controversies`: 争议与矛盾之记录

### Strategies

- 对比各来源之观点
- 标注信息之可信度（🟢/🟡/🟠/🔴）
- 评估替代之解释
- 记录来源间之矛盾
- 每个事实性陈述必有来源，使用 Markdown 链接格式 `[文本](URL)`
- 禁止使用占位符
- 所有章节必须完整填写
- 按以下结构撰写 report：执行摘要→研究背景→各子问题详细分析→核心争议→结论与展望
- 每个子问题需包含：定义、核心发现、评估方法、实证结果、争议点、研究空白
- controversies 需列出所有来源间矛盾，按重要性排序
- 结果存放于 `{vault}/.deep-research/{topic}/synthesis.md`
