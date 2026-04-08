# Flagg vs LeBron Scoring Tracker — Design

## Overview

A tongue-in-cheek embeddable WordPress graphic that tracks Cooper Flagg's career scoring pace against LeBron James' all-time record (40,474 points). Straight stats with playful, dynamically generated copy.

## Architecture: JS Widget + WP REST API Proxy

### Data Flow

1. Reader loads page with `[flagg-vs-lebron]` shortcode
2. Shortcode renders container div, enqueues JS/CSS
3. JS calls `/wp-json/bdn/v1/flagg-stats`
4. PHP endpoint checks WP transient cache (1-hour TTL)
   - Cache hit: return cached JSON
   - Cache miss: fetch from balldontlie.io API, compute stats, cache, return
5. JS renders progress bar with stats and cheeky headline

### API Source

- **balldontlie.io** free tier (requires API key, stored in WP options)
- Fetches career season stats, sums total points across all seasons
- LeBron's total hardcoded at 40,474 (retired)

### REST Endpoint

`GET /wp-json/bdn/v1/flagg-stats`

Returns:
```json
{
  "points": 847,
  "games": 64,
  "ppg": 13.2,
  "percentage": 2.1,
  "projected_year": 2049,
  "projected_age": 47,
  "lebron_total": 40474
}
```

### Projection Math

- Games per season: 82 (assume full seasons)
- Seasons remaining: `(40474 - current_points) / (ppg * 82)`
- Projected year: current year + seasons remaining
- Projected age: Flagg born 2006-12-21, so age = projected year - 2006

## The Graphic

- **Max width:** 600px, responsive
- **Headline:** Dynamic — e.g., "Cooper Flagg is 0.4% of the way to catching LeBron"
- **Progress bar:** Full-width. LeBron = 100%. Flagg = tiny sliver on left. Labeled.
- **Subtext:** "At his current pace of X.X PPG, Flagg will pass LeBron in **2049** (age 47)"
- **Footer:** "Data: balldontlie.io | BDN"
- **Tone:** Straight stats, playful framing

## File Structure

```
flagg-vs-lebron/
├── flagg-vs-lebron.php      # Plugin: shortcode, REST endpoint, transient cache
├── assets/
│   ├── flagg-tracker.js     # Vanilla JS widget
│   └── flagg-tracker.css    # Styles
└── README.md
```

Standalone WP plugin. Activate and `[flagg-vs-lebron]` is available site-wide.

## Decisions

- **Why WP transient cache:** Protects against API rate limits on high-traffic pages
- **Why vanilla JS:** No build tools needed, minimal footprint for an embed
- **Why shortcode:** Reusable across multiple pages in Newspack
- **LeBron total hardcoded:** He's retired; update manually only if needed
