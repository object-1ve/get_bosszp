"""BOSS直聘职位搜索 — POST 搜索接口

使用 search/joblist.json 搜索接口，支持丰富的筛选参数。
遇到 __zp_stoken__ 过期时自动通过 stoken 模块刷新。
"""
import json
import time

from constants import CITY_CODES
from session import session, refresh_stoken, refresh_timestamp_fields
import stoken as stoken_mod


# ===== 搜索接口地址 =====
URL = "https://www.zhipin.com/wapi/zpgeek/search/joblist.json"


# ===== 辅助函数 =====

def resolve_city(city: str) -> str:
    """将城市名称转换为城市编码，已是编码则原样返回。"""
    return CITY_CODES.get(city, city)


def _make_request(page: int, page_size: int, city: str, query: str,
                  job_type: str, salary: str, experience: str,
                  degree: str, industry: str, scale: str) -> tuple:
    """执行一次搜索请求

    Returns:
        (code, data) 元组
    """
    refresh_timestamp_fields()
    params = {"_": str(int(time.time() * 1000))}
    post_data = {
        "page": str(page),
        "pageSize": str(page_size),
        "query": query,
        "city": resolve_city(city),
        "expectInfo": "",
        "jobType": job_type,
        "salary": salary,
        "experience": experience,
        "degree": degree,
        "industry": industry,
        "scale": scale,
        "scene": "1",
        "encryptExpectId": "",
    }

    resp = session.post(URL, params=params, data=post_data)

    # 捕获响应 Set-Cookie 中的 stoken 参数（__zp_sseed__ / __zp_sname__ / __zp_sts__）
    stoken_mod.update_params_from_response(resp)

    try:
        result = resp.json()
        # print(result)
    except json.JSONDecodeError:
        return (-1, {"error": "非 JSON 响应", "raw": resp.text[:200]})

    return (result.get("code"), result)


def search_jobs(
    page: int = 1,
    page_size: int = 15,
    city: str = "101010100",
    query: str = "",
    retry: int = 1,
    job_type: str = "",
    salary: str = "",
    experience: str = "",
    degree: str = "",
    industry: str = "",
    scale: str = "",
) -> tuple:
    """搜索 BOSS 直聘职位

    使用 POST search/joblist.json 接口，遇到 code=37（stoken 过期）
    时自动通过 Playwright 刷新 stoken 并重试。

    Args:
        page: 页码
        page_size: 每页数量
        city: 城市编码或城市名称
        query: 搜索关键词
        retry: 最大重试次数
        job_type: 职位类型编码
        salary: 薪资编码
        experience: 经验编码
        degree: 学历编码
        industry: 行业编码
        scale: 公司规模编码

    Returns:
        (code, data) 元组，data 为 zpData 或错误信息
    """
    for attempt in range(retry):
        code, result = _make_request(
            page, page_size, city, query,
            job_type, salary, experience, degree, industry, scale,
        )  
        if code == 0:
            return (0, result.get("zpData", {}))

        if code == 37:
            zp_data = result.get("zpData", {})
            seed = zp_data.get("seed")
            ts = zp_data.get("ts")
            # sname 优先用响应体的 name（最新），fallback 到 session cookie
            sname = zp_data.get("name") or session.cookies.get("__zp_sname__", domain="www.zhipin.com")
            if seed and ts and sname and stoken_mod.is_available():
                if attempt > 0:
                    # 已重试过一次仍然 code=37 → 尝试二次刷新 stoken
                    print(f"[{attempt+1}/{retry}] code=37 仍存在，二次刷新 stoken...")
                else:
                    print(f"[{attempt+1}/{retry}] code=37，用 Playwright 重新生成 stoken...")
                stoken_mod.refresh_stoken_and_set_cookie(seed, ts, session, sname)
                continue

        # 其他错误码直接返回
        return (code, result)

    return (-2, {"error": "重试耗尽"})


# ===== 命令行入口 =====
if __name__ == "__main__":
    import argparse
    from constants import SALARY_CODES, EXP_CODES, DEGREE_CODES, INDUSTRY_CODES, SCALE_CODES, JOB_TYPE_CODES

    parser = argparse.ArgumentParser(description="BOSS直聘职位搜索（POST 搜索接口）")
    parser.add_argument("query", nargs="?", default="", help="搜索关键词")
    parser.add_argument("-c", "--city", default="101010100", help="城市名称或编码")
    parser.add_argument("-p", "--page", type=int, default=1, help="页码")
    parser.add_argument("--page-size", type=int, default=15, help="每页数量")
    parser.add_argument("--job-type", choices=JOB_TYPE_CODES.keys(), help="职位类型")
    parser.add_argument("--salary", choices=SALARY_CODES.keys(), help="薪资范围")
    parser.add_argument("--exp", choices=EXP_CODES.keys(), help="工作经验")
    parser.add_argument("--degree", choices=DEGREE_CODES.keys(), help="学历要求")
    parser.add_argument("--industry", choices=INDUSTRY_CODES.keys(), help="行业")
    parser.add_argument("--scale", choices=SCALE_CODES.keys(), help="公司规模")
    parser.add_argument("--retry", type=int, default=3, help="最大重试次数")
    parser.add_argument("-o", "--output", help="输出 JSON 文件路径")
    args = parser.parse_args()

    code, result = search_jobs(
        page=args.page, page_size=args.page_size, city=args.city,
        query=args.query, retry=args.retry,
        job_type=JOB_TYPE_CODES.get(args.job_type, ""),
        salary=SALARY_CODES.get(args.salary, ""),
        experience=EXP_CODES.get(args.exp, ""),
        degree=DEGREE_CODES.get(args.degree, ""),
        industry=INDUSTRY_CODES.get(args.industry, ""),
        scale=SCALE_CODES.get(args.scale, ""),
    )

    if code == 0:
        job_list = result.get("jobList", [])
        has_more = result.get("hasMore", False)
        total = result.get("totalCount", len(job_list))

        output = {"code": code, "message": "Success", "zpData": result}

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            print(f"[OK] 已保存 {len(job_list)} 条职位到 {args.output}")
        else:
            print(f"[OK] 找到 {len(job_list)} 条职位 (共{total}, hasMore={has_more})")
            print(f"     关键词: {args.query or '(空)'} | 城市: {args.city}")
            print()
            for i, job in enumerate(job_list, 1):
                name = job.get("jobName", "")
                brand = job.get("brandName", "")
                salary_desc = job.get("salaryDesc", "")
                exp = job.get("jobExperience", "")
                degree_name = job.get("jobDegree", "")
                skills = ", ".join(job.get("skills", [])[:3])
                print(f"  {i:2d}. {name} @ {brand}  {salary_desc}")
                print(f"      经验:{exp} 学历:{degree_name} 技能:{skills}")
            print()
            if has_more:
                print(f"[提示] 还有更多结果，使用 -p {args.page + 1} 查看下一页")
    else:
        print(f"[!] 请求失败: code={code}")
        print(json.dumps(result, ensure_ascii=False, indent=2)[:500])
