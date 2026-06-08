"""
Valkey 缓存模块 — 直接缓存 pickle 二进制数据

akshare API 返回 pandas DataFrame，直接 pickle 序列化缓存，
保留完整类型信息（datetime、float、int），无需 JSON 转换。

缓存格式：akcli:<func_name>:<params_hash>:v<N>。版本变更时自动视为 miss。
"""

import hashlib
import pickle
import sys

from akcli.ttl import ttl as _get_ttl

_CACHE_VERSION = "v1"

try:
    import redis

    _r = redis.Redis(host="127.0.0.1", port=6379, socket_connect_timeout=2)
    _r.ping()
    _STORE = _r
except Exception:
    _STORE = None


def _key(func_name, kwargs):
    """生成缓存 key：akcli:<func_name>:<params_hash>:v<N>"""
    if not kwargs:
        return f"akcli:{func_name}:{_CACHE_VERSION}"
    import json

    kv = json.dumps(kwargs, sort_keys=True, ensure_ascii=False)
    h = hashlib.md5(kv.encode()).hexdigest()[:12]
    return f"akcli:{func_name}:{h}:{_CACHE_VERSION}"


def cache_get(func_name, kwargs):
    """从缓存读取，未命中返回 None。返回反序列化后的对象（DataFrame/dict/list）"""
    if _STORE is None:
        return None
    try:
        raw = _STORE.get(_key(func_name, kwargs))
        if raw is None:
            return None
        return pickle.loads(raw)
    except Exception as e:
        print(f"cache_get error: {e}", file=sys.stderr)
        return None


def cache_set(func_name, kwargs, data):
    """写入缓存（接受任意 Python 对象，pickle 序列化）"""
    if _STORE is None:
        return
    try:
        raw = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        _STORE.setex(_key(func_name, kwargs), _get_ttl(func_name, kwargs), raw)
    except Exception as e:
        print(f"cache_set error: {e}", file=sys.stderr)
