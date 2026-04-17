#!/usr/bin/env python3
"""BaoStock helper for agents: wrap login/logout and ResultSet parsing."""

import contextlib
import inspect
import io
import json
import sys

import baostock as bs


class BaoStockError(RuntimeError):
    pass


def _first_line(doc):
    if not doc:
        return ""
    for line in doc.splitlines():
        line = line.strip()
        if line:
            return line[:200]
    return ""


def apis(keyword=""):
    keyword = keyword.lower()
    rows = []
    for name in sorted(dir(bs)):
        func = getattr(bs, name)
        if name.startswith("_") or not callable(func) or not inspect.isfunction(func):
            continue
        desc = _first_line(func.__doc__)
        if keyword and keyword not in name.lower() and keyword not in desc.lower():
            continue
        rows.append({"name": name, "desc": desc})
    return rows


def info(name):
    func = getattr(bs, name, None)
    if func is None:
        raise BaoStockError(f"Function not found: {name}")
    try:
        params = {
            pname: {
                "default": None if param.default is inspect.Parameter.empty else param.default,
                "required": param.default is inspect.Parameter.empty,
            }
            for pname, param in inspect.signature(func).parameters.items()
        }
    except (TypeError, ValueError):
        params = {}
    return {"name": name, "doc": (func.__doc__ or "").strip(), "params": params}


def result_to_data(result):
    if hasattr(result, "error_code"):
        if result.error_code != "0":
            raise BaoStockError(result.error_msg)
        rows = []
        while result.next():
            rows.append(dict(zip(result.fields, result.get_row_data())))
        return rows
    if hasattr(result, "to_dict"):
        return result.to_dict(orient="records")
    return result


def call(name, **kwargs):
    func = getattr(bs, name, None)
    if func is None:
        raise BaoStockError(f"Function not found: {name}")

    sink = io.StringIO()
    with contextlib.redirect_stdout(sink):
        login = bs.login()
    if login.error_code != "0":
        raise BaoStockError(login.error_msg)

    try:
        return result_to_data(func(**kwargs))
    finally:
        with contextlib.redirect_stdout(sink):
            bs.logout()


def _parse_kwargs(args):
    kwargs = {}
    for arg in args:
        key, value = arg.split("=", 1)
        kwargs[key] = value
    return kwargs


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: baostock_cli.py <func> [k=v...] | --list [kw] | --info <func>")

    if sys.argv[1] == "--list":
        keyword = sys.argv[2] if len(sys.argv) > 2 else ""
        print(json.dumps({"total": len(apis(keyword)), "apis": apis(keyword)}, ensure_ascii=False, indent=2))
        return

    if sys.argv[1] == "--info":
        print(json.dumps(info(sys.argv[2]), ensure_ascii=False, indent=2, default=str))
        return

    print(json.dumps(call(sys.argv[1], **_parse_kwargs(sys.argv[2:])), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
