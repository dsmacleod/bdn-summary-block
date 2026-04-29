# Newsroom Analytics Chatbot — Design

**Date:** 2026-04-29
**Status:** Approved (brainstorming complete)
**Owner:** Dan Macleod
**Next step:** Implementation plan via `writing-plans` skill

---

## 1. Purpose

A Slack-first chatbot (Phase 1) that answers BDN reporters' questions about how their stories are performing, in plain English, with numbers that match the existing dashboards exactly.

The bar: **"How's my Maine bills piece doing?"** returns specific numbers — engagement, reach, traffic sources, subscription conversions — with comparison to the reporter's own median and their section's median, attributed to source and timestamp. Not a screenshot; a sentence.

## 2. Primary users and scope

- **Primary:** reporters, asking about their own stories and their progress to quarterly EPV goals.
- **Secondary:** any reporter or editor asking about anyone else's story or aggregate output. No access gating — full transparency.
- **Out of scope (Phase 1):** editor-only views, comparative reporter rankings dashboards, web UI, proactive alerts, predictive trend analysis, causal "why did this work" inference.

## 3. Decisions captured during brainstorming

| Decision | Choice | Rationale |
|---|---|---|
| Primary user | Reporters first | Editor features are Phase 3 |
| Surface | Slack first; web UI in Phase 2 | Reporters live in Slack; zero adoption friction |
| Data freshness | Hybrid: hourly cache + GA4 Realtime fallback | 90% of questions don't need realtime; the rest do |
| Phase 1 sources | Mather + GA4 + WordPress | WP replaces MFN's tag-filtered views; MFN runs in parallel until reconciled |
| Identity | Slack email → WP author email; manual override table for edge cases | No new auth; freelancers handled by override |
| Access control | None — anyone sees anyone's aggregate output | User chose full transparency |
| LLM strategy | Defined tools only; no text-to-SQL | Accuracy guarantee requires auditable code paths |
| Unanswerable questions | Refuse cleanly + log to wishlist table | Drives Phase 2 tool prioritization from real demand |
| Deployment | Single small VPS (DigitalOcean droplet) | Cheap, simple, reversible |
| Post identity resolution | Fuzzy match against reporter's recent stories; auto-answer if one strong match (with title shown), confirm if ambiguous | Balances friction and correctness |
| Comparison baselines | Reporter's own 30-day median + section 30-day median | Skips story-type median (tag discipline uneven) |
| Codebase shape | Standalone new repo, copying SQL/queries from existing dashboards | No coupling to dashboards; trivial duplication; reversible |

## 4. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  DigitalOcean droplet (~$12-20/mo)                              │
│                                                                 │
│  ┌──────────────────┐     ┌──────────────────┐                  │
│  │ Slack listener   │     │  Hourly ETL      │                  │
│  │ (FastAPI + Bolt, │     │  (systemd timer) │                  │
│  │  Socket Mode)    │     │                  │                  │
│  └────────┬─────────┘     └────────┬─────────┘                  │
│           │                        │                            │
│           ▼                        ▼                            │
│  ┌──────────────────┐     ┌──────────────────┐                  │
│  │  Tool layer      │     │ Collectors:      │                  │
│  │  (Python funcs)  │     │  mather.py       │                  │
│  │                  │     │  ga4.py          │                  │
│  └────────┬─────────┘     │  wordpress.py    │                  │
│           │               └────────┬─────────┘                  │
│           ▼                        ▼                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Postgres (local)                                       │    │
│  │  - posts (post_id, url, author, section, tags, …)       │    │
│  │  - mather_epv_hourly                                    │    │
│  │  - author_goals (mirror of Mather AuthorGoals)          │    │
│  │  - ga4_pageviews_hourly, ga4_traffic_sources_hourly     │    │
│  │  - reporter_baselines, section_baselines (rolling 30d)  │    │
│  │  - slack_user_map (email → wp_author_id, overrides)     │    │
│  │  - unanswered_questions (wishlist)                      │    │
│  │  - etl_runs                                             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  Daily pg_dump → Backblaze B2                                   │
└─────────────────────────────────────────────────────────────────┘
       ▲                              ▲                       ▲
       │                              │                       │
  Slack workspace               Claude API             GA4 Realtime API
  (Socket Mode — no             (tool-use; LLM         (live fallback for
   inbound port needed)          never does math)       "right now" qs)
```

**Key shapes:**

- One droplet, two systemd units: `slack-listener.service` (always-on) and `etl-hourly.timer` (hourly cron).
- **Slack via Socket Mode**: no inbound port, no public webhook, no TLS setup needed. The listener dials *out* and holds the connection.
- Tool layer is pure Python functions invoked by Claude tool-use. SQL never crosses the LLM boundary.
- Collectors only write to Postgres. Tools only read from Postgres (except live GA4 Realtime). A slow Mather query can't block a Slack response.

## 5. Components

```
newsroom-analytics-bot/
├── README.md
├── pyproject.toml
├── .env.example
│
├── src/
│   ├── collectors/                       # ETL — read-only against external systems
│   │   ├── mather.py                     # EPV_Entry, Daily_EPVs, QuarterlyProgress, AuthorGoals
│   │   ├── ga4.py                        # Hourly batch + Realtime client
│   │   └── wordpress.py                  # Posts + tags + author + section + publish_ts
│   │
│   ├── store/
│   │   ├── schema.sql
│   │   ├── migrations/
│   │   ├── upserts.py
│   │   └── baselines.py                  # Rolling reporter/section median computation
│   │
│   ├── tools/                            # One tool per file
│   │   ├── _registry.py                  # Tool schema + dispatch
│   │   ├── identify_user.py
│   │   ├── find_post_by_fuzzy_title.py
│   │   ├── get_story_metrics.py
│   │   ├── get_traffic_sources.py
│   │   ├── get_subs_attributed.py
│   │   ├── compare_to_baselines.py
│   │   ├── get_goal_progress.py
│   │   ├── get_top_stories_for_author.py
│   │   ├── get_audience_signals.py
│   │   └── log_unanswered.py
│   │
│   ├── chatbot/
│   │   ├── claude_client.py              # Anthropic SDK wrapper, prompt caching on
│   │   ├── system_prompt.py              # Accuracy rules: no math, attribute sources, refuse cleanly
│   │   ├── conversation.py               # Tool-dispatch loop
│   │   └── formatting.py                 # Slack markdown rendering
│   │
│   ├── slack/
│   │   ├── app.py                        # Bolt entry (Socket Mode)
│   │   ├── handlers.py                   # @mention, DM, /howsmystory
│   │   └── identity.py                   # Slack email → wp_author_id (+ overrides)
│   │
│   ├── etl/
│   │   ├── hourly.py
│   │   ├── backfill.py                   # One-shot 90-day history populate
│   │   └── reconcile.py                  # Nightly comparison vs EPV dashboard
│   │
│   └── config.py                         # Pydantic settings from env
│
├── tests/
│   ├── unit/                             # Per-tool, against frozen JSON fixtures
│   ├── fixtures/
│   ├── integration/                      # Real Postgres in Docker, mocked APIs
│   ├── reconcile/                        # Asserts numbers match EPV dashboard exactly
│   └── manual/golden_questions.md        # 20 real reporter questions, eyeballed pre-release
│
├── deploy/
│   ├── systemd/
│   │   ├── slack-listener.service
│   │   ├── etl-hourly.service
│   │   └── etl-hourly.timer
│   ├── backup.sh                         # pg_dump → Backblaze B2
│   └── deploy.sh                         # One-command from local
│
└── docs/
    ├── plans/                            # Design docs (this one)
    └── runbook.md                        # On-call cheatsheet
```

**Component-level decisions:**

1. **One tool per file.** Adding a tool = one new file + one line in registry. Removing = delete the file. No giant `tools.py`.
2. **Collectors write; tools read.** Strict separation. Slow Mather = stale data, never a blocked response.
3. **`identify_user` is a tool**, not framework code. Every conversation log shows exactly who the bot thought it was talking to.

## 6. Tool catalog (Phase 1)

Every tool returns structured JSON with explicit `source` and `as_of` fields on every metric.

| Tool | Inputs | Returns |
|---|---|---|
| `identify_user` | `slack_user_id` | `{wp_author_id, full_name, email, is_known}` |
| `find_post_by_fuzzy_title` | `query, author_id?, window_days=30` | Ranked candidates with scores |
| `get_story_metrics` | `post_id, window` | EPVs, pageviews, sessions, engaged time, scroll depth |
| `get_traffic_sources` | `post_id, window` | Channels with pageviews + share % |
| `get_subs_attributed` | `post_id, window` | Subscription conversions (Mather) |
| `compare_to_baselines` | `post_id, metric` | Value + reporter 30d median + section 30d median + ratios |
| `get_goal_progress` | `wp_author_id, quarter?` | Quarter EPVs, goal, % to goal, bonus threshold, projected EPVs, pace verdict (read from Mather `QuarterlyProgress`) |
| `get_top_stories_for_author` | `wp_author_id, window, group_by=None, limit=10` | Ranked stories; optional rollup by section, tag, day-of-week, time-of-day, headline-length |
| `get_audience_signals` | `wp_author_id, window` | Top tags, sources, referrers, sections among that author's stories |
| `log_unanswered` | `slack_user_id, question, reason` | Wishlist log entry |

**10 tools. Anything else is Phase 2.**

### Honesty boundaries

- The bot describes the past; it doesn't prescribe the future.
- `get_audience_signals` returns *"among stories with this byline, these tags / sources / topics drove the most engagement"* — never *"your audience wants more X."*
- The bot does not infer causation. It can describe rates ("3,204 EPVs in 4 hours") and pre-computed projections (from a tool field), never invent ones.

## 7. Data flow

**Hourly ETL** (systemd timer, top of every hour):

1. `wordpress.py` → posts published or modified in last 7 days → upsert `posts`.
2. `mather.py` → EPV deltas since last run + full snapshot of `AuthorGoals` and `QuarterlyProgress` → upsert `mather_epv_hourly`, `author_goals`.
3. `ga4.py` → hourly pageviews + traffic sources for trailing 7 days → upsert `ga4_*`.
4. `baselines.py` → recompute rolling 30/90-day reporter and section medians.
5. Log run to `etl_runs`. If any step fails, others still run; bot reports stale data with correct `as_of`.

**Live path** (per Slack message): tools read Postgres only, except `get_story_metrics` with `window="last_hour"` or `"realtime"`, which calls GA4 Realtime API directly and merges with cached EPV.

**Backfill**: one-time `etl/backfill.py` populates ~90 days of history on first install so baselines aren't empty on day one.

## 8. Error handling

- **Stale data**: every tool response includes `as_of`. If older than 90 minutes, response sets `freshness_warning: true`; LLM is instructed to surface that.
- **External API failure**: ETL retries 3× with backoff, logs, continues. Bot keeps answering from last good cache. After 6 hours of failure → Slack alert in `#analytics-bot-alerts`.
- **Tool exception**: caught by dispatch; returned to Claude as `{error, retryable}`. LLM apologizes cleanly, calls `log_unanswered`, never fabricates.
- **Ambiguous post**: `find_post_by_fuzzy_title` returns scored candidates. If top score < 0.8 or top two within 0.05, LLM asks the user to disambiguate. Otherwise auto-answers and surfaces the title at the top of the response.
- **Unknown user**: `identify_user` returns `is_known: false`. Bot replies with the escalation path to add the mapping.
- **LLM-numeric audit**: every assistant message passes through a post-filter that extracts numerals and confirms each appears verbatim in a tool result from that turn. Mismatch → message is replaced with a generic apology + bug log. **This is the last line of defense for the accuracy guarantee.**

## 9. Testing

Three layers:

1. **Unit tests per tool** — frozen JSON fixtures of Mather/GA4/WP responses. ~60 tests, < 2s.
2. **Integration tests** — Postgres in Docker, full ETL against fixtures, each tool exercised end-to-end. ~15 tests, < 30s.
3. **Reconciliation tests** — nightly cron. For every reporter in `AuthorGoals`, run `get_goal_progress(author, current_quarter)` and assert numbers match the EPV dashboard's CSV output exactly. Drift > 0 fails the run, pings `#analytics-bot-alerts`. **This is the contract that keeps the chatbot honest with the dashboards reporters already trust.**

Plus `tests/manual/golden_questions.md` — 20 real reporter questions, eyeballed before every release.

## 10. Deployment

- Single Ubuntu LTS droplet, ~$12–20/mo.
- `slack-listener.service` (systemd, restart=always) + `etl-hourly.timer` + `reconcile.timer` (nightly).
- Postgres 16 on localhost; daily `pg_dump` → Backblaze B2 (separate object store, separate credentials).
- One-command deploy: `deploy/deploy.sh` rsyncs code, runs migrations, restarts units.
- Firewall: SSH only. Slack uses Socket Mode (outbound). No inbound web port in Phase 1.
- Logging: stdout → systemd-journald. Errors above WARN → Slack `#analytics-bot-alerts`.

## 11. Phasing

**Phase 1 — MVP (target: 4–6 weeks).** Slack only. Mather + GA4 + WP collectors. The 10 tools. Reconciliation tests against EPV dashboard. Reporter-facing only — but no access gating, anyone can ask anything.

**Phase 2 — Web UI + breadth (later).** Web app at internal URL. Add Mailchimp tool, Search Console tool, social tools (Meta + X) based on the wishlist log. Charts where text isn't enough.

**Phase 3 — Editor lens (later).** Aggregate-by-section dashboards, proactive alerts ("your story crossed 10K"), daily briefing emails. Re-evaluate access control if needed.

## 12. Open questions / things to revisit

- **MFN cutover criterion**: how many days of clean reconciliation between WP-derived metrics and MFN before we kill the MFN subscription? Default proposal: 30 days, drift < 1% on every comparable view.
- **Slack user → WP email mismatches**: who maintains the `slack_user_map` overrides table? Default: same person who maintains `AuthorGoals` quarterly.
- **Anthropic API cost ceiling**: alert threshold? Default: $100/mo soft cap with a Slack ping; hard cap not enforced in Phase 1.
- **Unanswered-question review cadence**: weekly? Whoever owns Phase 2 prioritization reads the wishlist log on Mondays.

## 13. Explicitly out of scope

To prevent scope creep, the following are NOT part of Phase 1:

- Causal "why did this story work" analysis
- Predictive "which story will go viral" forecasting
- Editor-only comparative reporter rankings (transparency was chosen)
- Newsletter / Mailchimp data
- Search Console data
- Social platform data (Meta, X)
- Charts or rich visual rendering
- Web UI
- Proactive alerts or briefing emails
- A SQL-fallback for unsupported questions

Each of these has a real argument for inclusion, and each will be reconsidered in Phase 2/3 against demand from the wishlist log.
