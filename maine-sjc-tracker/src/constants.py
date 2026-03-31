BASE_URL = "https://www.courts.maine.gov/courts/sjc"
CALENDAR_URL = f"{BASE_URL}/calendar.html"
MEMORANDA_URL = f"{BASE_URL}/memdec.html"
OPINIONS_URL = f"{BASE_URL}/opinions.html"
BRIEFS_BASE_URL = "https://www.courts.maine.gov/courts/sjc/briefs"

COUNTY_CODES = {
    "And": "Androscoggin",
    "Aro": "Aroostook",
    "BCD": "Business & Consumer Docket",
    "Cum": "Cumberland",
    "Fra": "Franklin",
    "Han": "Hancock",
    "Ken": "Kennebec",
    "Kno": "Knox",
    "Lin": "Lincoln",
    "Oxf": "Oxford",
    "Pen": "Penobscot",
    "Pis": "Piscataquis",
    "Sag": "Sagadahoc",
    "Som": "Somerset",
    "SRP": "State Register of Probate",
    "Wal": "Waldo",
    "Was": "Washington",
    "Yor": "York",
}

SHEET_COLUMNS = [
    "Docket Number",
    "Case Name",
    "County",
    "Attorney (Appellant)",
    "Attorney (Appellee)",
    "Trial Judge",
    "Subject",
    "Status",
    "Argument Date",
    "Decision Date",
    "Outcome",
    "Brief Links",
    "Opinion Link",
    "Summary",
    "First Seen",
    "Last Updated",
]
