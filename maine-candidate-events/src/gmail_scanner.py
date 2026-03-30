"""
Gmail scanner for Maine candidate event press releases and media advisories.

This script is meant to be run locally via a scheduled Claude Code task,
since it requires Gmail MCP access (not available on GitHub Actions).

Usage: claude -p "Run the Gmail scanner for Maine candidate events"
"""

# This module provides the Gmail search queries and candidate email mappings.
# The actual scanning is done by Claude Code via the Gmail MCP tool,
# since we need OAuth access that only runs locally.

CAMPAIGN_SENDERS = {
    "press@janetmills.com": ("Janet Mills", "Senate"),
    "press@grahamforsenate.com": ("Graham Platner", "Senate"),
    "press@electjordan.com": ("Jordan Wood", "CD-2"),
    "lfanguen@mainedems.org": (None, None),  # Maine Dems party press
    "press@collinsforme.com": ("Susan Collins", "Senate"),
    "dave@indivisiblebangor.org": (None, None),  # Advocacy org
}

GMAIL_SEARCH_QUERIES = [
    # Campaign press releases about events
    'subject:(event OR "town hall" OR rally OR forum OR debate OR advisory OR schedule OR appearance) from:(press@ OR campaign@ OR info@) Maine after:{today}',
    # Media advisories
    'subject:(advisory OR "media advisory" OR "press advisory") Maine after:{today}',
    # Direct candidate event announcements
    'subject:(event OR "town hall" OR rally OR schedule) (Collins OR Mills OR Platner OR Jackson OR Pingree OR LePage OR Baldacci OR Dunlap) after:{today}',
]

AIRTABLE_BASE_ID = "appwkB7dSz28n4knq"
AIRTABLE_TABLE_NAME = "Candidate Events"
