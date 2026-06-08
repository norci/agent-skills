#!/usr/bin/env python3
"""
akshare CLI wrapper - 让 agent 直接调用 akshare API

提供可被 import 的 call_api() 函数和命令行入口 main()。
Valkey 缓存自动生效，避免频繁网络请求。

用法（作为模块）:
    from akcli.cli import call_api
    df = call_api("stock_zt_pool_em", date=20260317)

用法（命令行）:
    akcli <function_name> [key=value ...]   调用 API
    akcli --list [keyword]                  列出/搜索可用 API
    akcli --info <function_name>            查看 API 详情
"""

import inspect
import json
import os
import subprocess
import sys
import time
from contextlib import suppress
from datetime import datetime, timezone

import akshare as ak

from akcli.auto_ban import check_banned, clean_expired, is_banned, record_failure
from akcli.cache import cache_get, cache_set


def _background_update():
    """后台静默更新 akshare/依赖（每小时最多一次，不阻塞主流程）。"""
    _UPDATE_INTERVAL = 3600          # 1 小时
    _PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    _UPDATE_FILE = os.path.join(_PROJECT_DIR, ".last_akshare_update")

    now = datetime.now(timezone.utc).timestamp()
    try:
        last = float(open(_UPDATE_FILE).read().strip())
    except Exception:
        last = 0

    if now - last < _UPDATE_INTERVAL:
        return

    # 写锁文件，避免并发触发
    try:
        with open(_UPDATE_FILE, "w") as f:
            f.write(str(now))
    except Exception:
        return

    subprocess.Popen(
        ["uv", "lock", "--upgrade-package", "akshare"],
        cwd=_PROJECT_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


_background_update()
clean_expired()  # 启动时清理过期条目

# --- 重试配置 ---
RETRY_MAX = 3
RETRY_DELAY = 5

_RETRYABLE_ERRORS = (
    ConnectionError,
    TimeoutError,
    OSError,
)


def _is_retryable(e):
    """判断异常是否可重试（网络类错误）"""
    if isinstance(e, _RETRYABLE_ERRORS):
        return True
    msg = str(e).lower()
    return any(
        k in msg
        for k in [
            "connection",
            "remote",
            "disconnect",
            "timeout",
            "refused",
            "reset",
            "aborted",
        ]
    )


def _call_raw(func, func_name, kwargs):
    """调用 akshare API，网络错误自动重试"""
    for attempt in range(1, RETRY_MAX + 1):
        try:
            result = func(**kwargs)
            if attempt > 1:
                print(f"[重试成功] {func_name} 第{attempt}次调用成功", file=sys.stderr)
            return {"ok": True, "data": result}
        except Exception as e:
            if attempt < RETRY_MAX and _is_retryable(e):
                time.sleep(RETRY_DELAY)
                continue
            record_failure(func_name, e)
            return {
                "ok": False,
                "error": str(e),
                "function": func_name,
                "attempts": attempt,
            }


def call_api(func_name, **kwargs):
    """
    调用 akshare API，自动缓存、自动重试、自动转 DataFrame。

    参数：
        func_name: akshare API 名称，如 "stock_zt_pool_em"
        **kwargs: API 参数

    返回：
        pandas DataFrame（大多数 API）
        或 dict / list（无法转 DataFrame 时）

    异常：
        RuntimeError: API 调用失败时抛出

    示例：
        df = call_api("stock_zt_pool_em", date=20260317)
        df = call_api("stock_zh_a_hist", symbol="600519", period="daily",
                      start_date="20260101", end_date="20260317", adjust="qfq")
    """
    # 检查是否被 ban
    banned = check_banned(func_name)
    if isinstance(banned, dict):
        raise RuntimeError(f"API '{func_name}' 已被 ban: {banned.get('error', '')}")

    # 查找 akshare 函数
    func = getattr(ak, func_name, None)
    if func is None:
        raise AttributeError(f"akshare 中找不到 '{func_name}'")

    # 参数类型转换（字符串 → int/float）
    converted = {}
    for k, v in kwargs.items():
        if isinstance(v, str):
            with suppress(ValueError):
                v = int(v)
            if isinstance(v, str):
                with suppress(ValueError):
                    v = float(v)
        converted[k] = v

    # 先查缓存（pickle 反序列化，直接返回 DataFrame/dict/list）
    cached = cache_get(func_name, converted)
    if cached is not None:
        return cached

    # 调用 API
    result = _call_raw(func, func_name, converted)
    if not result["ok"]:
        raise RuntimeError(f"API '{func_name}' 调用失败: {result['error']}")

    data = result["data"]

    # 直接缓存原始对象（pickle 序列化）
    cache_set(func_name, converted, data)

    return data


def get_first_line(doc):
    """取 docstring 第一行"""
    if not doc:
        return ""
    for line in doc.split("\n"):
        line = line.strip()
        if line:
            return line[:200]
    return ""


def list_apis(keyword=""):
    """列出可用 API（banned 的自动隐藏）"""
    results = []
    keyword_lower = keyword.lower()
    for name in sorted(dir(ak)):
        if name.startswith("_") or is_banned(name):
            continue
        fn = getattr(ak, name)
        if not inspect.isfunction(fn):
            continue
        doc = get_first_line(fn.__doc__)
        if keyword_lower and keyword_lower not in name.lower() and keyword_lower not in doc.lower():
            continue
        results.append({"name": name, "desc": doc})
    return results


def get_info(func_name):
    """获取 API 详情"""
    banned = check_banned(func_name)
    if isinstance(banned, dict):
        return banned
    func = getattr(ak, func_name, None)
    if func is None:
        return {"error": f"Function '{func_name}' not found"}
    try:
        sig = inspect.signature(func)
        params = {}
        for pname, param in sig.parameters.items():
            pinfo = {
                "type": str(param.annotation)
                if param.annotation != inspect.Parameter.empty
                else "str"
            }
            if param.default != inspect.Parameter.empty:
                pinfo["default"] = str(param.default)
            else:
                pinfo["required"] = True
            params[pname] = pinfo
    except Exception:
        params = {}
    return {
        "name": func_name,
        "doc": (func.__doc__ or "").strip()[:500],
        "params": params,
    }


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print(
            json.dumps(
                {"error": "Usage: akcli <func> [k=v...] | --list [kw] | --info <func>"},
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    if sys.argv[1] == "--list":
        keyword = sys.argv[2] if len(sys.argv) > 2 else ""
        results = list_apis(keyword)
        print(json.dumps({"total": len(results), "apis": results}, ensure_ascii=False, indent=2))
        return

    if sys.argv[1] == "--info":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Usage: akcli --info <function_name>"}, ensure_ascii=False))
            sys.exit(1)
        print(json.dumps(get_info(sys.argv[2]), ensure_ascii=False, indent=2))
        return

    func_name = sys.argv[1]

    # 解析 key=value 参数
    kwargs = {}
    for arg in sys.argv[2:]:
        if "=" in arg:
            k, v = arg.split("=", 1)
            kwargs[k] = v

    try:
        df = call_api(func_name, **kwargs)
        # 输出 JSON
        if hasattr(df, "to_json"):
            raw = df.to_json(orient="records", date_format="iso", force_ascii=False) or "[]"
        else:
            raw = json.dumps(df, default=str, ensure_ascii=False)
        print(raw)
    except (RuntimeError, AttributeError) as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)
