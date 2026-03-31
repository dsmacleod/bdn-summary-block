# Maine SJC Tracker

Multi-source scraper that tracks pending Maine Supreme Judicial Court (Law Court) cases and writes results to a Google Sheet on a weekly schedule.

## Sources

- **Calendar** — Scheduled oral arguments
- **Memoranda of Decision** — Decided cases (unpublished)
- **Published Opinions** — Decided cases (published)
- **Brief Directory Probing** — Early-stage case discovery via brief filings

## Setup

1. Create a Google Cloud service account with the Sheets API enabled.
2. Download the service account JSON key.
3. Create a Google Sheet with a header row using these columns:

   `Docket Number` | `Case Name` | `County` | `Attorney (Appellant)` | `Attorney (Appellee)` | `Trial Judge` | `Subject` | `Status` | `Argument Date` | `Decision Date` | `Outcome` | `Brief Links` | `Opinion Link` | `Summary` | `First Seen` | `Last Updated`

4. Share the Google Sheet with the service account email (give it Editor access).
5. Set these secrets in your GitHub repository:
   - `GOOGLE_CREDENTIALS_JSON` — the full JSON key file contents
   - `GOOGLE_SHEET_ID` — the ID from your Sheet URL

## Running manually

Set the environment variables, then:

```
cd maine-sjc-tracker && python main.py
```

## Schedule

Runs weekly on Monday at 6 AM ET via GitHub Actions. To change the schedule, edit the cron expression in `.github/workflows/scrape.yml`.

## Tests

```
cd maine-sjc-tracker && python -m pytest -v
```
