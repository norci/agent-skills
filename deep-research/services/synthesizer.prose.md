---
name: synthesizer
kind: service
---

### Description

综合服务，负责：
1. 将 `findings` 综合为结构化报告
2. 若为迭代模式，在原报告基础上增量更新

### Requires

- `findings`: 搜索之结果
- `subquestions`: 子问题列表
- `previous_report`: 上一版报告（可选，用于迭代模式）
- `improvements`: 修复建议（可选，用于迭代模式）

### Ensures

- `report`: 综合之报告，存放于 `{vault}/.deep-research/{topic}/workspace/synthesizer/report.md`
- `controversies`: 争议记录，存放于 `{vault}/.deep-research/{topic}/workspace/synthesizer/controversies.md`

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
- 若 `previous_report` 存在：
 - 在其基础上进行 **增量更新**（仅修改或补充，不重写）
 - 保留原报告之优势亮点（如源覆盖、理论完整性）
- 若 `improvements` 存在：
 - 按修复建议调整报告内容（如补充引用、统一标记）
- 结果同时保存副本至 `{vault}/.deep-research/{topic}/synthesis.md`

### Shape

- `self`: 综合研究结果，生成结构化报告
- `prohibited`: 修改 `findings` 或原始数据
