# A/B/Y Headline Testing Plugin — Design

## Goal

Allow BDN editors to test 2-3 headline variants on any post, automatically determine the highest-CTR winner based on homepage/section front clicks, and promote the winner to the canonical headline.

## Approach

Client-side headline swap (Approach A). Headlines are stored as post meta, swapped via a lightweight JS snippet on the frontend, tracked through GA4 custom events, and auto-resolved by a WP-Cron job that queries the GA4 Data API.

## Data Model

All data stored as post meta — no custom tables.

| Meta Key | Type | Description |
|---|---|---|
| `_headline_variants` | JSON array | `[{id: "a", text: "..."}, {id: "b", text: "..."}, ...]` |
| `_headline_test_status` | string | `active`, `completed`, `paused` |
| `_headline_test_winner` | string | Variant ID of the winner |

Global settings (stored in `wp_options`):
- Minimum impressions per variant before evaluation (default: 1,000)
- Maximum test duration in hours (default: 72)
- GA4 property ID
- GA4 service account credentials

Variant A is always the current `post_title`. On winner declaration, `post_title` is updated to the winning text.

## Editor UI

### Post Editor Sidebar Panel (Gutenberg SlotFill)

- "Headline Test" panel in the post sidebar
- Current post title shown as Variant A (read-only)
- Text inputs for Variant B and optional Variant C
- Start/Stop test toggle
- When complete, shows winner with CTR stats

### Admin Screen (Tools > Headline Tests)

- Table of all active and recent tests
- Columns: post title, variants, impressions, CTR, status, winner
- Create new test by searching for a post
- Manually end a test and pick a winner

## Frontend JS & Tracking

### Headline Swap (~2KB async script)

- Finds headline elements with `data-headline-test` attribute (injected via `the_title` filter)
- Checks localStorage for existing variant assignment; assigns randomly if none
- Swaps headline text in DOM
- Fires GA4 events:
  - `headline_test_impression`: params `post_id`, `variant_id`
  - `headline_test_click`: params `post_id`, `variant_id`

### Anti-Flash CSS

- Inline style: `[data-headline-test] { visibility: hidden }`
- JS adds `.ht-resolved` class after swap to restore visibility
- CSS fallback: animation restores visibility after 500ms if JS doesn't run

### Variant Assignment

- Stored in localStorage keyed by post ID
- Sticky per visitor per post
- Even random distribution

## Auto-Resolution

### WP-Cron Job (Hourly)

1. Queries GA4 Data API for impression and click events on active tests
2. Calculates CTR per variant
3. Applies chi-squared test (p < 0.05) once minimum impressions reached
4. If max duration reached without significance, picks the leading variant
5. On winner: sets status to `completed`, records winner, updates `post_title`

### GA4 API Auth

- Service account JSON key configured in plugin settings
- Stored securely (wp-config constant or encrypted option)

### Fallback

- If GA API unreachable, cron skips and retries next hour
