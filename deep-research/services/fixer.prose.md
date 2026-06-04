---
name: fixer
kind: service
---

### Description

修复服务，负责：
1. 读取 `issues.md` 中的问题
2. 按优先级（高 > 中 > 低）修复报告
3. 生成修复日志

### Requires

- `report`: 待修复之报告
- `findings`: 原始研究发现
- `vault`: Obsidian 之库路径

### Ensures

- `fixed_report`: 修复后之报告，存放于 `{vault}/.deep-research/{topic}/workspace/fixer/fixed_report.md`
- `fix_log`: 修复日志，记录已解决之问题，存放于 `{vault}/.deep-research/{topic}/workspace/fixer/fix_log.md`

### Strategies

- 读取 `{vault}/.deep-research/{topic}/workspace/critic/issues.md` 文件，按优先级排序
- **高优先级修复**：
 - 补充证据链：为缺乏来源的陈述添加引用（从 `findings` 中提取）
 - 统一可信度标记：确保同一来源在所有出现的地方标记一致
 - 修正数据准确性：确保报告中的评级与 `findings` 中的具体数据一致
- **中优先级修复**：
 - 优化结构层次：统一章节编号格式，添加过渡段落
 - 强化争议显性化：为每个争议提供支持和反对的证据列表
 - 统一术语定义：创建术语表，确保全文使用一致的术语
- **低优先级修复**：
 - 统一引用格式
 - 删除重复内容
 - 补充可视化（如图表）
- 若无法自动修复，在 `fix_log` 中标注「需人工处理」

### Shape

- `self`: 修复报告内容，生成修复日志
- `delegates`:
 - `researcher`: 补充证据（如需额外搜索）
- `prohibited`: 修改 `findings` 或原始数据
