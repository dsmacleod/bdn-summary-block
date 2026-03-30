# Maine Candidate Event Tracker

Automated daily scraper that finds public events for Maine 2026 candidates and populates an Airtable table for the BDN newsroom.

## Races Tracked
- US Senate (Collins' seat) — **priority**
- Governor
- US House CD-1
- US House CD-2

## Setup

1. Clone this repo
2. `pip install -r requirements.txt`
3. Set environment variables:
   - `ANTHROPIC_API_KEY`
   - `AIRTABLE_API_KEY`
   - `AIRTABLE_BASE_ID`
4. Run: `python -m src.scraper`

## Updating Candidates

Edit `candidates.yaml` to add/remove candidates or update their source URLs.

## GitHub Actions

Runs daily at 8am ET. Can also be triggered manually from the Actions tab.
