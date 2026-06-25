"""__zp_stoken__ 生成器 — 封装 Playwright 无头浏览器

根据 __zp_sname__ cookie 动态下载并执行对应的加密 JS 文件，
在真实浏览器环境中执行 {sname}.js 中的 ABC.z() 生成 stoken。
全局只维护一个浏览器实例，支持懒加载和关闭。

__zp_sseed__ / __zp_sname__ / __zp_sts__ 从 API 响应 Set-Cookie 中捕获，
在模块级内存中维护，而非依赖 session 请求 cookie。
"""
import os
import time

try:
    from playwright.sync_api import sync_playwright
    _HAS_PLAYWRIGHT = True
except ImportError:
    sync_playwright = None
    _HAS_PLAYWRIGHT = False

import requests

# webJs/ 目录位于 getDataNext 目录下
_WEB_JS_DIR = os.path.join(os.path.dirname(__file__), "webJs")
os.makedirs(_WEB_JS_DIR, exist_ok=True)

# JS 下载地址模板
_JS_DOWNLOAD_URL = "https://www.zhipin.com/web/common/security-js/{sname}.js"

# 全局浏览器实例（懒加载，复用）
_BROWSER = None
_PAGE = None
_PLAYWRIGHT = None
_CURRENT_SNAME = None  # 当前页面已加载的 sname

# ===== 内存缓存：从 API 响应 Set-Cookie 捕获的参数 =====
# 不从 session.cookies（请求 cookie）读取，而是从响应的 Set-Cookie 维护
_cache_sseed: str | None = None  # __zp_sseed__
_cache_sname: str | None = None  # __zp_sname__
_cache_sts: int | None = None    # __zp_sts__


# ===== 从响应捕获 stoken 参数 =====

def update_params_from_response(response) -> None:
    """从 API 响应的 Set-Cookie 中捕获 __zp_sseed__ / __zp_sname__ / __zp_sts__

    BOSS 直聘的某些 API 响应会在 Set-Cookie 中下发 stoken 加密参数，
    这些值不会出现在请求 cookie 中，必须从响应 cookie 捕获并维护在内存中。

    此外，code=37 的响应还会在 JSON body 的 zpData 中下发
    seed/ts/name，也会一并捕获。

    Args:
        response: requests.Response 实例
    """
    global _cache_sseed, _cache_sname, _cache_sts
    resp_cookies = response.cookies
    changed = []

    # 来源一：Set-Cookie（正常轮换时）
    sseed = resp_cookies.get("__zp_sseed__")
    if sseed:
        _cache_sseed = sseed
        changed.append("sseed")

    sname = resp_cookies.get("__zp_sname__")
    if sname:
        _cache_sname = sname
        changed.append("sname")

    sts = resp_cookies.get("__zp_sts__")
    if sts:
        try:
            _cache_sts = int(sts)
            changed.append("sts")
        except (ValueError, TypeError):
            pass

    # 来源二：JSON body 的 zpData（code=37 时，参数只在这里）
    try:
        body = response.json()
    except Exception:
        body = None
    if isinstance(body, dict) and body.get("code") == 37:
        zp = body.get("zpData", {})
        seed_body = zp.get("seed")
        ts_body = zp.get("ts")
        name_body = zp.get("name")
        if seed_body and not _cache_sseed:
            _cache_sseed = seed_body
            changed.append("sseed(body)")
        if name_body and not _cache_sname:
            _cache_sname = name_body
            changed.append("sname(body)")
        if ts_body:
            try:
                ts_int = int(ts_body)
                if _cache_sts is None:
                    _cache_sts = ts_int
                    changed.append("sts(body)")
            except (ValueError, TypeError):
                pass

    if changed:
        print(f"[stoken] 捕获参数: {', '.join(changed)}")


def get_cached_params() -> tuple:
    """获取内存缓存的 stoken 参数

    Returns:
        (seed, ts, sname) 三元组，缺失的值为 None
    """
    return _cache_sseed, _cache_sts, _cache_sname


def is_available() -> bool:
    """检查 Playwright 是否可用"""
    return _HAS_PLAYWRIGHT


def _js_path(sname: str) -> str:
    """返回对应 sname 的 JS 文件路径"""
    return os.path.join(_WEB_JS_DIR, f"{sname}.js")


def _download_js(sname: str) -> str:
    """下载 sname.js 到 webJs 目录（若不存在）

    Args:
        sname: __zp_sname__ 值（如 11859538）

    Returns:
        JS 文件路径
    """
    path = _js_path(sname)
    if os.path.exists(path):
        return path

    url = _JS_DOWNLOAD_URL.format(sname=sname)
    print(f"[stoken] 下载加密脚本: {url}")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    with open(path, "w", encoding="utf-8") as f:
        f.write(resp.text)

    print(f"[stoken] 已保存: {path}")
    return path


def _ensure_page(sname: str = "11859538"):
    """懒加载: 初始化并复用同一个浏览器页面

    当 sname 与上次不同时，自动重新加载对应 JS 文件。

    Args:
        sname: __zp_sname__ 值
    """
    global _BROWSER, _PAGE, _PLAYWRIGHT, _CURRENT_SNAME
    if not _HAS_PLAYWRIGHT:
        raise RuntimeError("playwright 未安装: pip install playwright && playwright install chromium")

    # 确保 JS 文件已下载
    js_path = _download_js(sname)

    if _PAGE is None:
        # 首次初始化浏览器
        _PLAYWRIGHT = sync_playwright().start()
        _BROWSER = _PLAYWRIGHT.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        _PAGE = _BROWSER.new_page()

        # 移除 webdriver 属性，伪装真实浏览器
        _PAGE.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true,
            });
            window.chrome = { runtime: {} };
            if (navigator.permissions) {
                const origQuery = navigator.permissions.query;
                navigator.permissions.query = (p) => Promise.resolve({state: 'granted', onchange: null});
            }
        """)

        # 访问空白页初始化环境
        _PAGE.goto("about:blank")
        _PAGE.set_content("<!DOCTYPE html><html><body></body></html>")

        # 加载 JS 加密模块
        with open(js_path, "r", encoding="utf-8") as f:
            js_code = f.read()
        _PAGE.evaluate(js_code)
        _CURRENT_SNAME = sname
    elif sname != _CURRENT_SNAME:
        # sname 变了 → 重新加载新 JS 文件到干净的页面上下文
        _PAGE.goto("about:blank")
        _PAGE.set_content("<!DOCTYPE html><html><body></body></html>")
        with open(js_path, "r", encoding="utf-8") as f:
            js_code = f.read()
        _PAGE.evaluate(js_code)
        _CURRENT_SNAME = sname

    return _PAGE


def generate_stoken(seed: str, ts: int, sname: str = "11859538") -> str:
    """在 Playwright 浏览器中执行 ABC.z() 生成 stoken

    Args:
        seed: __zp_sseed__ 值
        ts: __zp_sts__ 时间戳
        sname: __zp_sname__ 值，用于确定加载哪个加密 JS 文件

    Returns:
        stoken 字符串
    """
    page = _ensure_page(sname)

    stoken = page.evaluate(
        """([seed, ts]) => {
            try {
                var adjusted = parseInt(ts) + (480 + new Date().getTimezoneOffset()) * 60000;
                var abc = new ABC();
                var r = abc.z(seed, adjusted);
                return String(r);
            } catch (e) {
                return "ERROR: " + (e.message || e);
            }
        }""",
        [seed, ts],
    )
    return stoken


def refresh_stoken_and_set_cookie(seed: str, ts: int, session, sname: str = None) -> str:
    """生成 stoken 并设置到 session cookie，返回 stoken 值

    同时更新 __zp_sseed__、__zp_sts__、__zp_sname__ cookie 和内存缓存，
    确保后续请求使用最新的加密参数。

    Args:
        seed: __zp_sseed__ 值
        ts: __zp_sts__ 时间戳
        session: requests.Session 实例
        sname: __zp_sname__ 值；若为 None 则从 session cookie 读取

    Returns:
        生成的 stoken 字符串
    """
    from urllib.parse import quote

    if sname is None:
        sname = session.cookies.get("__zp_sname__", domain="www.zhipin.com")
    if not sname:
        raise ValueError("缺少 sname（请传入或确保 session cookie 中存在 __zp_sname__）")

    # 同步到内存缓存
    global _cache_sseed, _cache_sname, _cache_sts
    _cache_sseed = seed
    _cache_sname = sname
    _cache_sts = ts

    stoken = generate_stoken(seed, ts, sname)
    session.cookies.set(
        "__zp_stoken__", quote(stoken, safe=""),
        domain="www.zhipin.com", path="/",
    )
    # 同步更新 cookie 中的 seed、ts、sname（响应体里的新值）
    session.cookies.set(
        "__zp_sseed__", seed,
        domain="www.zhipin.com", path="/",
    )
    session.cookies.set(
        "__zp_sts__", str(ts),
        domain="www.zhipin.com", path="/",
    )
    session.cookies.set(
        "__zp_sname__", sname,
        domain="www.zhipin.com", path="/",
    )
    return stoken


def refresh_stoken_from_cookies(session) -> bool:
    """从内存缓存读取 seed/ts/sname，主动生成新 stoken 并设置到 cookie

    每次请求前调用，确保 __zp_stoken__ 始终是最新生成的，
    而非等到过期（code=37）才刷新。

    seed/ts/sname 不是从请求 cookie 中读取，而是从之前 API 响应
    Set-Cookie 更新到内存缓存的变量中获取（见 update_params_from_response）。

    Args:
        session: requests.Session 实例

    Returns:
        True 刷新成功，False（seed/ts/sname 缺失或 Playwright 不可用）
    """
    if not _HAS_PLAYWRIGHT:
        print("[stoken] Playwright 不可用，跳过 stoken 刷新")
        return False

    # 优先从内存缓存读取（由 API 响应 Set-Cookie 维护）
    seed = _cache_sseed
    sname = _cache_sname
    ts_from_cache = _cache_sts

    # fallback: 从 session 请求 cookie 读取（兼容已有 cookie 的场景）
    if not seed:
        seed = session.cookies.get("__zp_sseed__", domain="www.zhipin.com")
    if not sname:
        sname = session.cookies.get("__zp_sname__", domain="www.zhipin.com")
    if ts_from_cache is None:
        ts_str = session.cookies.get("__zp_sts__", domain="www.zhipin.com")
        if ts_str:
            try:
                ts_from_cache = int(ts_str)
            except (ValueError, TypeError):
                ts_from_cache = None

    if not seed:
        print("[stoken] 缺少 __zp_sseed__（未从响应 cookie 捕获到），跳过刷新")
        return False
    if not sname:
        print("[stoken] 缺少 __zp_sname__（未从响应 cookie 捕获到），跳过刷新")
        return False
    if ts_from_cache is None:
        print("[stoken] 缺少 __zp_sts__（未从响应 cookie 捕获到），跳过刷新")
        return False

    # 用当前时间戳覆盖，确保每次生成不同的 stoken
    # now_ts = int(time.time() * 1000)
    session.cookies.set("__zp_sts__", str(ts_from_cache), domain="www.zhipin.com", path="/")

    try:
        stoken = refresh_stoken_and_set_cookie(seed, ts_from_cache, session, sname)
    except Exception as e:
        print(f"[stoken] 生成失败: {e}")
        return False

    masked = stoken[:20] + "..." if len(stoken) > 23 else stoken
    print(f"[stoken] 已刷新 → {masked}")
    return True


def close():
    """关闭浏览器实例"""
    global _BROWSER, _PAGE, _PLAYWRIGHT
    if _PAGE:
        try:
            _PAGE.close()
        except Exception:
            pass
        _PAGE = None
    if _BROWSER:
        try:
            _BROWSER.close()
        except Exception:
            pass
        _BROWSER = None
    if _PLAYWRIGHT:
        try:
            _PLAYWRIGHT.stop()
        except Exception:
            pass
        _PLAYWRIGHT = None


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        seed = sys.argv[1]
        ts = int(sys.argv[2])
        sname = sys.argv[3]
    elif len(sys.argv) >= 3:
        seed = sys.argv[1]
        ts = int(sys.argv[2])
        sname = "11859538"
    else:
        seed = "p7uu30ex6vKspZPZvnJnAYWXhoFaMbqubazqoxhOIlU="
        ts = 1782367593947
        sname = "11859538"

    stoken = generate_stoken(seed, ts, sname)
    print(f"__zp_stoken__: {stoken}")
    close()
