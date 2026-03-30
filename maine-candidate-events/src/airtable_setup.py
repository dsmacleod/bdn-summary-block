"""One-time script to create the Candidate Events table in Airtable."""

import os
from pyairtable import Api
from pyairtable.models.schema import FieldSchema

def create_table():
    api = Api(os.environ["AIRTABLE_API_KEY"])
    base = api.base(os.environ["AIRTABLE_BASE_ID"])

    # We'll create the table via the Airtable MCP tool instead,
    # since pyairtable doesn't support table creation directly.
    # This file documents the schema for reference.
    print("Create table 'Candidate Events' with these fields:")
    print("- Candidate (Single Select)")
    print("- Race (Single Select: Senate, Governor, CD-1, CD-2)")
    print("- Event Type (Single Select: Town Hall, Rally, Debate, Fundraiser, Press Conference, Campaign Stop, Forum, Other)")
    print("- Date & Time (Date with time)")
    print("- Location (Single Line Text)")
    print("- Source URL (URL)")
    print("- Source (Single Select: Campaign Website, Facebook, Party Calendar, News, Other)")
    print("- Last Verified (Date)")

if __name__ == "__main__":
    create_table()
