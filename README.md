# getData — BOSS直聘数据采集工具

> 基于结构化项目组织的 BOSS 直聘职位数据采集工具。支持关键词搜索、多维度筛选、职位详情获取、自动 `__zp_stoken__` 刷新、数据持久化存储。

本人爱慕虚荣，请大家多多star啊！！！

[![Python Version](https://img.shields.io/badge/python-%3E%3D3.11-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

## 作者有话说(非ai)

逆向接口存在被封号的风险,不如脚本猫一把梭^v^.

---

## 目录

- [特性](#特性)
- [快速开始](#快速开始)
  - [前置要求](#前置要求)
  - [安装](#安装)
- [使用指南](#使用指南)
  - [完整采集（搜索 + 详情 + 入库）](#完整采集搜索--详情--入库)
  - [仅搜索职位列表](#仅搜索职位列表)
  - [查看职位详情](#查看职位详情)
  - [刷新 Cookie 配置](#刷新-cookie-配置)
- [数据模型](#数据模型)
- [scriptsCat — 脚本猫自动采集](#scriptscat--脚本猫自动采集)
- [架构说明](#架构说明)
  - [项目结构](#项目结构)
  - [模块职责](#模块职责)
  - [核心机制：stoken 刷新](#核心机制stoken-刷新)
  - [请求日志](#请求日志)
- [贡献](#贡献)
- [许可](#许可)
- [免责声明](#免责声明)

---

## 特性

- **实时搜索** — 通过 BOSS 直聘搜索接口 (`search/joblist.json`) 获取职位列表，支持关键词、城市、薪资、经验、学历、行业、公司规模等多维度筛选
- **职位详情** — 通过 `job/detail.json` 接口获取完整职位信息，包括公司信息、招聘者信息、岗位描述、地图位置等
- **自动化 stoken** — 内置 Playwright 无头浏览器，自动下载并执行加密 JS 生成 `__zp_stoken__`，遇到过期自动刷新
- **数据持久化** — 支持 SQLite 数据库存储，数据按 `brand`、`boss`、`job`、`zpdata` 四表拆分，外键关联
- **请求日志** — 所有 HTTP 请求/响应自动保存为 JSON 文件，方便排查问题
- **终端友好** — CJK 中文字符宽度的格式化表格输出

---

## 快速开始

### 前置要求

- **Python ≥ 3.11**
- **Playwright**（可选但推荐，用于自动 stoken 刷新）

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/getData.git
cd getData

# 使用 pip 安装（推荐：先创建虚拟环境）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install requests

# 如需自动 stoken 刷新（推荐）:
pip install playwright
playwright install chromium
```

或使用 [uv](https://docs.astral.sh/uv/)（更快）:

```bash
uv sync                     # 自动创建 .venv 并安装所有依赖
playwright install chromium # 安装浏览器
```

---

## 使用指南

### 完整采集（搜索 + 详情 + 入库）

修改 `main.py` 顶部的配置变量，然后直接运行：

```bash
python main.py
```

#### 配置项说明

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SEARCH_QUERY` | `"agent开发"` | 搜索关键词 |
| `CITY` | `"100010000"` | 城市编码或名称（`"北京"` 或 `"101010100"`） |
| `TOTAL_PAGES` | `1` | 要抓取的页数（每页固定 15 条） |
| `PAGE_SIZE` | `15` | 每页数量（API 固定值，不支持其他值） |
| `RETRY` | `2` | stoken 过期重试次数 |
| `FETCH_DETAIL` | `True` | 是否获取详情并入库 |
| `SALARY` | `""` | 薪资筛选编码 |
| `EXPERIENCE` | `""` | 经验筛选编码 |
| `DEGREE` | `""` | 学历筛选编码 |
| `INDUSTRY` | `""` | 行业筛选编码 |
| `SCALE` | `""` | 公司规模筛选编码 |
| `JOB_TYPE` | `""` | 职位类型编码 |

### 仅搜索职位列表

```bash
# 基本搜索（搜索 "前端开发"，城市：北京）
python search_api.py "前端开发" --city 北京

# 带筛选条件
python search_api.py "前端开发" --city 北京 --salary 15-20K --exp 3-5年

# 带输出文件
python search_api.py Python --city 上海 --degree 本科 --industry 互联网 -p 2 -o results.json
```

#### search_api.py 命令行参数

```
python search_api.py [查询词] [选项]

位置参数:
  query                 搜索关键词

选项:
  -c, --city            城市名称或编码（默认: 101010100）
  -p, --page            页码（默认: 1）
  --page-size           每页数量（默认: 15）
  --job-type            职位类型（全职/实习/兼职）
  --salary              薪资范围（3K以下/3-5K/…/50K以上）
  --exp                 工作经验（不限/在校应届/1年以内/…/10年以上）
  --degree              学历要求（不限/大专/本科/硕士/博士）
  --industry            行业（互联网/金融/医疗健康/…）
  --scale               公司规模（0-20人/…/10000人以上）
  --retry               最大重试次数（默认: 3）
  -o, --output          输出 JSON 文件路径
```

### 查看职位详情

```bash
python detail_api.py
```

默认使用示例 securityId；如需自定义，修改 `detail_api.py` 底部的 `sec_id` 和 `test_lid` 参数。

### 刷新 Cookie 配置

```bash
python update.py
```

该命令从 `headers.py` 提取最新 headers 和 cookies，合并写入 `header.json`。修改 `headers.py` 中的 token 或 cookie 后需执行此命令才能生效。

---

## 数据模型

详情数据拆分为 4 张表，通过外键关联：

```
┌─────────────────────────────────────────┐
│                 zpdata                   │  ← 主表，一次详情请求一条记录
│  id (PK)                                │
│  encrypt_job_id ──────→ job(encrypt_id) │
│  encrypt_user_id ─────→ boss(encrypt_user_id) │
│  encrypt_brand_id ────→ brand(encrypt_brand_id) │
│  security_id, lid, page_type, ...       │
└─────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │   job    │  │   boss   │  │  brand   │
    │ 岗位详情 │  │ 招聘者信息│  │ 公司信息 │
    └──────────┘  └──────────┘  └──────────┘
```

- **brand** — 公司/品牌信息（名称、Logo、阶段、规模、行业、标签等）
- **boss** — 招聘者信息（姓名、职位、头像、活跃时间、认证状态等）
- **job** — 岗位详情（职位名称、薪资、描述、技能、地址、地图坐标等）
- **zpdata** — 主记录，包含本次请求的快照信息，外键关联以上三表

---

## scriptsCat — 脚本猫自动采集

`scriptsCat/` 提供了一套基于 [脚本猫（ScriptCat）](https://scriptcat.org/) 的替代采集方案，实现"浏览器自动点击 → 拦截 API 响应 → 导出 JSON → Python 入库"的完整链路，无需逆向加密参数。

### 文件说明

| 文件 | 说明 |
|------|------|
| `bosszpAuto.js` | 脚本猫脚本（v1.3），安装后在 Boss 直聘搜索页注入操作按钮 |
| `detail.json` | 脚本导出的原始职位详情数据 |
| `sqliteInit.py` | Python 脚本，将 `detail.json` 解析并写入 `detail.db` |
| `detail.db` | SQLite 数据库，存储结构化的职位、Boss、公司信息 |

### 脚本功能（bosszpAuto.js）

安装 [脚本猫](https://scriptcat.org/) 后导入此脚本，访问 Boss 直聘搜索页时页面右下角会出现操作面板：

- **▶ 开始自动点击** — 自动逐个点击职位卡片，触发详情 API 请求，支持无限滚动自动加载下一批
- **📦 导出JSON** — 将缓存的所有 `job/detail.json` 响应导出为文件，导出后自动清空缓存
- **🗑 清空缓存** — 手动清空已拦截的数据

脚本通过拦截 XHR 和 Fetch 请求中的 `job/detail.json` 接口，自动缓存每条职位的完整详情数据（含公司、Boss、地址等）。

### 数据入库

```bash
cd scriptsCat
python sqliteInit.py
```

解析 `detail.json` 并写入 `detail.db`，包含四张表：

| 表名 | 内容 |
|------|------|
| `jobs` | 职位信息（名称、城市、薪资、经验要求、技能标签等） |
| `bosses` | 招聘者信息（姓名、头衔、头像、在线状态） |
| `companies` | 公司信息（名称、规模、融资阶段、行业） |
| `job_details` | 关联表，串联职位、Boss、公司三者关系 |

> **注意**：`detail.json` 可能包含多次导出的重复数据，脚本以 `encrypt_job_id` 为唯一键去重。`encrypt_user_id` 列为从接口响应中额外提取的 Boss 加密 ID，用于与主流程的数据对齐。

### 使用流程

1. 在脚本猫中导入 `bosszpAuto.js`
2. 打开 Boss 直聘搜索页，点击"开始自动点击"
3. 脚本自动遍历职位列表并拦截详情数据
4. 点击"导出JSON"保存为 `detail.json`
5. 运行 `python sqliteInit.py` 将数据写入 `detail.db`

---

## 架构说明

### 项目结构

```
getData/
├── main.py              # 主流程编排（搜索 → 详情 → 入库）
├── constants.py         # 城市、薪资、学历等编码表
├── session.py           # 统一 HTTP 会话（headers + cookies + 动态字段刷新）
├── stoken.py            # __zp_stoken__ 生成器（Playwright 无头浏览器）
├── search_api.py        # 搜索职位（POST 接口）
├── detail_api.py        # 职位详情（GET 接口）
├── utils.py             # 工具函数（类型转换、文件名安全化、终端宽度适配）
├── update.py            # 从 headers.py 提取数据刷新 header.json
├── request_logger.py    # 请求/响应自动日志（保存为 JSON）
├── headers.py           # 手动维护的 headers + cookies 样本
├── header.json          # session.py 加载的正式配置（由 update.py 生成）
├── pyproject.toml       # 项目元数据与依赖声明
├── db/
│   ├── schema.sql       # 数据库表结构（4 表 + 索引）
│   └── import_data.py   # 导入数据到 SQLite
├── webJs/
│   ├── traceid.py       # TraceID 生成与解码（原生 Python，无 JS 依赖）
│   └── {sname}.js       # BOSS 直聘加密 JS（自动下载，由 sname 标识）
└── scriptsCat/
    ├── bosszpAuto.js    # 脚本猫脚本：自动点击职位 + 拦截 detail.json
    ├── sqliteInit.py    # 将导出的 detail.json 写入 SQLite
    ├── detail.json      # 脚本导出的原始职位详情数据
    └── detail.db        # SQLite 数据库（职位/Boss/公司/关联四张表）
```

### 模块职责

| 模块 | 职责 |
|------|------|
| `session.py` | 全局 `requests.Session`，统一管理 headers 和 cookies；每次请求前自动刷新 `traceId` 和 `Referer` 中的时间戳 |
| `stoken.py` | Playwright 无头浏览器生成 `__zp_stoken__`；从响应 Set-Cookie 捕获 `__zp_sseed__`/`__zp_sname__`/`__zp_sts__`；内存缓存与 cookie 同步 |
| `search_api.py` | 封装职位搜索 API，遇到 `code=37` 自动刷新 stoken 重试 |
| `detail_api.py` | 封装职位详情 API，每次请求前主动刷新 stoken |
| `request_logger.py` | Session 钩子，每次请求完成自动保存请求/响应到 `requests_log/` 目录 |
| `constants.py` | 编码表：城市、薪资、经验、学历、行业、公司规模、职位类型 |
| `utils.py` | 安全类型转换（`s/i/f/j`）、文件名安全化、CJK 适配的终端填充/截断 |
| `update.py` | 从 `headers.py` 提取 headers/cookies 写入 `header.json` |

### 核心机制：stoken 刷新

`__zp_stoken__` 是 BOSS 直聘接口的身份验证令牌，会定期过期。本工具实现了全自动的 stoken 生命周期管理：

1. **参数捕获** — 每次 API 请求/响应时，`stoken.update_params_from_response()` 从 Set-Cookie 中捕获 `__zp_sseed__`、`__zp_sname__`、`__zp_sts__` 三个参数，维护在内存缓存中；`code=37` 的响应体也包含这些参数，一并捕获
2. **JS 下载** — 根据 `__zp_sname__`（如 `11859538`）自动下载对应加密 JS 文件 `https://www.zhipin.com/web/common/security-js/{sname}.js`，保存到 `webJs/` 目录
3. **浏览器执行** — 在 Playwright 无头浏览器中执行该 JS 的 `ABC.z(seed, adjusted_ts)` 方法生成 stoken
4. **会话更新** — 将生成的 stoken 设置到 session cookie 的 `__zp_stoken__` 字段，后续请求自动携带
5. **过期重试** — 搜索/详情 API 遇到 `code=37`（stoken 过期）时自动触发以上流程

浏览器实例全局唯一、复用、懒加载，同一个 sname 不会重复下载 JS。

### 请求日志

所有 HTTP 请求自动记录到 `requests_log/` 目录，每条记录一个 JSON 文件：

```json
{
  "timestamp": "2026-06-25T23:22:15.123",
  "duration_ms": 452.1,
  "request": { "method": "POST", "url": "...", "headers": {...} },
  "response": { "status_code": 200, "headers": {...}, "body": {...} },
  "cookies": { "request": {...}, "response": {...} }
}
```

日志文件命名格式：`{时间}_{状态码}_{接口路径}.json`。加密 JS 下载请求会自动过滤，不生成日志。

---

## 贡献

欢迎提交 Issue 或 Pull Request。涉及 Cookie/Token 等敏感信息请勿提交到公开仓库。

---

## 许可

[MIT License](LICENSE)

---

## 免责声明

本工具仅供学习和研究使用。使用者应遵守 BOSS 直聘的用户协议和相关法律法规，不得用于商业用途或大规模抓取。作者不对因使用本工具产生的任何法律问题负责。
