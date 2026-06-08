#!/bin/sh
# akcli.sh - 调用 AKCLI API，返回原始 JSON
# 数据处理由 LLM 按需写 Python 脚本完成
cd "$(dirname "$0")" && exec uv run -m akcli "$@"
