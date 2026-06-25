"""统一 HTTP 会话管理 — 全局共享的 requests.Session

所有 API 模块共用同一个 session，包含统一的 Headers 和 Cookies。
Header/Cookie 数据从 header.json 加载，但以下字段会自动更新：
  - traceId             → 实时生成（内嵌时间戳）
  - Referer 中的 _security_check → 实时生成（内嵌时间戳）
如需更新 Cookie（如 __zp_stoken__ 刷新），调用 refresh_stoken()。
如需手动刷新时间相关字段，调用 refresh_timestamp_fields()。

所有请求/响应自动保存为 JSON 文件到 requests_log/ 目录。
"""
import json
import os
import re
import time

import requests
from urllib.parse import quote

from request_logger import request_logger
from webJs.traceid import generate as _generate_traceid

# ===== 从 JSON 加载配置 =====
_json_path = os.path.join(os.path.dirname(__file__), "header.json")
with open(_json_path, encoding="utf-8") as _f:
    _config = json.load(_f)

# ===== 全局会话 =====
session = requests.Session()

# ===== 挂载请求日志钩子（所有请求自动保存为 JSON）=====
session.hooks["response"].append(request_logger)

# ===== 统一请求头 =====
session.headers.update(_config["headers"])

# ===== 用实时值覆盖静态时间相关字段 =====
def _now_ms() -> int:
    return int(time.time() * 1000)


def _update_security_check() -> None:
    """刷新 Referer 中的 _security_check 时间戳"""
    referer = session.headers.get("Referer", "")
    if not referer:
        return
    new_referer = re.sub(
        r"_security_check=\d+_\d+",
        f"_security_check=1_{_now_ms()}",
        referer,
    )
    if new_referer != referer:
        session.headers["Referer"] = new_referer


def refresh_timestamp_fields() -> None:
    """刷新所有与时间相关的字段（traceId + _security_check）

    每次请求前应调用此方法，确保 traceId 和 Referer 中的
    _security_check 时间戳与当前时间同步。
    """
    session.headers["traceId"] = _generate_traceid()
    _update_security_check()


# 模块加载时立即刷新一次
refresh_timestamp_fields()

# ===== 统一初始 Cookie =====
_initial_cookies = _config["_initial_cookies"]

for name, value in _initial_cookies.items():
    session.cookies.set(name, value, domain="www.zhipin.com", path="/")


def refresh_traceid() -> str:
    """生成新的 traceId 并更新到请求头，同时返回该值"""
    tid = _generate_traceid()
    session.headers["traceId"] = tid
    return tid


def refresh_stoken(stoken: str) -> None:
    """刷新 __zp_stoken__ 到会话 cookie

    Args:
        stoken: 新生成的 stoken 值（由 stoken 模块提供）
    """
    encoded = quote(stoken, safe="")
    session.cookies.set("__zp_stoken__", encoded, domain="www.zhipin.com", path="/")


def update_headers(**kwargs) -> None:
    """动态更新请求头（同时自动刷新 traceId 和 _security_check 以同步时间）"""
    refresh_timestamp_fields()
    session.headers.update(kwargs)
