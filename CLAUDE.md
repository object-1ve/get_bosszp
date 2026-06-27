# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BOSS直聘 (BOSS Zhipin) job data crawler. Searches job listings via API, fetches details, auto-refreshes auth tokens (`__zp_stoken__`) using Playwright headless browser, and stores structured data in SQLite.

**Two collection approaches coexist:**
1. **API-based** (`main.py`) — direct HTTP calls with automated stoken refresh
2. **Browser automation** (`scriptsCat/`) — Tampermonkey/ScriptCat script that intercepts XHR responses, exports JSON, then imports to SQLite via Python

## Commands

```bash
# Setup
uv sync                          # Install dependencies (preferred)
pip install requests playwright  # Alternative
playwright install chromium      # Required for stoken generation

# Run full pipeline (search → detail → DB)
python main.py

# Search only (CLI with filters)
python search_api.py "关键词" --city 北京 --salary 15-20K

# Detail query
python detail_api.py

# Refresh header.json from headers.py
python update.py

# Import browser-collected data
cd scriptsCat && python sqliteInit.py

# Direct DB access
sqlite3 db/bossfinal.db
```

No test suite or linter is configured.

## Architecture

### Request Flow
```
main.py (orchestrator)
  → search_api.py (POST search/joblist.json)
    → session.py (shared requests.Session, auto-refreshes traceId/timestamp)
      → stoken.py (Playwright generates __zp_stoken__ on code=37 expiry)
  → detail_api.py (GET job/detail.json)
  → db/import_data.py (SQLite write, 4-table schema)
```

`request_logger.py` hooks into the session — every HTTP call is saved as JSON in `requests_log/`.

### stoken Refresh Pipeline
1. `stoken.py` captures `__zp_sseed__`, `__zp_sname__`, `__zp_sts__` from Set-Cookie headers
2. Downloads encrypted JS from `zhipin.com/web/common/security-js/{sname}.js` → `webJs/`
3. Executes `ABC.z(seed, adjusted_ts)` in Playwright headless browser
4. Sets resulting stoken on session cookie; retries on `code=37`

Browser instance is singleton, lazy-loaded. Same sname JS is cached on disk.

### Database Schema (4 tables)
- `zpdata` — master record per detail request, FKs to all three below
- `job` — position details, requirements, skills, map coords
- `boss` — recruiter info, activity status
- `brand` — company info, funding stage, industry

Schema defined in `db/schema.sql`. `scriptsCat/detail.db` is a separate DB with a slightly different 4-table schema (`jobs`/`bosses`/`companies`/`job_details`).

### Key Modules

| Module | Role |
|--------|------|
| `session.py` | Global `requests.Session`; refreshes `traceId` and `Referer` timestamp before each request |
| `stoken.py` | Token lifecycle: capture params → download JS → Playwright exec → update cookie |
| `constants.py` | Encoding lookup tables for city, salary, experience, degree, industry, scale |
| `utils.py` | `s(v)`/`i(v)`/`f(v)`/`j(v)` safe type converters; `pad()` for CJK-aware terminal formatting |
| `headers.py` | Manual header/cookie config (edit this, then run `update.py`) |
| `request_logger.py` | Session hook — saves req/res as JSON files |
| `webJs/traceid.py` | TraceID generation (pure Python, no JS dependency) |

### Important Patterns

- **Safe type helpers** in `utils.py`: `s(v)` → `''` on None, `i(v)` → `0`, `f(v)` → `0.0`, `j(v)` → JSON string for list/dict
- **Constants are string-keyed dicts** in `constants.py`, e.g. `CITY["北京"]` → `"101010100"`
- **search_api.py** accepts both Chinese names and codes for filters (resolves via constants)
- **header.json** is generated — never edit directly; modify `headers.py` then run `update.py`

## Conventions

- Python 3.11+ required
- All user-facing output uses CJK-aware terminal formatting
- README and comments are in Chinese
- No CI/CD, no linting, no type checking configured
- `requests_log/`, `db/bossfinal.db`, `webJs/*.js` (downloaded), `.venv/` are gitignored
