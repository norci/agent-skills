"""
TTL 计算模块

支持两种 TTL 策略：
1. 静态规则：从 ttl_rules.json 加载，按 API 名 + 参数匹配
2. 动态计算：历史数据（日K/周K/月K/分钟K）按数据更新时间计算

交易日历从 akcli.trading_calendar 获取（Valkey 缓存）。
"""

import json
import os
from datetime import datetime, timedelta, timezone

from akcli.trading_calendar import is_trading_day, next_trading_day

_CN_TZ = timezone(timedelta(hours=8))

_RULES_FILE = os.path.join(os.path.dirname(__file__), "ttl_rules.json")

# ============================================================
# 静态规则
# ============================================================

_API_TTL = {}  # {api_name: ttl_seconds}
_DEFAULT_TTL = 1800
_PARAM_TTL = {}  # {api_name: {tuple(sorted(params.items())): ttl}}


def _load_rules():
    try:
        with open(_RULES_FILE) as f:
            data = json.load(f)
        for group in data["rules"]:
            ttl = group["ttl"]
            for api in group.get("apis", []):
                _API_TTL[api] = ttl
        for pr in data.get("param_rules", []):
            api = pr["api"]
            if api not in _PARAM_TTL:
                _PARAM_TTL[api] = {}
            for p in pr["params"]:
                _PARAM_TTL[api][tuple(sorted(p.items()))] = pr["ttl"]
    except Exception:
        pass


_load_rules()


# ============================================================
# 交易时段工具
# ============================================================

AM_START = 9 * 60 + 30  # 9:30
AM_END = 11 * 60 + 30  # 11:30
PM_START = 13 * 60  # 13:00
PM_END = 15 * 60  # 15:00


def _in_trading_hour(dt):
    """是否在交易时段内（9:30-11:30, 13:00-15:00）"""
    if not is_trading_day(dt):
        return False
    t = dt.hour * 60 + dt.minute
    return (AM_START <= t <= AM_END) or (PM_START <= t <= PM_END)


def _total_min(dt):
    """当天已过分钟数"""
    return dt.hour * 60 + dt.minute


# ============================================================
# 日/周/月 动态 TTL
# ============================================================


def _last_trading_day_in_week(dt):
    """本周（周一到周日）最后一个交易日"""
    mon = dt - timedelta(days=dt.weekday())
    for i in range(6, -1, -1):
        d = mon + timedelta(days=i)
        if is_trading_day(d):
            return d
    return dt


def _last_trading_day_in_month(dt):
    """当月最后一个交易日"""
    if dt.month == 12:
        nxt = datetime(dt.year + 1, 1, 1, tzinfo=_CN_TZ)
    else:
        nxt = datetime(dt.year, dt.month + 1, 1, tzinfo=_CN_TZ)
    d = nxt - timedelta(days=1)
    for _ in range(31):
        if is_trading_day(d):
            return d
        d -= timedelta(days=1)
    return dt


def _at_close(dt):
    """dt 的当天 15:30"""
    return dt.replace(hour=15, minute=30, second=0, microsecond=0)


def _daily_next_update(dt):
    """日K：交易日 15:30，非交易日跳到下个交易日"""
    if not is_trading_day(dt):
        return _at_close(next_trading_day(dt))
    close = _at_close(dt)
    if dt < close:
        return close
    return _at_close(next_trading_day(dt))


def _weekly_next_update(dt):
    """周K：本周最后一个交易日 15:30"""
    last = _last_trading_day_in_week(dt)
    close = _at_close(last)
    if dt < close:
        return close
    nxt_mon = last + timedelta(days=(7 - last.weekday()))
    return _at_close(_last_trading_day_in_week(nxt_mon))


def _monthly_next_update(dt):
    """月K：当月最后一个交易日 15:30"""
    last = _last_trading_day_in_month(dt)
    close = _at_close(last)
    if dt < close:
        return close
    if dt.month == 12:
        mid = datetime(dt.year + 1, 1, 15, tzinfo=_CN_TZ)
    else:
        mid = datetime(dt.year, dt.month + 1, 15, tzinfo=_CN_TZ)
    return _at_close(_last_trading_day_in_month(mid))


# ============================================================
# 分钟级动态 TTL
# ============================================================


def _next_bar_boundary(dt, minutes):
    """当前交易时段内，下一根 K 线 bar 的边界"""
    t = _total_min(dt)
    if AM_START <= t <= AM_END:
        rel = t - AM_START
        nxt_rel = ((rel // minutes) + 1) * minutes
        if nxt_rel <= AM_END - AM_START:
            nxt = AM_START + nxt_rel
            return dt.replace(hour=nxt // 60, minute=nxt % 60, second=0, microsecond=0)
        return dt.replace(hour=13, minute=0, second=0, microsecond=0)
    elif PM_START <= t <= PM_END:
        rel = t - PM_START
        nxt_rel = ((rel // minutes) + 1) * minutes
        if nxt_rel <= PM_END - PM_START:
            nxt = PM_START + nxt_rel
            return dt.replace(hour=nxt // 60, minute=nxt % 60, second=0, microsecond=0)
        return None  # 下午最后一个 bar
    return None


def _first_bar_time(trading_day, minutes):
    """找到某交易日的第一个 bar 起点"""
    am = AM_START  # 9:30
    bar_min = am if am % minutes == 0 else ((am // minutes) + 1) * minutes
    return trading_day.replace(hour=bar_min // 60, minute=bar_min % 60, second=0, microsecond=0)


def _minute_ttl(func_name, kwargs):
    """分钟级数据 TTL"""
    now = datetime.now(_CN_TZ)

    period = kwargs.get("period") if kwargs else None
    try:
        mins = int(period) if period else 5
        if mins not in (1, 5, 15, 30, 60):
            mins = 5
    except (ValueError, TypeError):
        mins = 5

    td = is_trading_day(now)
    th = td and _in_trading_hour(now)

    if th:
        nxt = _next_bar_boundary(now, mins)
        if nxt is not None:
            return max(int((nxt - now).total_seconds()), 60)

    # 非交易时段
    if not td:
        nxt_day = next_trading_day(now)
    else:
        tm = _total_min(now)
        if tm < AM_START:  # 盘前
            nxt_day = now
        elif tm >= PM_END:  # 盘后
            nxt_day = next_trading_day(now)
        else:  # 午休 11:30-13:00
            nxt = now.replace(hour=13, minute=0, second=0, microsecond=0)
            return max(int((nxt - now).total_seconds()), 60)

    open_t = _first_bar_time(nxt_day, mins)
    return max(int((open_t - now).total_seconds()), 60)


# ============================================================
# 统一入口
# ============================================================


def _dynamic_ttl(func_name, kwargs):
    """历史/实时数据动态 TTL"""
    now = datetime.now(_CN_TZ)

    # 实时行情：30s
    if "_spot" in func_name or "_realtime" in func_name or "_intraday" in func_name:
        return 30

    # 分钟级数据：动态计算到下根 bar
    if "_hist_min" in func_name or "_minute" in func_name:
        return _minute_ttl(func_name, kwargs)

    # 日/周/月 历史数据
    period = kwargs.get("period") if kwargs else None

    if "_daily" in func_name or "_weekly" in func_name or "_monthly" in func_name:
        if "_weekly" in func_name:
            nxt = _weekly_next_update(now)
        elif "_monthly" in func_name:
            nxt = _monthly_next_update(now)
        else:
            nxt = _daily_next_update(now)
    elif "_hist" in func_name:
        if period == "weekly":
            nxt = _weekly_next_update(now)
        elif period == "monthly":
            nxt = _monthly_next_update(now)
        else:
            nxt = _daily_next_update(now)
    else:
        return None

    return max(int((nxt - now).total_seconds()), 60)


def ttl(func_name, kwargs=None):
    """
    统一 TTL 入口。
    返回 TTL 秒数。
    """
    # 动态 TTL（历史数据）
    dynamic = _dynamic_ttl(func_name, kwargs)
    if dynamic is not None:
        return dynamic

    # 参数级规则
    if kwargs and func_name in _PARAM_TTL:
        key = tuple(sorted(kwargs.items()))
        if key in _PARAM_TTL[func_name]:
            return _PARAM_TTL[func_name][key]

    # 显式列表
    if func_name in _API_TTL:
        return _API_TTL[func_name]

    # 默认
    return _DEFAULT_TTL
