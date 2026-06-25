"""
BOSS直聘 TraceID 工具
====================
原生 Python 实现，无需 JS 运行时。

功能:
    generate()  — 生成 F- 开头的 TraceID（对应 JS 的 generateBossTraceID）
    decode(id)  — 从 TraceID 反解创建时间（对应 JS 的 getTimeFromBossTraceID）
"""

import time
import random
import string


def generate() -> str:
    """
    生成 BOSS 直聘 TraceID

    JS 原型:
        function generateBossTraceID() {
            var hexTs = Date.now().toString(16);          // 当前时间戳转 hex
            var rand = ""; for (var i=0;i<10;i++)         // 10位随机字符
                rand += "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"[Math.floor(62 * Math.random())];
            return "F-" + hexTs.slice(-6) + rand;
        }
    """
    # 当前毫秒时间戳 -> hex，取后6位
    hex_ts = hex(int(time.time() * 1000))[2:]       # 去掉 "0x" 前缀
    if len(hex_ts) < 6:                             # 补零至至少6位
        hex_ts = hex_ts.zfill(6)
    ts_part = hex_ts[-6:]                           # 取最后6位

    # 10位随机字符 (62进制字符集)
    chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    rand_part = "".join(random.choice(chars) for _ in range(10))

    return f"F-{ts_part}{rand_part}"


def decode(trace_id: str, now: int | None = None) -> float | None:
    """
    从 TraceID 反解创建时间戳（毫秒）

    参数:
        trace_id: 如 "F-0019efede5ff913M1KkEXC"
        now:      可指定"当前时间"（毫秒时间戳），默认 time.time()*1000

    返回:
        毫秒时间戳 (float)，解析失败返回 None

    原理:
        算法见 JS 的 getTimeFromBossTraceID:
            var n = id.slice(2, 8);               // 6位 hex 时间偏移
            var t = parseInt(n, 16);              // -> 毫秒偏移量 (0~16777215)
            var o = Date.now();                   // 当前时间
            var r = o.toString(16).slice(-6);     // 当前时间的最后6位hex
            var a = o - parseInt(r, 16);          // 对齐到当前16.78s窗口的起点
            return new Date(a + t);               // 窗口起点 + 偏移量

    精度:
        只能在 16.78 秒窗口内正确解码（0x1000000 ms ≈ 16.78s）。
        TraceID 生成后尽快解码结果才准确，隔太久解码会对齐到新的窗口。
    """
    if not trace_id or not trace_id.startswith("F-"):
        return None

    if now is None:
        now = time.time() * 1000

    hex_offset = trace_id[2:8]                      # 第2-8位 = 6位hex
    if len(hex_offset) != 6 or not all(c in "0123456789abcdefABCDEF" for c in hex_offset):
        return None

    offset_ms = int(hex_offset, 16)                 # 毫秒偏移 0~16777215

    now_hex = hex(int(now))[2:]                     # 当前时间戳转hex
    if len(now_hex) < 6:
        now_hex = now_hex.zfill(6)
    now_last6 = now_hex[-6:]

    window_start = int(now) - int(now_last6, 16)    # 对齐到当前窗口起点
    return window_start + offset_ms


def decode_to_datetime(trace_id: str) -> str | None:
    """
    反解时间并以可读字符串返回

    参数:
        trace_id: 如 "F-0019efede5ff913M1KkEXC"

    返回:
        格式化的时间字符串，如 "2026-06-25 16:58:00.047"
    """
    from datetime import datetime

    ms = decode(trace_id)
    if ms is None:
        return None

    dt = datetime.fromtimestamp(ms / 1000)
    return dt.strftime("%Y-%m-%d %H:%M:%S.") + f"{int(ms % 1000):03d}"


# ---------------------------------------------------------------
# 快捷入口
# ---------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2 and sys.argv[1] in ("-d", "--decode"):
        # python traceid.py -d F-xxx
        for tid in sys.argv[2:]:
            result = decode_to_datetime(tid)
            if result:
                print(f"{tid}  ->  {result}")
            else:
                print(f"{tid}  ->  解析失败")
    else:
        # python traceid.py          → 生成一个
        # python traceid.py -n 5     → 生成5个
        count = 1
        if len(sys.argv) >= 3 and sys.argv[1] == "-n":
            count = int(sys.argv[2])

        for i in range(count):
            tid = generate()
            dt = decode_to_datetime(tid)
            print(f"{tid}  ({dt})")
