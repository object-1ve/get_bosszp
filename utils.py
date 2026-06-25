"""通用工具函数 — 安全类型转换等"""
import json
from typing import Any


def s(v: Any) -> str:
    """安全转字符串，None → ''"""
    if v is None:
        return ''
    if isinstance(v, bool):
        return '1' if v else '0'
    return str(v)


def i(v: Any) -> int:
    """安全转 int，None/'' → 0；bool True→1"""
    if v is None:
        return 0
    if isinstance(v, bool):
        return 1 if v else 0
    try:
        return int(v)
    except (ValueError, TypeError):
        return 0


def f(v: Any) -> float:
    """安全转 float，None/'' → 0.0"""
    if v is None:
        return 0.0
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def j(v: Any) -> str:
    """列表或字典 → JSON 字符串；None → 'null'"""
    if v is None:
        return 'null'
    if isinstance(v, (list, tuple, dict)):
        return json.dumps(v, ensure_ascii=False)
    return s(v)


def safe_filename(text: str, max_len: int = 40) -> str:
    """将字符串转为安全的文件名片段"""
    safe = "".join(c if c.isalnum() or c in " _-.()[]" else "_" for c in text)
    safe = safe.strip().rstrip(".-")
    if not safe:
        safe = "unknown"
    return safe[:max_len]


def wcwidth(c: str) -> int:
    """返回单个字符的终端显示宽度（CJK 全角=2，其他=1）"""
    o = ord(c)
    if 0x4e00 <= o <= 0x9fff or 0x3000 <= o <= 0x303f or 0xff00 <= o <= 0xffef:
        return 2
    return 1


def vis_width(s: str) -> int:
    """返回字符串的终端显示宽度"""
    return sum(wcwidth(ch) for ch in s)


def pad(s: str, width: int) -> str:
    """将 s 填充/截断到指定终端显示宽度（CJK 适配），左对齐

    超过宽度的部分自动截断并追加 "..."（占用 3 列宽度），
    确保表格 | 纵向对齐。
    """
    s = str(s) if s is not None else ""
    cur = vis_width(s)
    if cur <= width:
        return s + " " * (width - cur)

    # 超过宽度 → 截断 + 省略号
    ELLIPSIS_W = 3  # "..." 的显示宽度
    if width <= ELLIPSIS_W:
        return "." * width if width > 0 else ""

    avail = width - ELLIPSIS_W  # 留给实际内容的宽度
    truncated = ""
    w = 0
    for ch in s:
        cw = wcwidth(ch)
        if w + cw > avail:
            break
        truncated += ch
        w += cw
    return truncated + "..."
