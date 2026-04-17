"""
自动 Ban 检测模块

功能：
- 管理手动 ban 列表（blocked.json → BANNED_APIS）
- 追踪 API 调用失败次数
- 连续失败达到阈值后自动 ban（写入 state file）
- 被 ban 的 API 过期后自动解封，下次调用时重试
- 仅对网络级错误（连接拒绝、重置、超时）触发，不影响参数错误等

用法：
    from akcli.auto_ban import is_banned, check_banned, record_failure, clean_expired
"""

import json
import os
from datetime import UTC, datetime, timedelta

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_BLOCKED_FILE = os.path.join(_DATA_DIR, "blocked.json")


# 运行时数据：~/.local/share/akcli/
def _state_dir():
    d = os.path.join(os.path.expanduser("~"), ".local", "share", "akcli")
    os.makedirs(d, exist_ok=True)
    return d


_STATE_FILE = os.path.join(_state_dir(), "auto_blocked.json")

# --- 手动 ban 列表 ---
BANNED_APIS = {}
if os.path.exists(_BLOCKED_FILE):
    with open(_BLOCKED_FILE) as _f:
        BANNED_APIS = json.load(_f)

# --- 配置 ---
FAIL_THRESHOLD = 3  # 连续失败 N 次后自动 ban
BAN_DURATION_HOURS = 24  # 自动 ban 持续时间（小时）

_BAN_ERROR_TYPES = (
    ConnectionRefusedError,
    ConnectionResetError,
    TimeoutError,
    OSError,
)


def _load():
    if os.path.exists(_STATE_FILE):
        with open(_STATE_FILE) as f:
            return json.load(f)
    return {}


def _save(data):
    with open(_STATE_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _now():
    return datetime.now(UTC)


def _is_network_ban_error(e):
    return isinstance(e, _BAN_ERROR_TYPES)


def is_banned(name):
    """检查 API 是否被 ban（手动 + 自动）"""
    return name in BANNED_APIS or is_auto_banned(name)


def check_banned(name):
    """
    统一 ban 检查入口。
    返回 None 表示未被 ban；返回 dict 表示被 ban（可直接作为错误输出）。
    """
    if name in BANNED_APIS:
        return {"error": f"API '{name}' 已被 ban", "use": BANNED_APIS[name]}
    if is_auto_banned(name):
        return {
            "error": f"API '{name}' 因连续网络错误已被临时 ban，请稍后重试或使用其他 API"
        }
    return None


def is_auto_banned(name):
    """检查 API 是否处于自动 ban 状态（未过期则返回 True）"""
    data = _load()
    entry = data.get(name)
    if not entry or "expires" not in entry:
        return False
    expires = datetime.fromisoformat(entry["expires"])
    if _now() > expires:
        del data[name]
        _save(data)
        return False
    return True


def record_failure(name, error):
    """
    记录一次 API 调用失败。
    仅对网络级错误计数；非网络错误忽略。
    达到阈值后写入 state file。
    """
    if not _is_network_ban_error(error):
        return

    data = _load()
    entry = data.get(name, {"failures": 0})
    entry["failures"] = entry.get("failures", 0) + 1
    entry["last_error"] = str(error)
    entry["last_time"] = _now().isoformat()

    if entry["failures"] >= FAIL_THRESHOLD:
        entry["banned_at"] = _now().isoformat()
        entry["expires"] = (_now() + timedelta(hours=BAN_DURATION_HOURS)).isoformat()
        entry["reason"] = f"连续 {entry['failures']} 次网络错误自动 ban"

    data[name] = entry
    _save(data)


def clean_expired():
    """清理所有已过期的自动 ban 条目，返回清理数量"""
    data = _load()
    now = _now()
    expired = [
        k
        for k, v in data.items()
        if "expires" in v and now > datetime.fromisoformat(v["expires"])
    ]
    for k in expired:
        del data[k]
    if expired:
        _save(data)
    return len(expired)
