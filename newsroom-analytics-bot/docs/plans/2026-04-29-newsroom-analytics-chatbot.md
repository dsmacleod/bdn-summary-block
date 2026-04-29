# Newsroom Analytics Chatbot Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Slack-first chatbot that answers BDN reporters' questions about story performance, EPV-goal progress, and audience signals — with numbers that match the existing dashboards exactly.

**Architecture:** Standalone Python repo on a single DigitalOcean droplet. Hourly ETL from Mather + GA4 + WordPress into local Postgres. FastAPI/Bolt Slack listener (Socket Mode) calls Claude with defined tools that read Postgres only. No text-to-SQL. Every numeric claim traces back to a tool result.

**Tech Stack:** Python 3.12, Postgres 16, FastAPI, Slack Bolt (Socket Mode), Anthropic SDK, pytest, Docker (tests), systemd, DigitalOcean droplet.

**Reference:** See `2026-04-29-newsroom-analytics-chatbot-design.md` in this directory for the full design and rationale behind every choice below.

---

## Working agreements (read before starting)

- **TDD always.** Write the failing test first; run it; watch it fail; implement; watch it pass; commit. No exceptions.
- **Frequent commits.** One commit per task minimum. Use `feat:`, `test:`, `chore:`, `docs:` prefixes consistently.
- **DRY, but only after the second duplication.** Three similar lines is fine; abstract on the third occurrence, not the first.
- **YAGNI.** If the design doc lists something as Phase 2/3 or "out of scope," do not build it now. Period.
- **Numbers must be accurate.** Every tool returns `source` and `as_of` on every metric. The LLM never does math. The numeric audit post-filter is non-negotiable.
- **Pure read collectors; only the store writes.** Never call a collector from a tool.
- **One tool per file.** Each tool is independently testable.
- **Zero secrets in git.** Use `.env` locally and the droplet's environment in prod. The `.env.example` should list every key with a placeholder.

---

## Milestone 0: Repo scaffold

### Task 0.1: Initialize the repo

**Files:**
- Create: `newsroom-analytics-bot/.gitignore`
- Create: `newsroom-analytics-bot/pyproject.toml`
- Create: `newsroom-analytics-bot/README.md`
- Create: `newsroom-analytics-bot/.env.example`
- Create: `newsroom-analytics-bot/src/__init__.py`
- Create: `newsroom-analytics-bot/tests/__init__.py`

**Step 1: `.gitignore`**

```
.env
__pycache__/
*.pyc
.pytest_cache/
.venv/
.coverage
*.log
data/
```

**Step 2: `pyproject.toml`**

```toml
[project]
name = "newsroom-analytics-bot"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "anthropic>=0.40.0",
    "slack-bolt>=1.21",
    "fastapi>=0.115",
    "uvicorn>=0.32",
    "pydantic>=2.9",
    "pydantic-settings>=2.6",
    "psycopg[binary,pool]>=3.2",
    "pymysql>=1.1",
    "google-analytics-data>=0.18",
    "requests>=2.32",
    "python-dotenv>=1.0",
    "rapidfuzz>=3.10",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "pytest-cov>=6.0",
    "ruff>=0.7",
    "mypy>=1.13",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
```

**Step 3: `.env.example`**

```
# Slack (Socket Mode — no public webhook needed)
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_SIGNING_SECRET=...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-opus-4-7

# Postgres (local on droplet)
DATABASE_URL=postgresql://analytics:CHANGEME@localhost:5432/analytics

# Mather Listener DB (read-only)
MATHER_HOST=...
MATHER_PORT=3306
MATHER_USER=...
MATHER_PASSWORD=...
MATHER_DB=...

# GA4
GA4_PROPERTY_ID=303794572
GOOGLE_APPLICATION_CREDENTIALS=/etc/newsroom-analytics-bot/ga4-sa.json

# WordPress
WP_DB_HOST=...
WP_DB_USER=...
WP_DB_PASSWORD=...
WP_DB_NAME=...

# Alerts
ALERTS_SLACK_CHANNEL=#analytics-bot-alerts
```

**Step 4: minimal `README.md`** — link to the design doc, list `make` targets that will exist by the end of plan.

**Step 5: Commit**

```bash
git add newsroom-analytics-bot/
git commit -m "chore(newsroom-analytics-bot): initial repo scaffold"
```

### Task 0.2: Pydantic settings module

**Files:**
- Create: `src/config.py`
- Test: `tests/unit/test_config.py`

**Step 1: failing test**

```python
# tests/unit/test_config.py
from src.config import Settings

def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/d")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-x")
    monkeypatch.setenv("SLACK_APP_TOKEN", "xapp-x")
    monkeypatch.setenv("MATHER_HOST", "h"); monkeypatch.setenv("MATHER_USER", "u")
    monkeypatch.setenv("MATHER_PASSWORD", "p"); monkeypatch.setenv("MATHER_DB", "d")
    monkeypatch.setenv("WP_DB_HOST", "h"); monkeypatch.setenv("WP_DB_USER", "u")
    monkeypatch.setenv("WP_DB_PASSWORD", "p"); monkeypatch.setenv("WP_DB_NAME", "d")
    monkeypatch.setenv("GA4_PROPERTY_ID", "1")
    s = Settings()
    assert s.anthropic_api_key == "sk-ant-test"
    assert s.anthropic_model == "claude-opus-4-7"
```

**Step 2: implementation**

```python
# src/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str
    anthropic_model: str = "claude-opus-4-7"
    database_url: str
    slack_bot_token: str
    slack_app_token: str
    slack_signing_secret: str = ""
    mather_host: str
    mather_port: int = 3306
    mather_user: str
    mather_password: str
    mather_db: str
    ga4_property_id: str
    wp_db_host: str
    wp_db_user: str
    wp_db_password: str
    wp_db_name: str
    alerts_slack_channel: str = "#analytics-bot-alerts"
```

**Step 3: run + commit**

```bash
pytest tests/unit/test_config.py -v   # PASS
git add src/config.py tests/unit/test_config.py
git commit -m "feat(config): pydantic settings from env"
```

---

## Milestone 1: Postgres schema + store layer

### Task 1.1: Schema definition

**Files:**
- Create: `src/store/schema.sql`
- Create: `src/store/migrations/0001_initial.sql` (identical to schema.sql for v1)
- Create: `tests/integration/test_schema.py`

**Step 1: write `schema.sql`** (full DDL — every table from the design doc).

```sql
-- Dimension table for posts
CREATE TABLE IF NOT EXISTS posts (
    post_id        BIGINT PRIMARY KEY,
    url            TEXT NOT NULL,
    title          TEXT NOT NULL,
    wp_author_id   BIGINT NOT NULL,
    author_name    TEXT NOT NULL,
    section        TEXT,
    tags           TEXT[] NOT NULL DEFAULT '{}',
    publish_ts     TIMESTAMPTZ NOT NULL,
    last_modified  TIMESTAMPTZ NOT NULL,
    fetched_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS posts_author_publish_idx ON posts(wp_author_id, publish_ts DESC);
CREATE INDEX IF NOT EXISTS posts_section_publish_idx ON posts(section, publish_ts DESC);
CREATE INDEX IF NOT EXISTS posts_tags_gin ON posts USING gin(tags);

-- Mather hourly EPV snapshots
CREATE TABLE IF NOT EXISTS mather_epv_hourly (
    post_id     BIGINT NOT NULL,
    hour_ts     TIMESTAMPTZ NOT NULL,
    epvs        BIGINT NOT NULL,
    fetched_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (post_id, hour_ts)
);
CREATE INDEX IF NOT EXISTS mather_epv_post_idx ON mather_epv_hourly(post_id, hour_ts DESC);

-- Mirror of Mather AuthorGoals table
CREATE TABLE IF NOT EXISTS author_goals (
    wp_author_id  BIGINT NOT NULL,
    author_name   TEXT NOT NULL,
    quarter       SMALLINT NOT NULL,
    year          SMALLINT NOT NULL,
    goal          BIGINT NOT NULL,
    multiplier    NUMERIC(4,2) NOT NULL,
    fetched_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (wp_author_id, quarter, year)
);

-- Mirror of QuarterlyProgress view (precomputed by Mather)
CREATE TABLE IF NOT EXISTS quarterly_progress (
    wp_author_id     BIGINT NOT NULL,
    author_name      TEXT NOT NULL,
    quarter          SMALLINT NOT NULL,
    year             SMALLINT NOT NULL,
    quarter_epvs     BIGINT NOT NULL,
    goal             BIGINT NOT NULL,
    pct_to_goal      NUMERIC(6,3) NOT NULL,
    bonus_threshold  BIGINT NOT NULL,
    epvs_to_bonus    BIGINT NOT NULL,
    projected_epvs   BIGINT NOT NULL,
    pace_verdict     TEXT NOT NULL,
    fetched_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (wp_author_id, quarter, year)
);

-- GA4 hourly pageviews per post
CREATE TABLE IF NOT EXISTS ga4_pageviews_hourly (
    post_id          BIGINT NOT NULL,
    hour_ts          TIMESTAMPTZ NOT NULL,
    pageviews        BIGINT NOT NULL,
    sessions         BIGINT NOT NULL,
    avg_engaged_time NUMERIC(8,2),
    fetched_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (post_id, hour_ts)
);

-- GA4 traffic sources rollup per post per day
CREATE TABLE IF NOT EXISTS ga4_traffic_sources_daily (
    post_id    BIGINT NOT NULL,
    day        DATE NOT NULL,
    channel    TEXT NOT NULL,
    pageviews  BIGINT NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (post_id, day, channel)
);

-- Rolling 30-day reporter median (refreshed hourly)
CREATE TABLE IF NOT EXISTS reporter_baselines (
    wp_author_id BIGINT PRIMARY KEY,
    epv_median_30d   BIGINT NOT NULL,
    pv_median_30d    BIGINT NOT NULL,
    sample_size      INT NOT NULL,
    refreshed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Rolling 30-day section median
CREATE TABLE IF NOT EXISTS section_baselines (
    section          TEXT PRIMARY KEY,
    epv_median_30d   BIGINT NOT NULL,
    pv_median_30d    BIGINT NOT NULL,
    sample_size      INT NOT NULL,
    refreshed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Slack user → WP author mapping
CREATE TABLE IF NOT EXISTS slack_user_map (
    slack_user_id  TEXT PRIMARY KEY,
    email          TEXT NOT NULL,
    wp_author_id   BIGINT NOT NULL,
    full_name      TEXT NOT NULL,
    is_override    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS slack_user_email_idx ON slack_user_map(email);

-- Wishlist log
CREATE TABLE IF NOT EXISTS unanswered_questions (
    id            BIGSERIAL PRIMARY KEY,
    slack_user_id TEXT NOT NULL,
    question      TEXT NOT NULL,
    reason        TEXT NOT NULL,
    asked_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ETL run log
CREATE TABLE IF NOT EXISTS etl_runs (
    id          BIGSERIAL PRIMARY KEY,
    source      TEXT NOT NULL,
    started_at  TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    rows        BIGINT,
    status      TEXT NOT NULL,
    error       TEXT
);
```

**Step 2: integration test loads schema into a Docker Postgres**

```python
# tests/integration/test_schema.py
import os, pytest, psycopg

@pytest.fixture(scope="module")
def conn():
    url = os.environ["TEST_DATABASE_URL"]  # set by conftest.py via testcontainers
    with psycopg.connect(url) as c:
        with c.cursor() as cur:
            with open("src/store/schema.sql") as f:
                cur.execute(f.read())
        c.commit()
        yield c

def test_all_tables_exist(conn):
    expected = {"posts", "mather_epv_hourly", "author_goals", "quarterly_progress",
                "ga4_pageviews_hourly", "ga4_traffic_sources_daily",
                "reporter_baselines", "section_baselines",
                "slack_user_map", "unanswered_questions", "etl_runs"}
    with conn.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        actual = {r[0] for r in cur.fetchall()}
    assert expected.issubset(actual)
```

**Step 3: `tests/conftest.py`** spins up a Postgres testcontainer once per session and exposes `TEST_DATABASE_URL` via env.

**Step 4: run + commit.** `pytest tests/integration/test_schema.py -v` must pass. Commit message: `feat(store): initial postgres schema`.

### Task 1.2: Upsert helpers

**Files:**
- Create: `src/store/upserts.py`
- Test: `tests/integration/test_upserts.py`

One function per table. Each is an idempotent `INSERT … ON CONFLICT … DO UPDATE`. Test by inserting a row, inserting again with different values, asserting the new values landed.

**Reference shape:**

```python
# src/store/upserts.py
import psycopg
from datetime import datetime
from typing import Iterable

def upsert_posts(conn: psycopg.Connection, rows: Iterable[dict]) -> int:
    sql = """
    INSERT INTO posts (post_id, url, title, wp_author_id, author_name,
                       section, tags, publish_ts, last_modified)
    VALUES (%(post_id)s, %(url)s, %(title)s, %(wp_author_id)s, %(author_name)s,
            %(section)s, %(tags)s, %(publish_ts)s, %(last_modified)s)
    ON CONFLICT (post_id) DO UPDATE SET
        url=EXCLUDED.url, title=EXCLUDED.title,
        wp_author_id=EXCLUDED.wp_author_id, author_name=EXCLUDED.author_name,
        section=EXCLUDED.section, tags=EXCLUDED.tags,
        last_modified=EXCLUDED.last_modified, fetched_at=NOW()
    """
    rows = list(rows)
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    conn.commit()
    return len(rows)
```

Test for each helper: insert N rows, re-insert N rows with mutations, assert COUNT(*) == N and mutated columns reflect the second write. Commit: `feat(store): upsert helpers per table`.

### Task 1.3: Baseline computation

**Files:**
- Create: `src/store/baselines.py`
- Test: `tests/integration/test_baselines.py`

Compute the rolling-30-day reporter and section EPV/PV medians. SQL-only; no Python median. Test against a hand-built fixture where the median is obvious.

**Key SQL:**

```sql
-- Reporter EPV median over last 30 days, per author, per *story*
INSERT INTO reporter_baselines (wp_author_id, epv_median_30d, pv_median_30d, sample_size)
SELECT
    p.wp_author_id,
    PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY story_epvs.total) AS epv_median,
    COALESCE(PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY story_pvs.total), 0) AS pv_median,
    COUNT(*)
FROM posts p
JOIN LATERAL (
    SELECT SUM(epvs) AS total
    FROM mather_epv_hourly e
    WHERE e.post_id = p.post_id
) story_epvs ON TRUE
LEFT JOIN LATERAL (
    SELECT SUM(pageviews) AS total
    FROM ga4_pageviews_hourly g
    WHERE g.post_id = p.post_id
) story_pvs ON TRUE
WHERE p.publish_ts >= NOW() - INTERVAL '30 days'
GROUP BY p.wp_author_id
ON CONFLICT (wp_author_id) DO UPDATE
  SET epv_median_30d = EXCLUDED.epv_median_30d,
      pv_median_30d  = EXCLUDED.pv_median_30d,
      sample_size    = EXCLUDED.sample_size,
      refreshed_at   = NOW();
```

Same shape for `section_baselines` keyed by `section` instead of author. Commit: `feat(baselines): rolling 30d reporter and section medians`.

---

## Milestone 2: Collectors

### Task 2.1: WordPress collector

**Files:**
- Create: `src/collectors/wordpress.py`
- Test: `tests/unit/test_wordpress_collector.py`
- Fixture: `tests/fixtures/wp_posts.json`

Pulls posts modified in the last 7 days from the WP DB via `pymysql`. Returns a list of dicts in the shape `upsert_posts` expects. Includes tag list (from `wp_term_relationships` joined to `wp_terms`).

**SQL skeleton:**

```sql
SELECT p.ID AS post_id, p.post_title AS title, p.post_date_gmt AS publish_ts,
       p.post_modified_gmt AS last_modified, p.post_author AS wp_author_id,
       u.display_name AS author_name, ...
FROM wp_posts p
JOIN wp_users u ON u.ID = p.post_author
WHERE p.post_status = 'publish'
  AND p.post_modified_gmt >= UTC_TIMESTAMP() - INTERVAL 7 DAY
```

Tag pull is a second query: `SELECT object_id, name FROM wp_term_relationships JOIN wp_terms …`. Build the tag array in Python and merge with posts.

Test: feed the function a mock pymysql cursor whose `fetchall` returns `wp_posts.json`. Assert returned dicts have the right shape. Commit: `feat(collectors): wordpress posts and tags`.

### Task 2.2: Mather collector

**Files:**
- Create: `src/collectors/mather.py`
- Test: `tests/unit/test_mather_collector.py`
- Fixtures: `tests/fixtures/mather_epv.json`, `tests/fixtures/mather_goals.json`, `tests/fixtures/mather_progress.json`

Three pulls:
1. `pull_epv_hourly(since: datetime)` — query `Daily_EPVs` (or hourly equivalent if available). Otherwise use `EPV_Entry` directly with `LAG()`.
2. `pull_author_goals(year, quarter)` — full snapshot of `AuthorGoals` for the current quarter.
3. `pull_quarterly_progress()` — read the `QuarterlyProgress` view directly. **Read raw, do not recompute.**

**Critical rule:** the chatbot's `get_goal_progress` numbers must equal what `QuarterlyProgress` returns. Reading the view directly guarantees this.

Each function returns dicts shaped for the corresponding upsert helper. Commit: `feat(collectors): mather EPV, goals, quarterly progress`.

### Task 2.3: GA4 collector (batch)

**Files:**
- Create: `src/collectors/ga4.py`
- Test: `tests/unit/test_ga4_collector.py`
- Fixture: `tests/fixtures/ga4_response.json`

Use `google-analytics-data` v1beta. Two pulls:
1. `pull_pageviews_hourly(since)` — dimensions: `pagePath`, `dateHour`. Metrics: `screenPageViews`, `sessions`, `userEngagementDuration`. Map `pagePath` → `post_id` via the `posts` table; rows that don't match a known post get dropped (logged).
2. `pull_traffic_sources_daily(since)` — dimensions: `pagePath`, `date`, `defaultChannelGroup`. Metric: `screenPageViews`.

Test by mocking the GA4 client `run_report` method to return a fixed response object. Commit: `feat(collectors): ga4 hourly pageviews and traffic sources`.

### Task 2.4: GA4 Realtime client

**Files:**
- Create: `src/collectors/ga4_realtime.py`
- Test: `tests/unit/test_ga4_realtime.py`

Wraps the GA4 Realtime API for the live-fallback path used by `get_story_metrics(window="realtime")`. Returns active users + pageviews-in-last-30-min for a single `pagePath`. Don't write to Postgres — return directly to the caller. Commit: `feat(collectors): ga4 realtime client`.

---

## Milestone 3: ETL orchestration

### Task 3.1: Hourly orchestrator

**Files:**
- Create: `src/etl/hourly.py`
- Test: `tests/integration/test_hourly_etl.py`

`hourly.py` runs all collectors in order, writes results via `upserts.py`, recomputes baselines, logs to `etl_runs`. If any source fails, log the error to `etl_runs` and continue with the others. After 6 hours of consecutive failures for a given source, post to the alerts Slack channel.

**Skeleton:**

```python
# src/etl/hourly.py
def run_hourly():
    started = datetime.utcnow()
    for source, fn in [("wordpress", run_wordpress),
                       ("mather", run_mather),
                       ("ga4", run_ga4)]:
        try:
            rows = fn()
            log_run(source, started, rows, status="ok")
        except Exception as e:
            log_run(source, started, 0, status="error", error=str(e))
            maybe_alert(source)
    refresh_baselines()
```

Test: mock the three `run_*` functions; verify that one failing doesn't abort the others. Commit: `feat(etl): hourly orchestrator with per-source isolation`.

### Task 3.2: Backfill script

**Files:**
- Create: `src/etl/backfill.py`
- Test: `tests/integration/test_backfill.py` (smoke only)

One-shot script that pulls 90 days of history from each source. Used on first deploy and after data corruption. Same collectors, wider window. Commit: `feat(etl): 90-day backfill script`.

---

## Milestone 4: Tool framework

### Task 4.1: Tool registry

**Files:**
- Create: `src/tools/_registry.py`
- Test: `tests/unit/test_registry.py`

A tool is a Python function decorated with `@tool` that:
1. Has a Pydantic input model
2. Returns a Pydantic output model
3. Auto-generates the JSON schema Claude tool-use expects

```python
# src/tools/_registry.py
from typing import Callable, get_type_hints
from pydantic import BaseModel

_REGISTRY: dict[str, dict] = {}

def tool(name: str, description: str):
    def decorator(fn: Callable):
        hints = get_type_hints(fn)
        input_model = hints["payload"]
        _REGISTRY[name] = {
            "name": name,
            "description": description,
            "input_schema": input_model.model_json_schema(),
            "fn": fn,
        }
        return fn
    return decorator

def all_schemas() -> list[dict]:
    return [{"name": t["name"],
             "description": t["description"],
             "input_schema": t["input_schema"]}
            for t in _REGISTRY.values()]

def dispatch(name: str, raw_input: dict) -> dict:
    spec = _REGISTRY[name]
    payload = spec["fn"].__annotations__["payload"](**raw_input)
    result = spec["fn"](payload=payload)
    return result.model_dump(mode="json")
```

Test: register a fake tool with a Pydantic input model; verify `all_schemas()` returns the right JSON Schema; verify `dispatch` validates input and returns the result. Commit: `feat(tools): registry and dispatch framework`.

### Task 4.2: Common metric envelope

**Files:**
- Create: `src/tools/_common.py`
- Test: `tests/unit/test_common.py`

Every metric in any tool result uses this envelope:

```python
# src/tools/_common.py
from datetime import datetime
from pydantic import BaseModel

class Metric(BaseModel):
    value: float
    source: str          # "mather" | "ga4" | "ga4_realtime" | "mather:QuarterlyProgress"
    as_of: datetime
    freshness_warning: bool = False
```

A helper `metric(value, source, as_of)` sets `freshness_warning=True` automatically if `as_of < now - 90 minutes`. Test the freshness logic. Commit: `feat(tools): metric envelope with freshness flag`.

---

## Milestone 5: Tools (one task per tool)

For every tool below: write a Pydantic input model, a Pydantic output model, the implementation, and at least one happy-path + one edge-case test against fixtures. Commit per tool.

### Task 5.1: `identify_user`

**Inputs:** `slack_user_id`. **Output:** `{wp_author_id, full_name, email, is_known}`.

Reads `slack_user_map` directly. If not found, attempts a lookup via Slack API (`users.info` for email) and the WP DB (email → author). On match, inserts into `slack_user_map`. On no match, returns `is_known=False`.

**Edge case test:** unknown user returns `is_known=False`, no row inserted. Commit: `feat(tools): identify_user`.

### Task 5.2: `find_post_by_fuzzy_title`

**Inputs:** `query, author_id?, window_days=30`. **Output:** ranked candidates with scores.

Pulls candidate posts (filtered by `author_id` and `window_days` if given), scores each via `rapidfuzz.fuzz.WRatio(query, title)`, returns top 5 with `score` ∈ [0,1].

**Test:** fixture of 20 posts, query "maine bills", assert top hit is the housing-bill story. Commit: `feat(tools): fuzzy post lookup`.

### Task 5.3: `get_story_metrics`

**Inputs:** `post_id, window` (`"since_publish" | "last_24h" | "last_hour" | "realtime" | iso8601_range`). **Output:** EPVs, pageviews, sessions, avg engaged time, scroll depth — each as a `Metric`.

For `realtime`, calls `ga4_realtime.py`. Otherwise reads Postgres aggregates. **All math (sums, averages) happens in SQL or Python here, not in the LLM.**

**Test:** fixture of 24 hours of data, window=`last_24h`, assert sum is correct. Commit: `feat(tools): story metrics with realtime fallback`.

### Task 5.4: `get_traffic_sources`

**Inputs:** `post_id, window`. **Output:** list of `{channel, pageviews, share_pct, source, as_of}`.

Reads `ga4_traffic_sources_daily`, aggregates over window, computes share %. Test: fixture with 3 channels, assert shares sum to 100. Commit: `feat(tools): traffic sources by channel`.

### Task 5.5: `get_subs_attributed`

**Inputs:** `post_id, window`. **Output:** subscription conversions count.

For Phase 1, the Mather schema attributing subs to posts is needed. **If this attribution table doesn't exist in the Mather DB**, this tool returns `{conversions: None, source: "mather", note: "attribution table not configured", as_of: …}`. Document the requirement in `docs/runbook.md`. Don't fake it.

Commit: `feat(tools): subscription attribution (or graceful degradation)`.

### Task 5.6: `compare_to_baselines`

**Inputs:** `post_id, metric` (`"epvs" | "pageviews"`). **Output:** value, reporter median, section median, ratio_to_self, ratio_to_section.

Reads from `reporter_baselines` and `section_baselines`. Ratios computed in Python. Test: fixture where reporter median=1000, section median=2000, story value=2500 → ratios 2.5 and 1.25. Commit: `feat(tools): compare_to_baselines`.

### Task 5.7: `get_goal_progress`

**Inputs:** `wp_author_id, quarter?, year?`. **Output:** all fields from `quarterly_progress` table verbatim.

**This is the critical tool for the accuracy guarantee.** It reads `quarterly_progress` directly — no recomputation. Source string: `"mather:QuarterlyProgress"`.

**Test:** fixture mirroring the QuarterlyProgress view; assert every output field matches a column in that view. Commit: `feat(tools): goal progress from QuarterlyProgress view`.

### Task 5.8: `get_top_stories_for_author`

**Inputs:** `wp_author_id, window, group_by?, limit=10`. **Output:** ranked stories with primary + secondary metrics; or rolled-up groups when `group_by` is set.

`group_by` ∈ `{section, tag, day_of_week, time_of_day, headline_length}`. For tag: `UNNEST(tags) AS tag GROUP BY tag`. For `time_of_day`: bucket `EXTRACT(hour FROM publish_ts)` into morning/afternoon/evening/overnight.

**Test:** fixture with 50 stories across 3 sections; query with `group_by="section"`; assert sections sorted by total EPVs. Commit: `feat(tools): top stories with rollups`.

### Task 5.9: `get_audience_signals`

**Inputs:** `wp_author_id, window`. **Output:** `{top_tags, top_sources, top_referrers, top_sections}` — each a list of `{label, engagement}`.

Three SQL queries: top tags by EPV sum (joined on this author's posts), top channels by pageview sum, top referring domains (if available — graceful degrade if not), top sections.

**Honesty constraint:** the tool description (visible to Claude) explicitly says *"Returns descriptive aggregates only. Do not narrate as 'your audience wants X'."* Commit: `feat(tools): audience signals (descriptive only)`.

### Task 5.10: `log_unanswered`

**Inputs:** `slack_user_id, question, reason`. **Output:** `{ok: true, id: int}`.

Inserts into `unanswered_questions`. Trivial test. Commit: `feat(tools): log unanswered question`.

---

## Milestone 6: Chatbot LLM glue

### Task 6.1: System prompt

**Files:**
- Create: `src/chatbot/system_prompt.py`
- Test: `tests/unit/test_system_prompt.py` (snapshot test)

The system prompt must be load-bearing. It includes:

1. Role: "You are a newsroom analytics assistant for BDN reporters."
2. Tool catalog summary (auto-generated from registry).
3. **Hard rules:**
   - Never invent numbers. Every numeric claim must come from a tool result in this turn.
   - Never do math the tools didn't already do. If a number isn't in a tool result, don't compute it.
   - Always cite source and `as_of` for every metric.
   - If `freshness_warning` is true on any metric, surface that to the user.
   - If no tool can answer the question, explain what you can answer instead and call `log_unanswered`.
   - Describe the past; do not predict the future or infer causation.
   - For "audience" questions: describe what tags/sources/topics drove engagement among that author's existing stories. Never write "your audience wants X."

Snapshot test ensures the prompt doesn't drift accidentally. Commit: `feat(chatbot): system prompt with accuracy rules`.

### Task 6.2: Claude client wrapper

**Files:**
- Create: `src/chatbot/claude_client.py`
- Test: `tests/unit/test_claude_client.py`

Wraps the Anthropic SDK. Adds:
- Prompt caching on the system prompt and tool definitions (they're stable across turns).
- Automatic retry with backoff on 429/5xx.
- Logging of every API call (request hash, tokens in/out, cost estimate) to a local `chatbot_calls.jsonl`.

**Reference: see the `claude-api` skill for current best practices on caching and tool use.**

Test by mocking the Anthropic client and asserting cache_control headers are set on the right blocks. Commit: `feat(chatbot): claude client with prompt caching`.

### Task 6.3: Conversation loop

**Files:**
- Create: `src/chatbot/conversation.py`
- Test: `tests/unit/test_conversation.py`

The dispatch loop:

1. Send user message + system prompt + tool definitions to Claude.
2. If response has `tool_use` blocks: dispatch each (in parallel where independent), append `tool_result` blocks, send back to Claude.
3. Loop until Claude returns a `text`-only response.
4. Cap at 10 turns per conversation; abort with apology if hit.

Test with a mock Claude client that returns a scripted sequence: `[tool_use(identify_user)] → [tool_use(find_post)] → [tool_use(get_story_metrics, get_traffic_sources)] → [text]`. Assert tools are dispatched correctly and the final text is returned. Commit: `feat(chatbot): conversation/dispatch loop`.

### Task 6.4: Numeric audit post-filter

**Files:**
- Create: `src/chatbot/numeric_audit.py`
- Test: `tests/unit/test_numeric_audit.py`

After Claude returns its final text, extract every numeric token (digits and digit groups) via regex. For each, verify it appears verbatim in at least one tool result from this conversation. If any number doesn't trace, replace the entire response with a generic apology and log to a `numeric_audit_failures` log file.

```python
# src/chatbot/numeric_audit.py
import re
NUMBER_RE = re.compile(r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b|\b\d+\b")

def audit(text: str, tool_results: list[dict]) -> tuple[bool, list[str]]:
    """Returns (is_clean, untraceable_numbers)."""
    haystack = " ".join(str(tr) for tr in tool_results)
    untraceable = []
    for m in NUMBER_RE.findall(text):
        if m not in haystack:
            untraceable.append(m)
    return (len(untraceable) == 0, untraceable)
```

**Test cases:**
- LLM output contains "3,204 EPVs", tool result has "3,204" → clean.
- LLM output contains "approximately 800/hour", tool results don't → untraceable: ["800"].
- LLM output contains "2.8x", tool result has "2.8" → clean (substring match).

Hook this into the conversation loop after the final text is generated. On failure, return: *"I have the data but my response failed an internal accuracy check. Try asking again, or rephrase. (Logged for debugging.)"*

Commit: `feat(chatbot): numeric audit post-filter`.

### Task 6.5: Slack markdown formatter

**Files:**
- Create: `src/chatbot/formatting.py`

Optional helper that converts the LLM's output to Slack-flavored markdown (bullets with `•`, bold with `*…*`, etc.). Likely a no-op if Claude is prompted to output Slack-style directly. Keep minimal. Commit: `feat(chatbot): slack markdown formatter`.

---

## Milestone 7: Slack listener

### Task 7.1: Bolt app skeleton

**Files:**
- Create: `src/slack/app.py`
- Create: `src/slack/handlers.py`
- Test: `tests/integration/test_slack_handlers.py`

Use Bolt for Python with Socket Mode. Three handlers:
- `@app.event("app_mention")` — when bot is @-mentioned in a channel.
- `@app.event("message")` (im channel filter) — DMs.
- `@app.command("/howsmystory")` — slash command (Phase 1 quick alias).

Each handler builds a context dict, calls `chatbot.conversation.run()`, posts the response back as a thread reply. Commit: `feat(slack): bolt socket-mode app and handlers`.

### Task 7.2: Identity resolution layer

**Files:**
- Create: `src/slack/identity.py`
- Test: `tests/unit/test_slack_identity.py`

Wraps `identify_user` with a per-process LRU cache (5-minute TTL). Called by handlers before dispatch. Commit: `feat(slack): identity caching layer`.

---

## Milestone 8: Reconciliation

### Task 8.1: Reconciliation test suite

**Files:**
- Create: `tests/reconcile/test_goal_progress_matches_dashboard.py`
- Create: `src/etl/reconcile.py` (separate runner; not run by `pytest` in CI)

The reconcile runner:
1. Pulls `QuarterlyProgress` from Mather directly.
2. For each row, calls `get_goal_progress(wp_author_id, quarter, year)`.
3. Asserts every numeric field is exactly equal.
4. On any mismatch, writes a report to `reconcile_reports/YYYY-MM-DD.json` and posts to `#analytics-bot-alerts`.

Run nightly via `reconcile.timer` systemd unit. Commit: `feat(reconcile): nightly check vs Mather QuarterlyProgress`.

### Task 8.2: Golden questions checklist

**Files:**
- Create: `tests/manual/golden_questions.md`

A markdown file with ~20 real reporter questions and the expected shape of a correct answer ("must include EPVs, traffic sources, comparison to median; must cite Mather and GA4"). Run by hand before each release. Not automated. Commit: `docs(tests): golden questions checklist`.

---

## Milestone 9: Deployment

### Task 9.1: systemd units

**Files:**
- Create: `deploy/systemd/slack-listener.service`
- Create: `deploy/systemd/etl-hourly.service`
- Create: `deploy/systemd/etl-hourly.timer`
- Create: `deploy/systemd/reconcile.service`
- Create: `deploy/systemd/reconcile.timer`

`slack-listener.service`: `Restart=always`, runs `python -m src.slack.app`.
`etl-hourly.timer`: `OnCalendar=hourly`.
`reconcile.timer`: `OnCalendar=*-*-* 02:00:00` (nightly 2am).

Commit: `feat(deploy): systemd units`.

### Task 9.2: Backup script

**Files:**
- Create: `deploy/backup.sh`

Daily `pg_dump` piped to `b2 upload-file` (or `rclone`) to Backblaze B2. Retains 30 daily + 12 monthly. Commit: `feat(deploy): nightly postgres backup to B2`.

### Task 9.3: Deploy script

**Files:**
- Create: `deploy/deploy.sh`

`rsync` source to the droplet, run `pip install -e .`, run pending migrations, restart systemd units. Idempotent. Commit: `feat(deploy): one-command deploy`.

### Task 9.4: Runbook

**Files:**
- Create: `docs/runbook.md`

How to:
- Add a new Slack user → WP author mapping (`slack_user_map` insert).
- Read the wishlist log.
- Check ETL health (`SELECT * FROM etl_runs ORDER BY started_at DESC LIMIT 20`).
- Force a backfill.
- Diagnose a numeric_audit failure.
- Roll back a deploy.

Commit: `docs(runbook): operations cheatsheet`.

---

## Milestone 10: Cutover

### Task 10.1: Pilot rollout

Deploy to one private Slack channel with 3 reporters volunteered by Dan. Run for 2 weeks. Each evening, review the day's `unanswered_questions` and `numeric_audit_failures` logs. Iterate.

### Task 10.2: MFN parity report

After 30 days of clean reconciliation against `QuarterlyProgress`, run a comparison report between WP-derived tag/time/author rollups and the equivalent MFN views in `editorial-products-dashboard`. If drift < 1% on every comparable view for 30 consecutive days, propose cancelling the MFN subscription. Otherwise, document gaps.

---

## Acceptance criteria for Phase 1 done

- [ ] All 10 tools implemented, unit-tested, integration-tested.
- [ ] Hourly ETL runs reliably for 7 consecutive days without manual intervention.
- [ ] Reconciliation tests pass nightly for 7 consecutive days.
- [ ] 3 reporters report (qualitatively) that the bot answers their typical questions accurately.
- [ ] No `numeric_audit_failures` for 7 consecutive days under real reporter use.
- [ ] Runbook documents every common operation.
- [ ] Backups run nightly; one restore drill performed successfully.

---

## Out of scope — do NOT build in Phase 1

(Repeated from the design doc. If a question makes you think "should I quickly add…" — the answer is no.)

- Causal "why did this story work" analysis
- Predictive forecasting
- Editor-only comparative dashboards
- Newsletter / Mailchimp data
- Search Console data
- Social platform data (Meta, X)
- Charts / visual rendering / web UI
- Proactive alerts or briefing emails
- SQL fallback for unsupported questions

Each will be reconsidered in Phase 2/3 against demand from the wishlist log.
