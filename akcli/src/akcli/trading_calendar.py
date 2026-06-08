"""
交易日历模块

从 akshare 获取 A 股交易日历，缓存到 Valkey（Redis）。
存储格式：key=akcli:cal:{year}, type=set, members=日期字符串

用法：
    from akcli.calendar import is_trading_day, next_trading_day
"""

import json
import os
import subprocess
from datetime import datetime, timedelta, timezone

try:
    import redis

    _r = redis.Redis(
        host="127.0.0.1", port=6379, decode_responses=True, socket_connect_timeout=2
    )
    _r.ping()
    _STORE = _r
except Exception:
    _STORE = None

_CN_TZ = timezone(timedelta(hours=8))
_CACHE_TTL = 365 * 86400  # 1 年


def _fetch_year(year):
    """通过 uv run 获取指定年份的交易日列表"""
    code = (
        "import json, akshare as ak;"
        f" df = ak.tool_trade_date_hist_sina();"
        f' dates = df["trade_date"].astype(str).tolist();'
        f' print(json.dumps([d for d in dates if d.startswith("{year}")]))'
    )
    # 找到项目根目录（包含 pyproject.toml 的目录）
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    try:
        result = subprocess.run(
            ["uv", "run", "python", "-c", code],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=project_dir,
        )
        if result.returncode == 0:
            return json.loads(result.stdout.strip())
    except Exception:
        pass
    return None


def _ensure_year(year):
    """确保年份数据在 Valkey 中"""
    if _STORE is None:
        return
    key = f"akcli:cal:{year}"
    if _STORE.exists(key):
        return
    dates = _fetch_year(year)
    if dates:
        pipe = _STORE.pipeline()
        pipe.sadd(key, *dates)
        pipe.expire(key, _CACHE_TTL)
        pipe.execute()


def is_trading_day(dt=None):
    """判断是否为交易日"""
    if dt is None:
        dt = datetime.now(_CN_TZ)
    if _STORE is None:
        # Valkey 不可用：回退到简单工作日判断
        return dt.weekday() < 5
    _ensure_year(dt.year)
    return _STORE.sismember(f"akcli:cal:{dt.year}", dt.strftime("%Y-%m-%d"))


def next_trading_day(dt=None):
    """找到下一个交易日"""
    if dt is None:
        dt = datetime.now(_CN_TZ)
    d = dt + timedelta(days=1)
    for _ in range(30):
        if is_trading_day(d):
            return d
        d += timedelta(days=1)
    return d


def prev_trading_day(dt=None):
    """找到上一个交易日"""
    if dt is None:
        dt = datetime.now(_CN_TZ)
    d = dt - timedelta(days=1)
    for _ in range(30):
        if is_trading_day(d):
            return d
        d -= timedelta(days=1)
    return d
