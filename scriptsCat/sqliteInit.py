"""
SQLite 数据库初始化 — 根据 detail.json 结构设计
表结构:
  jobs        — 职位信息 (jobInfo)
  bosses      — 招聘者信息 (bossInfo)
  companies   — 公司/品牌信息 (brandComInfo)
  job_details — 职位详情 (顶层元数据 + 三张子表的外键关联)
"""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "detail.db"


def init_db(db_path: str | Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript("""
    -- 职位信息
    CREATE TABLE IF NOT EXISTS jobs (
        encrypt_id             TEXT PRIMARY KEY,
        encrypt_user_id        TEXT,
        invalid_status         INTEGER DEFAULT 0,
        job_name               TEXT,
        position               INTEGER,
        position_name          TEXT,
        location               INTEGER,
        location_name          TEXT,
        location_url           TEXT,
        experience_name        TEXT,
        degree_name            TEXT,
        job_type               INTEGER DEFAULT 0,
        proxy_job              INTEGER DEFAULT 0,
        proxy_type             INTEGER DEFAULT 0,
        salary_desc            TEXT,
        pay_type_desc          TEXT,
        post_description       TEXT,
        recruitment_count      TEXT,
        encrypt_address_id     TEXT,
        address                TEXT,
        longitude              REAL,
        latitude               REAL,
        static_map_url         TEXT,
        pc_static_map_url      TEXT,
        baidu_static_map_url   TEXT,
        baidu_pc_static_map_url TEXT,
        overseas_info          TEXT,
        show_skills            TEXT,
        anonymous              INTEGER DEFAULT 0,
        job_status_desc        TEXT
    );

    -- 招聘者信息
    CREATE TABLE IF NOT EXISTS bosses (
        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        name                 TEXT,
        title                TEXT,
        tiny_avatar          TEXT,
        large_avatar         TEXT,
        active_time_desc     TEXT,
        online               INTEGER DEFAULT 0,
        brand_name           TEXT,
        source               INTEGER DEFAULT 0,
        certificated         INTEGER DEFAULT 0,
        tag_icon_url         TEXT,
        avatar_sticker_url   TEXT
    );

    -- 公司/品牌信息
    CREATE TABLE IF NOT EXISTS companies (
        encrypt_brand_id      TEXT PRIMARY KEY,
        brand_name            TEXT,
        logo                  TEXT,
        stage                 INTEGER DEFAULT 0,
        stage_name            TEXT,
        scale                 INTEGER,
        scale_name            TEXT,
        industry              INTEGER,
        industry_name         TEXT,
        introduce             TEXT,
        labels                TEXT,
        active_time           INTEGER,
        visible_brand_info    INTEGER DEFAULT 0,
        focus_brand           INTEGER DEFAULT 0,
        customer_brand_name   TEXT,
        customer_brand_stage  TEXT
    );

    -- 职位详情：关联顶层元数据 + 子表外键
    CREATE TABLE IF NOT EXISTS job_details (
        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        code                 INTEGER,
        message              TEXT,
        page_type            INTEGER DEFAULT 0,
        self_access          INTEGER DEFAULT 0,
        security_id          TEXT,
        session_id           TEXT,
        lid                   TEXT,
        encrypt_job_id       TEXT REFERENCES jobs(encrypt_id),
        boss_id              INTEGER REFERENCES bosses(id),
        encrypt_brand_id     TEXT REFERENCES companies(encrypt_brand_id),
        invite_type          INTEGER DEFAULT 0,
        already_sent         INTEGER DEFAULT 0,
        can_send_resume      INTEGER DEFAULT 0,
        can_send_phone       INTEGER DEFAULT 0,
        can_send_wechat      INTEGER DEFAULT 0,
        interest_job         INTEGER DEFAULT 0,
        be_friend            INTEGER DEFAULT 0,
        already_apply        INTEGER DEFAULT 0,
        can_feedback         INTEGER DEFAULT 0,
        chat_bubble          TEXT,
        cert_materials       TEXT,
        created_at           TEXT DEFAULT (datetime('now','localtime'))
    );

    CREATE INDEX IF NOT EXISTS idx_jobs_location   ON jobs(location);
    CREATE INDEX IF NOT EXISTS idx_jobs_position    ON jobs(position);
    CREATE INDEX IF NOT EXISTS idx_jobs_salary      ON jobs(salary_desc);
    CREATE INDEX IF NOT EXISTS idx_details_job      ON job_details(encrypt_job_id);
    CREATE INDEX IF NOT EXISTS idx_details_boss     ON job_details(boss_id);
    CREATE INDEX IF NOT EXISTS idx_details_brand    ON job_details(encrypt_brand_id);
    """)

    conn.commit()
    return conn


def insert_from_json(conn: sqlite3.Connection, data: dict, stats: dict) -> int:
    """解析一条 detail.json 并插入，返回 job_details.id。
    stats 用于计数: {"jobs": {"new": 0, "update": 0}, ...}
    """
    zp = data.get("zpData", {})
    job = zp.get("jobInfo", {})
    boss = zp.get("bossInfo", {})
    brand = zp.get("brandComInfo", {})
    one_key = zp.get("oneKeyResumeInfo", {})
    relation = zp.get("relationInfo", {})
    ats = zp.get("atsOnlineApplyInfo", {})
    appendix = zp.get("appendixInfo", {})

    # ── jobs（按 encrypt_id 去重，重复则用新数据覆盖）
    job_values = (
        job.get("encryptId"), job.get("encryptUserId"),
        int(job.get("invalidStatus", False)),
        job.get("jobName"), job.get("position"), job.get("positionName"),
        job.get("location"), job.get("locationName"), job.get("locationUrl"),
        job.get("experienceName"), job.get("degreeName"),
        job.get("jobType", 0), job.get("proxyJob", 0), job.get("proxyType", 0),
        job.get("salaryDesc"), job.get("payTypeDesc"),
        job.get("postDescription"), job.get("recruitmentCountDesc"),
        job.get("encryptAddressId"), job.get("address"),
        job.get("longitude"), job.get("latitude"),
        job.get("staticMapUrl"), job.get("pcStaticMapUrl"),
        job.get("baiduStaticMapUrl"), job.get("baiduPcStaticMapUrl"),
        json.dumps(job.get("overseasAddressList"), ensure_ascii=False),
        json.dumps(job.get("showSkills"), ensure_ascii=False),
        job.get("anonymous", 0), job.get("jobStatusDesc"),
    )
    if conn.execute(
        "SELECT 1 FROM jobs WHERE encrypt_id=?", (job.get("encryptId"),)
    ).fetchone():
        print(f"🔄 jobs 覆盖更新: encrypt_id={job.get('encryptId')}  jobName={job.get('jobName')}")
        stats["jobs"]["update"] += 1
        conn.execute("""
            UPDATE jobs SET
                encrypt_user_id=?, invalid_status=?, job_name=?,
                position=?, position_name=?, location=?, location_name=?, location_url=?,
                experience_name=?, degree_name=?, job_type=?, proxy_job=?, proxy_type=?,
                salary_desc=?, pay_type_desc=?, post_description=?, recruitment_count=?,
                encrypt_address_id=?, address=?, longitude=?, latitude=?,
                static_map_url=?, pc_static_map_url=?, baidu_static_map_url=?, baidu_pc_static_map_url=?,
                overseas_info=?, show_skills=?, anonymous=?, job_status_desc=?
            WHERE encrypt_id=?
        """, job_values[1:] + (job.get("encryptId"),))
    else:
        conn.execute("""
            INSERT INTO jobs (
                encrypt_id, encrypt_user_id, invalid_status, job_name,
                position, position_name, location, location_name, location_url,
                experience_name, degree_name, job_type, proxy_job, proxy_type,
                salary_desc, pay_type_desc, post_description, recruitment_count,
                encrypt_address_id, address, longitude, latitude,
                static_map_url, pc_static_map_url, baidu_static_map_url, baidu_pc_static_map_url,
                overseas_info, show_skills, anonymous, job_status_desc
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, job_values)
        stats["jobs"]["new"] += 1

    # ── bosses（按 name+brand_name 去重，重复则用新数据覆盖）
    boss_values = (
        boss.get("name"), boss.get("title"),
        boss.get("tiny"), boss.get("large"),
        boss.get("activeTimeDesc"), int(boss.get("bossOnline", False)),
        boss.get("brandName"), boss.get("bossSource", 0),
        int(boss.get("certificated", False)),
        boss.get("tagIconUrl"), boss.get("avatarStickerUrl"),
    )
    row = conn.execute(
        "SELECT id FROM bosses WHERE name=? AND brand_name=?",
        (boss.get("name"), boss.get("brandName")),
    ).fetchone()
    if row:
        boss_id = row[0]
        print(f"🔄 bosses 覆盖更新: id={boss_id}  name={boss.get('name')}  brand={boss.get('brandName')}")
        stats["bosses"]["update"] += 1
        conn.execute("""
            UPDATE bosses SET
                title=?, tiny_avatar=?, large_avatar=?,
                active_time_desc=?, online=?, source=?,
                certificated=?, tag_icon_url=?, avatar_sticker_url=?
            WHERE id=?
        """, boss_values[2:] + (boss_id,))
    else:
        cur = conn.execute("""
            INSERT INTO bosses (
                name, title, tiny_avatar, large_avatar,
                active_time_desc, online, brand_name, source,
                certificated, tag_icon_url, avatar_sticker_url
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, boss_values)
        boss_id = cur.lastrowid
        stats["bosses"]["new"] += 1

    # ── companies（按 encrypt_brand_id 去重，重复则用新数据覆盖）
    brand_values = (
        brand.get("encryptBrandId"), brand.get("brandName"),
        brand.get("logo"), brand.get("stage", 0), brand.get("stageName"),
        brand.get("scale"), brand.get("scaleName"),
        brand.get("industry"), brand.get("industryName"),
        brand.get("introduce"),
        json.dumps(brand.get("labels"), ensure_ascii=False),
        brand.get("activeTime"), int(brand.get("visibleBrandInfo", False)),
        int(brand.get("focusBrand", False)),
        brand.get("customerBrandName"), brand.get("customerBrandStageName"),
    )
    if conn.execute(
        "SELECT 1 FROM companies WHERE encrypt_brand_id=?", (brand.get("encryptBrandId"),)
    ).fetchone():
        print(f"🔄 companies 覆盖更新: encrypt_brand_id={brand.get('encryptBrandId')}  brandName={brand.get('brandName')}")
        stats["companies"]["update"] += 1
        conn.execute("""
            UPDATE companies SET
                brand_name=?, logo=?, stage=?, stage_name=?,
                scale=?, scale_name=?, industry=?, industry_name=?,
                introduce=?, labels=?, active_time=?, visible_brand_info=?,
                focus_brand=?, customer_brand_name=?, customer_brand_stage=?
            WHERE encrypt_brand_id=?
        """, brand_values[1:] + (brand.get("encryptBrandId"),))
    else:
        conn.execute("""
            INSERT INTO companies (
                encrypt_brand_id, brand_name, logo, stage, stage_name,
                scale, scale_name, industry, industry_name, introduce,
                labels, active_time, visible_brand_info, focus_brand,
                customer_brand_name, customer_brand_stage
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, brand_values)
        stats["companies"]["new"] += 1

    # ── job_details（按 encrypt_job_id 去重，重复则用新数据覆盖）
    detail_values = (
        data.get("code"), data.get("message"),
        zp.get("pageType", 0), int(zp.get("selfAccess", False)),
        zp.get("securityId"), zp.get("sessionId"), zp.get("lid"),
        job.get("encryptId"), boss_id, brand.get("encryptBrandId"),
        one_key.get("inviteType", 0), int(one_key.get("alreadySend", False)),
        int(one_key.get("canSendResume", False)),
        int(one_key.get("canSendPhone", False)),
        int(one_key.get("canSendWechat", False)),
        int(relation.get("interestJob", False)),
        int(relation.get("beFriend", False)),
        int(ats.get("alreadyApply", False)),
        int(appendix.get("canFeedback", False)),
        appendix.get("chatBubble"),
        json.dumps(zp.get("certMaterials", []), ensure_ascii=False),
    )
    existing = conn.execute(
        "SELECT id FROM job_details WHERE encrypt_job_id=?", (job.get("encryptId"),)
    ).fetchone()
    if existing:
        print(f"🔄 job_details 覆盖更新: id={existing[0]}  encrypt_job_id={job.get('encryptId')}  jobName={job.get('jobName')}")
        stats["job_details"]["update"] += 1
        conn.execute("""
            UPDATE job_details SET
                code=?, message=?, page_type=?, self_access=?, security_id=?, session_id=?, lid=?,
                encrypt_job_id=?, boss_id=?, encrypt_brand_id=?,
                invite_type=?, already_sent=?, can_send_resume=?, can_send_phone=?, can_send_wechat=?,
                interest_job=?, be_friend=?, already_apply=?,
                can_feedback=?, chat_bubble=?, cert_materials=?
            WHERE id=?
        """, detail_values + (existing[0],))
        conn.commit()
        return existing[0]

    cur = conn.execute("""
        INSERT INTO job_details (
            code, message, page_type, self_access, security_id, session_id, lid,
            encrypt_job_id, boss_id, encrypt_brand_id,
            invite_type, already_sent, can_send_resume, can_send_phone, can_send_wechat,
            interest_job, be_friend, already_apply,
            can_feedback, chat_bubble, cert_materials
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, detail_values)
    stats["job_details"]["new"] += 1

    conn.commit()
    return cur.lastrowid


if __name__ == "__main__":
    conn = init_db()
    print(f"✅ 数据库已创建: {DB_PATH}")

    json_path = Path(__file__).parent / "detail.json"
    if json_path.exists():
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        # 支持 JSON 数组或单个对象
        items = data if isinstance(data, list) else [data]
        stats = {
            "jobs":        {"new": 0, "update": 0},
            "bosses":      {"new": 0, "update": 0},
            "companies":   {"new": 0, "update": 0},
            "job_details": {"new": 0, "update": 0},
        }
        for item in items:
            row_id = insert_from_json(conn, item, stats)
            # print(f"✅ 已导入 → job_details.id = {row_id}")

        print()
        print("📊 导入汇总:")
        for t in ("jobs", "bosses", "companies", "job_details"):
            cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            n, u = stats[t]["new"], stats[t]["update"]
            print(f"   {t}: 共 {cnt} 条（新增 {n}，覆盖更新 {u}）")

    conn.close()
