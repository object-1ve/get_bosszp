# getData — BOSS直聘数据采集

基于 `py/` 模块的功能复刻，采用结构化项目组织，统一管理请求会话和 Cookie。

## 目录结构

```
getData/
├── main.py              # 主流程编排
├── constants.py         # 城市/薪资/学历等编码表
├── session.py           # 统一 HTTP 会话（headers + cookies）
├── stoken.py            # 封装 stoken 生成（Playwright 无头浏览器）
├── search_api.py        # 搜索职位（POST 接口）
├── detail_api.py        # 职位详情（GET 接口）
├── utils.py             # 工具函数（类型转换、文件名安全化）
├── db/
│   ├── schema.sql       # 数据库表结构（4 表）
│   └── import_data.py   # 导入数据到 SQLite
├── pyproject.toml
└── README.md
```

## 安装

```bash
# 核心依赖
pip install requests

# 如需 stoken 自动刷新（推荐）:
pip install playwright
playwright install chromium
```

## 使用

### 完整采集流程

```bash
cd getData
python main.py
```

修改 `main.py` 顶部的配置变量来调整搜索条件。

### 仅搜索职位列表

```bash
python search_api.py 前端开发 -c 北京 --page-size 15
python search_api.py 前端开发 -c 北京 --salary 15-20K --exp 3-5年
```

### 查看职位详情

```bash
python detail_api.py
# 如需指定 securityId，修改 detail_api.py 底部的示例参数
```

### 命令行搜索

```bash
python search_api.py Python -c 上海 --degree 本科 --industry 互联网 -p 2 -o results.json
```

## 架构说明

- **统一会话**: `session.py` 维护全局 `requests.Session`，所有 API 模块共用 headers 和 cookies
- **自动 stoken 刷新**: 当 API 返回 code=37（stoken 过期）时，自动调用 Playwright 重新生成
- **模块化**: 搜索、详情、数据库导入各自独立，通过 `main.py` 编排流程
