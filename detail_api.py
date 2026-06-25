"""BOSS直聘职位详情查询 — 自动处理 __zp_stoken__ 过期

通过 securityId + lid 获取职位详情，遇到 stoken 过期自动刷新。
"""
import json
import time

from session import session, refresh_timestamp_fields
import stoken as stoken_mod


URL = "https://www.zhipin.com/wapi/zpgeek/job/detail.json"


def _make_request(security_id: str, lid: str) -> tuple:
    """执行一次详情请求

    Returns:
        (code, data) 元组
    """
    refresh_timestamp_fields()
    params = {
        "securityId": security_id,
        "lid": lid,
        "_": str(int(time.time() * 1000)),
    }
    resp = session.get(URL, params=params)

    # 捕获响应 Set-Cookie 中的 stoken 参数（__zp_sseed__ / __zp_sname__ / __zp_sts__）
    stoken_mod.update_params_from_response(resp)
    stoken_mod.refresh_stoken_from_cookies(session)
    try:
        data = resp.json()
    except json.JSONDecodeError:
        raw = resp.text[:500]
        print(f"  └─ [!] 非 JSON 响应: {raw}")
        return (-1, {"error": "非 JSON 响应", "raw": raw})
    return (data.get("code"), data)


def fetch_detail(security_id: str, lid: str, retry: int = 1) -> tuple:
    """获取 BOSS 直聘职位详情

    每次请求前主动刷新 stoken，遇到 code=37 自动重试。

    Args:
        security_id: 职位的 securityId（从列表接口获得）
        lid: lid 值（从列表接口获得）
        retry: 最大重试次数

    Returns:
        (code, data) 元组，data 为 zpData 或错误信息
    """
    # 每次请求 detail 前主动刷新 stoken


    for attempt in range(retry):
        code, data = _make_request(security_id, lid)

        if code == 0:
            return (0, data.get("zpData", {}))

        if code == 37:
            zp_data = data.get("zpData", {})
            seed = zp_data.get("seed")
            ts = zp_data.get("ts")
            # sname 优先用响应体的 name（最新），fallback 到 session cookie
            sname = zp_data.get("name") or session.cookies.get("__zp_sname__", domain="www.zhipin.com")
            if seed and ts and sname and stoken_mod.is_available():
                print(f"[{attempt+1}/{retry}] code=37，用 Playwright 重新生成 stoken...")
                stoken_mod.refresh_stoken_and_set_cookie(seed, ts, session, sname)
                continue

        return (code, data)

    return (-2, {"error": "重试耗尽"})


if __name__ == "__main__":
    # 示例查询
    sec_id = "j6iBNryFf2jRA-i16nUsp3hOzJ1NJ4O33WpMzKcX6dwez0qbMC1kaYMpO4L7fk6g8P4wYQQBTMKSPo83bkGm9E2zvWY1pPa3-xKb6dFXnfs9EXRigHM3sZC8rUZWLtld0azc2ZY3mVCZrvE48Z_YwbreDV-Km6CR2o33miqN9jILy6eYrdq6l6gRpvSZcBOu1nACQXqnkHuZP2_TqWsMqx_y73Fsqom9EzTjOWJ9XoUBqqnfrKEaTyVDC630if4D6EOfBKuP9L47yCYevLMlbGVH_Wf5QzEca5y6CwRIU0Lngf6h1KLv"
    test_lid = "a2OPa8Jcqe1.search.4"
    code, result = fetch_detail(sec_id, test_lid)
    if code == 0:
        print(f"[OK] 获取详情成功")
        print(json.dumps(result, ensure_ascii=False, indent=2)[:1000])
    else:
        print(f"[!] 请求失败: code={code}")
        print(json.dumps(result, ensure_ascii=False, indent=2)[:500])
