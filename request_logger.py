"""请求/响应日志 — 自动保存所有 HTTP 请求到 JSON 文件

在 session.py 的全局 Session 上挂载钩子，
每次请求完成时自动将 请求/响应 保存为 JSON。
"""
import json
import os
import time
from datetime import datetime

_LOG_DIR = os.path.join(os.path.dirname(__file__), "requests_log")
os.makedirs(_LOG_DIR, exist_ok=True)


def _safe_json(obj):
    """尝试将对象转为可 JSON 序列化的形式"""
    if obj is None:
        return None
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


def _parse_body(response) -> str | dict | list | None:
    """尝试解析响应体为 JSON，否则返回原始文本"""
    text = response.text
    if not text:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        # 截断过长的文本（超过 10KB 截取前后）
        if len(text) > 10_240:
            return {
                "_truncated": True,
                "length": len(text),
                "head": text[:5_000],
                "tail": text[-5_000:],
            }
        return text


def _parse_request_body(request) -> str | dict | list | None:
    """尝试解析请求体"""
    body = getattr(request, "body", None)
    if not body:
        return None
    try:
        text = body.decode("utf-8")
    except (UnicodeDecodeError, AttributeError):
        try:
            text = body.decode("gbk")
        except (UnicodeDecodeError, AttributeError):
            text = str(body)
    if not text:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return text


def _cookies_dict(cookies) -> dict:
    """将 RequestsCookieJar 转为普通 dict"""
    return {c.name: c.value for c in cookies}


def _headers_dict(headers) -> dict:
    """将 CaseInsensitiveDict 转为普通 dict"""
    return dict(headers)


def request_logger(response, *args, **kwargs):
    """requests.Session 事件钩子 — 每次请求完成后调用

    用法: session.hooks["response"].append(request_logger)
    """
    try:
        req = response.request
        ts = datetime.now().isoformat(timespec="milliseconds")

        # 过滤掉下载加密 JS 本身的请求（不生成日志）
        if "/common/security-js/" in req.url:
            return

        log_entry = {
            "timestamp": ts,
            "duration_ms": round(response.elapsed.total_seconds() * 1000, 1),
            "request": {
                "method": req.method,
                "url": req.url,
                "headers": _headers_dict(req.headers),
            },
            "response": {
                "status_code": response.status_code,
                "headers": _headers_dict(response.headers),
                "body": _parse_body(response),
            },
            "cookies": {
                "request": _cookies_dict(req._cookies) if hasattr(req, "_cookies") and req._cookies is not None else {},
                "response": _cookies_dict(response.cookies),
            },
        }

        # 请求参数 / 体
        if req.method == "GET":
            log_entry["request"]["params"] = _safe_json(
                dict(req.params) if hasattr(req, "params") and req.params else {}
            )
        else:
            log_entry["request"]["body"] = _parse_request_body(req)

        # 文件名: 时间戳_状态码_简短路径.json
        from urllib.parse import urlparse
        parsed = urlparse(req.url)
        short_path = parsed.path.strip("/").replace("/", "_") or "root"
        safe_path = "".join(c if c.isalnum() or c in "-_" else "_" for c in short_path)[:60]
        filename = f"{time.strftime('%H%M%S')}_{response.status_code}_{safe_path}.json"
        filepath = os.path.join(_LOG_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, ensure_ascii=False, indent=2)
    except Exception as e:
        # 日志模块自身永不崩溃，防止干扰正常请求
        print(f"[request_logger] 保存日志失败: {e}", file=__import__('sys').stderr)
