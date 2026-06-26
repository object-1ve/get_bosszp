"""BOSS直聘职位采集主程序 — getData 版

工作流程:
  1. 调用 search_api.search_jobs() 获取职位列表（POST 搜索接口）
  2. 对每条职位调用 detail_api.fetch_detail() 获取详情
  3. 保存为 JSON 文件 + 存入 bossfinal.db（4 表结构）

统一使用 session.py 的全局会话，stoken 自动刷新逻辑在各 API 模块中内置。
"""
import json
import os
import random
import sys
import time

# ===== 添加项目根目录到 path，确保本地导入 =====
BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, BASE_DIR)

from constants import (
    CITY_CODES,
)
import search_api
import detail_api
from session import session
import stoken as stoken_mod
from db.import_data import get_conn, init_schema, import_detail, print_stats
from utils import safe_filename, pad

TOTAL_PAGES = 5  # ← 要抓的总页数（每页 PAGE_SIZE=15 条，固定值）

# ===== 配置 =====
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ----- 搜索配置（在此修改筛选条件） -----
SEARCH_QUERY = "后端开发"           # 搜索关键词
CITY = "100010000"                  # 城市名称或编码（北京）
PAGE_SIZE = 15                       # 每页数量（固定 15，API 不支持其他值）
RETRY = 3                           # 重试次数

# 筛选参数（留空则不筛选，编码值参考 constants.py）
SALARY = ""          # 薪资范围
EXPERIENCE = "108,102,103"      # 工作经验
DEGREE = ""          # 学历要求
INDUSTRY = ""        # 行业
SCALE = ""           # 公司规模
JOB_TYPE = "1901"        # 职位类型

# 运行模式
FETCH_DETAIL = True  # 是否获取详情并入库


# ===== 辅助函数 =====

def _build_filter_kwargs() -> dict:
    """将配置中的筛选参数直接传入（原值就是 API 编码）"""
    kwargs = {}
    if SALARY:        kwargs["salary"] = SALARY
    if EXPERIENCE:    kwargs["experience"] = EXPERIENCE
    if DEGREE:        kwargs["degree"] = DEGREE
    if INDUSTRY:      kwargs["industry"] = INDUSTRY
    if SCALE:         kwargs["scale"] = SCALE
    if JOB_TYPE:      kwargs["job_type"] = JOB_TYPE
    return kwargs


def _describe_filters() -> str:
    """生成筛选条件描述文本"""
    active_filters = []
    if SALARY:       active_filters.append(f"薪资:{SALARY}")
    if EXPERIENCE:   active_filters.append(f"经验:{EXPERIENCE}")
    if DEGREE:       active_filters.append(f"学历:{DEGREE}")
    if INDUSTRY:     active_filters.append(f"行业:{INDUSTRY}")
    if SCALE:        active_filters.append(f"规模:{SCALE}")
    if JOB_TYPE:     active_filters.append(f"类型:{JOB_TYPE}")
    return " · ".join(active_filters) if active_filters else "无筛选"


def _ensure_stoken_available() -> bool:
    """检查 stoken 生成依赖是否就绪"""
    if not stoken_mod.is_available():
        print("[!] 需要安装 playwright:")
        print("    pip install playwright && playwright install chromium")
        return False
    return True


# ===== 核心流程 =====

def fetch_all_jobs(page: int = 1):
    """获取指定页码的职位列表（含筛选参数）"""
    filters = _build_filter_kwargs()
    filter_desc = _describe_filters()

    print(f"[*] 搜索职位: query='{SEARCH_QUERY}', city={CITY}, page={page}/{TOTAL_PAGES} | 筛选: {filter_desc}")

    code, data = search_api.search_jobs(
        page=page,
        page_size=PAGE_SIZE,
        city=CITY,
        query=SEARCH_QUERY,
        retry=RETRY,
        **filters,
    )

    if code != 0:
        print(f"[!] 获取职位列表失败: code={code}")
        print(json.dumps(data, ensure_ascii=False, indent=2)[:500])
        return [], ""

    job_list = data.get("jobList", [])
    lid = data.get("lid", "")
    print(f"[OK] 获取到 {len(job_list)} 条职位 (lid={lid})")
    print(f"     关键词: {SEARCH_QUERY} | 城市: {CITY}")
    if filter_desc != "无筛选":
        print(f"     筛选: {filter_desc}")

    return job_list, lid


def fetch_job_detail(security_id: str, lid: str, index: int, total: int):
    """获取单个职位详情

    Returns:
        (code, detail_data) 元组。code=0 时 detail_data 有效，
        否则 detail_data 为 None。
    """
    print(f"[{index}/{total}] 获取详情: securityId={security_id[:24]}...")
    code, detail_data = detail_api.fetch_detail(security_id, lid)

    if code == 0:
        job_name = detail_data.get("jobName", detail_data.get("jobId", "unknown"))
        print(f"  └─ OK: {job_name}")
        if index == 1:
            print(f"  └─ 响应字段: {list(detail_data.keys())[:15]}")
        return (code, detail_data)
    else:
        print(f"  └─ FAIL: code={code}")
        # 打印响应体辅助排错
        if isinstance(detail_data, dict):
            msg = detail_data.get("message", detail_data.get("error", ""))
            if msg:
                print(f"  └─ message: {msg}")
            # 打印请求参数，方便排查
            print(f"  └─ securityId: {security_id[:24]}...")
            print(f"  └─ lid: {lid}")
        return (code, None)


def save_detail(detail_data: dict, security_id: str, index: int) -> str:
    """保存详情为 JSON 文件到 output 目录"""
    job_id = (
        detail_data.get("jobId")
        or detail_data.get("encryptJobId")
        or detail_data.get("encryptId")
        or detail_data.get("lid")
        or ""
    )
    if job_id:
        job_id = safe_filename(job_id, 24)
    else:
        import hashlib
        job_id = hashlib.md5(security_id.encode()).hexdigest()[:12]

    job_name = detail_data.get("jobName", "unknown")
    safe_name = safe_filename(job_name)

    filename = f"{index:02d}_{safe_name}_{job_id}.json"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(detail_data, f, ensure_ascii=False, indent=2)

    print(f"  └─ 已保存: {filename}")
    return filepath


# ===== 主入口 =====

def main():
    print("=" * 60)
    print("  BOSS 直聘职位采集 (getData)")
    print("=" * 60)
    print(f"  总页数: {TOTAL_PAGES} | 每页: {PAGE_SIZE} 条")
    print()

    # 检查 Playwright 依赖
    if not _ensure_stoken_available():
        sys.exit(1)

    # 初始化数据库
    print("[DB] 初始化数据库...")
    conn = get_conn()
    init_schema(conn)
    from db.import_data import DB_PATH
    print(f"      数据库: {DB_PATH}")

    # ----- 设置默认 stoken 参数（首次搜索时用于主动刷新 stoken）-----
    print("[*] 设置默认 stoken 参数 cookie...")
    session.cookies.set(
        "__zp_sseed__",
        "0HSsHiBVJIt0MK06zc1TA24ublk1SHopOukle1/gF9+yJRCYoQ92lklDjSrhg3R7Tyd8AhJv869BpeO3xNZ7ug==",
        domain="www.zhipin.com", path="/",
    )
    session.cookies.set(
        "__zp_sname__", "11859538",
        domain="www.zhipin.com", path="/",
    )
    session.cookies.set(
        "__zp_sts__", "1782396140488",
        domain="www.zhipin.com", path="/",
    )
    # 首次主动生成 stoken，避免第一次请求因缺少 stoken 返回 code=37
    stoken_mod.refresh_stoken_from_cookies(session)

    all_results = []
    grand_total_jobs = 0
    grand_total_success = 0

    for page in range(1, TOTAL_PAGES + 1):
        print(f"\n{'='*60}")
        print(f"  第 {page}/{TOTAL_PAGES} 页")
        print(f"{'='*60}")

        # ----- 获取当前页职位列表 -----
        job_list, lid = fetch_all_jobs(page=page)
        if not job_list:
            print(f"[!] 第 {page} 页无数据，继续下一页")
            continue

        grand_total_jobs += len(job_list)

        # 打印职位概览表
        print()
        print(f"{'#':>3} | {pad('职位名称',24)} | {pad('经验',10)} | {pad('薪资',20)} | {pad('学历',8)} | {pad('公司',24)} | {pad('规模',14)}")
        print("-" * (3 + 3 + 24 + 3 + 10 + 3 + 20 + 3 + 8 + 3 + 24 + 3 + 14))
        for i, job in enumerate(job_list, 1):
            print(f"{i:3d} | {pad(job.get('jobName',''),24)} | {pad(job.get('jobExperience',''),10)} | {pad(job.get('salaryDesc',''),20)} | {pad(job.get('jobDegree',''),8)} | {pad(job.get('brandName',''),24)} | {pad(job.get('brandScaleName',''),14)}")
        print()

        if not FETCH_DETAIL:
            continue

        # 如果是第一页，给用户一次确认机会
        # if page == 1:
        #     input("按回车键开始获取详情 (Ctrl+C 取消)...\n")

        # ----- 逐个获取当前页的详情 -----
        page_results = []
        for i, job in enumerate(job_list, 1):
            security_id = job.get("securityId") or job.get("encryptId") or job.get("jobId", "")
            job_lid = job.get("lid", lid)

            if not security_id:
                job_name = job.get("jobName", "unknown")
                print(f"[{i}/{len(job_list)}] 跳过 {job_name}: 缺少 securityId")
                continue

            # 获取详情
            code, detail = fetch_job_detail(security_id, job_lid, i, len(job_list))
            if code != 0:
                print(f"  └─ [!] 请求失败(code={code})，停止后续详情查询")
                break
            if detail is None:
                continue

            # 保存 JSON
            save_detail(detail, security_id, i)

            # 导入数据库
            zp_id = import_detail(conn, detail, job_list_item=job)
            if zp_id:
                job_name = detail.get("jobName", "")
                page_results.append({"index": i, "jobName": job_name, "securityId": security_id, "zpdata_id": zp_id})

            # 随机请求间隔（防止反爬，最后一条不等待）
            if i < len(job_list):
                delay = random.uniform(2.0, 4.0)
                print(f"      等待 {delay:.1f}s...")
                time.sleep(delay)

        # ----- 提交当前页数据到数据库 -----
        conn.commit()
        grand_total_success += len(page_results)
        all_results.extend(page_results)

        print(f"\n[OK] 第 {page} 页完成: {len(page_results)} / {len(job_list)} 条成功")

        # 页间间隔
        if page < TOTAL_PAGES:
            delay = random.uniform(3.0, 5.0)
            print(f"\n      页间隔等待 {delay:.1f}s（防止反爬）...")
            time.sleep(delay)

    # ----- 最终统计 -----
    print()
    print("=" * 60)
    if FETCH_DETAIL:
        print(f"  采集完成: {grand_total_success} / {grand_total_jobs} 条成功（共 {TOTAL_PAGES} 页）")
        print_stats(conn, label="  数据库")
        print("=" * 60)
        for r in all_results:
            print(f"  {r['index']:2d}. {r['jobName']} (zpdata.id={r['zpdata_id']})")
    else:
        print(f"  列表获取完成: {grand_total_jobs} 条职位（共 {TOTAL_PAGES} 页）")
    print("=" * 60)

    conn.close()


if __name__ == "__main__":
    main()
