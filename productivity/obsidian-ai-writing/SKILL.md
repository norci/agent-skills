---
name: obsidian-ai-writing
description:凡需在 Obsidian 中使用本地模型辅助写作、配置 Text Generator 插件，即当加载。
---

# Obsidian AI 写作之道

## 器用
- **插件**：Text Generator（开源 GPLv3，免费）
- **模型**：Ollama 本地运行

## 部署

```bash
ollama pull qwen2.5:7b
ollama serve
```

Obsidian 中：
- 装 Text Generator 插件
- 设 Provider 为 Ollama
- 设 Base URL 为 http://localhost:11434

## 用法

选中文本 → 右键 Text Generator → Run Prompt

**示例提示**：
```
扩写此段为三百字，文言风格
```

## 提示

- RAG 需开 Context 设置
- 模型慢则换小参数量（如 1.5b）
- Text Generator 已足，毋须自研脚本
