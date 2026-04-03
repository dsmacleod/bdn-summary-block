# Maine Candidate Event Tracker — Design

## Purpose

Automated daily scraper that finds public events for Maine 2026 congressional and gubernatorial candidates and populates an Airtable table for the BDN newsroom. Priority is on the US Senate race for Susan Collins' seat.

## Races Tracked

- US Senate (Collins' seat)
- Governor (Mills term-limited)
- US House CD-1
- US House CD-2

## Data Model — Airtable

New table "Candidate Events" in the existing BDN News Budget base (`appwkB7dSz28n4knq`).

| Field | Type | Notes |
|-------|------|-------|
| Candidate | Single select | Declared candidates |
| Race | Single select | Senate, Governor, CD-1, CD-2 |
| Event Type | Single select | Town Hall, Rally, Debate, Fundraiser, Press Conference, Campaign Stop, Forum, Other |
| Date & Time | Date (with time) | |
| Location | Single line text | Venue + city/town |
| Source URL | URL | Where the event was found |
| Source | Single select | Campaign Website, Facebook, Party Calendar, News, Other |
| Last Verified | Date | When scraper last confirmed this event |

## Architecture

Python scraper running daily via GitHub Actions.

### Pipeline

1. **Load candidate registry** — `candidates.yaml` config with names, races, parties, and source URLs per candidate.
2. **Fetch sources** — For each candidate, scrape campaign website, Facebook page, party calendars, and Google search results using `requests` + `trafilatura`.
3. **Extract events** — Feed raw text to Claude API (Haiku) with a structured extraction prompt. Returns JSON array of events.
4. **Deduplicate** — Match against existing Airtable records on candidate + date + location (fuzzy location matching).
5. **Push to Airtable** — Insert new events via `pyairtable`.

### Candidate Registry

YAML file in the repo listing declared/likely candidates per race with their source URLs. Easy to update without code changes.

### Secrets (GitHub Actions)

- `ANTHROPIC_API_KEY`
- `AIRTABLE_API_KEY`

### Dependencies

- `requests` — HTTP fetching
- `trafilatura` — HTML to clean text
- `googlesearch-python` — Google search results
- `anthropic` — Claude API
- `pyairtable` — Airtable API
- `pyyaml` — Config parsing
- `thefuzz` — Fuzzy string matching for dedup

## Approach

Using Claude API for event extraction rather than brittle per-site CSS selectors. Campaign sites are inconsistent and change frequently; LLM extraction is more resilient. Cost is minimal (<$1/day at this volume using Haiku).
