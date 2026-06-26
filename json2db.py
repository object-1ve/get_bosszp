"""JSON 文件批量导入数据库

从 requests_log/ 目录（或指定路径）读取 job_detail JSON 文件，
提取 zpData 后导入 bossfinal.db 的 4 张表（brand / boss / job / zpdata）。

支持:
  - 批量导入整个目录（默认只处理 job_detail 文件）
  - 导入单个 JSON 文件
  - 跳过已导入的重复数据（INSERT OR IGNORE / INSERT OR REPLACE）

用法:
  python json2db.py                          # 导入 requests_log/ 下所有 detail JSON
  python json2db.py path/to/file.json        # 导入单个文件
  python json2db.py path/to/dir/             # 导入指定目录下所有 detail JSON
  python json2db.py --all                    # 同时导入 search_joblist 中的职位信息
  python json2db.py --stats                  # 仅显示数据库统计
"""
import argparse
import glob
import json
import os
import sys

# ===== 添加项目根目录到 path =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from db.import_data import (
    get_conn, init_schema, import_detail, print_stats, DB_PATH,
)


# ── 路径常量 ──────────────────────────────────────────────
REQUESTS_LOG_DIR = os.path.join(BASE_DIR, "requests_log")


def _is_detail_file(filepath: str) -> bool:
    """判断是否为职位详情 JSON 文件（文件名含 job_detail）"""
    return "job_detail" in os.path.basename(filepath)


def _load_wrapped_json(filepath: str) -> dict | None:
    """加载并解包 requests_log 格式的 JSON 文件

    返回 zpData 字典，失败返回 None。
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"  [!] 解析失败: {os.path.basename(filepath)} — {e}")
        return None

    # 兼容两种结构:
    #   1) 完整包装: { response: { body: { zpData: {...} } } }
    #   2) 裸 zpData: { jobInfo: {...}, bossInfo: {...}, ... }
    if "response" in data:
        body = data.get("response", {}).get("body", {})
        zpData = body.get("zpData")
        if zpData is None:
            print(f"  [!] 无 zpData: {os.path.basename(filepath)}")
            return None
        return zpData

    # 直接就是 zpData（main.py 保存的 output 格式）
    if "jobInfo" in data or "brandComInfo" in data:
        return data

    print(f"  [!] 未知格式: {os.path.basename(filepath)}")
    return None


def _extract_job_list_item(zpdata: dict, request_url: str = "") -> dict | None:
    """从 zpData 中提取等效的 job_list_item 信息

    detail 接口中 salaryDesc 可能为空字符串，
    列表中的 job_list_item 可以补充这些字段。
    从 JSON 文件导入时没有列表数据，尽力从 detail 中提取。
    """
    job_info = zpdata.get("jobInfo", {})
    brand_info = zpdata.get("brandComInfo", {})

    # 构建一个等效的 job_list_item，让 import_detail 的补充逻辑生效
    return {
        "salaryDesc": job_info.get("salaryDesc", ""),
        "brandName": brand_info.get("brandName", ""),
        "brandScaleName": brand_info.get("scaleName", ""),
    }


def import_file(conn, filepath: str) -> int:
    """导入单个 JSON 文件，返回成功导入的 zpdata 数量（0 或 1）"""
    basename = os.path.basename(filepath)
    zpdata = _load_wrapped_json(filepath)
    if zpdata is None:
        return 0

    job_info = zpdata.get("jobInfo", {})
    job_name = job_info.get("jobName", "unknown")
    encrypt_id = job_info.get("encryptId", "?")

    job_list_item = _extract_job_list_item(zpdata)

    try:
        zp_id = import_detail(conn, zpdata, job_list_item=job_list_item)
    except Exception as e:
        print(f"  [!] 导入失败: {basename} — {e}")
        return 0

    if zp_id:
        print(f"  [OK] {job_name} ({encrypt_id[:20]}...) → zpdata.id={zp_id}")
        return 1
    else:
        print(f"  [!] 导入返回空: {basename}")
        return 0


def import_directory(conn, dirpath: str, only_detail: bool = True) -> tuple[int, int]:
    """批量导入目录下的 JSON 文件

    Args:
        conn: 数据库连接
        dirpath: JSON 文件所在目录
        only_detail: True 时只处理 job_detail 文件

    Returns:
        (total_files, success_count) 元组
    """
    json_files = sorted(glob.glob(os.path.join(dirpath, "*.json")))
    if not json_files:
        print(f"[!] 目录下无 JSON 文件: {dirpath}")
        return 0, 0

    if only_detail:
        json_files = [f for f in json_files if _is_detail_file(f)]

    total = len(json_files)
    print(f"[*] 找到 {total} 个 JSON 文件待导入")
    if total == 0:
        return 0, 0

    success = 0
    for idx, filepath in enumerate(json_files, 1):
        print(f"\n[{idx}/{total}] {os.path.basename(filepath)}")
        success += import_file(conn, filepath)

    return total, success


def main():
    parser = argparse.ArgumentParser(
        description="将 JSON 文件导入 bossfinal.db",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="JSON 文件路径或目录路径（默认: requests_log/）",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="仅显示数据库统计信息",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="强制重新初始化数据库表结构",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="导入所有 JSON 文件（包括 search_joblist）",
    )

    args = parser.parse_args()

    # 初始化数据库
    print("=" * 60)
    print("  JSON → 数据库导入工具")
    print("=" * 60)
    print(f"  数据库: {DB_PATH}")

    conn = get_conn()
    init_schema(conn)
    print("[OK] 数据库表结构已就绪")
    print()

    # 仅查看统计
    if args.stats:
        print_stats(conn)
        conn.close()
        return

    # 确定导入路径
    target_path = args.path
    if target_path is None:
        target_path = REQUESTS_LOG_DIR

    target_path = os.path.abspath(target_path)
    only_detail = not args.all

    # 执行导入
    if os.path.isfile(target_path):
        # 导入单个文件
        print(f"[*] 导入文件: {os.path.basename(target_path)}")
        success = import_file(conn, target_path)
        total = 1
    elif os.path.isdir(target_path):
        # 导入目录
        print(f"[*] 扫描目录: {target_path}")
        total, success = import_directory(conn, target_path, only_detail=only_detail)
    else:
        print(f"[!] 路径不存在: {target_path}")
        conn.close()
        sys.exit(1)

    # 提交并统计
    conn.commit()
    print()
    print("=" * 60)
    print(f"  导入完成: {success}/{total} 条成功")
    print_stats(conn)
    print("=" * 60)

    conn.close()


if __name__ == "__main__":
    main()
