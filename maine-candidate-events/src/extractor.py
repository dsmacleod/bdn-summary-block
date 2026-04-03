import json
import logging
from datetime import date
import anthropic

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Extract ONLY explicitly announced upcoming events from the following text for the candidate "{candidate_name}".

STRICT RULES:
- ONLY extract events where the text explicitly states a specific date AND location for a future event.
- A news article ABOUT a candidate is NOT an event. Do not invent events from news coverage.
- Do NOT guess or infer dates. The date must be clearly written in the text (e.g., "April 15" or "March 30 at 6pm").
- Do NOT guess or infer locations. The venue/address must be explicitly stated.
- If the text describes an event that already happened (past tense: "held", "attended", "spoke at"), skip it entirely.
- When in doubt, return []. It is MUCH better to miss an event than to fabricate one.

Today's date is {today}. Do NOT include events before today.

For each CONFIRMED upcoming event, return a JSON object with:
- event_type: one of "Town Hall", "Rally", "Debate", "Fundraiser", "Press Conference", "Campaign Stop", "Forum", "Other"
- date_time: ISO 8601 format (YYYY-MM-DDTHH:MM:SS). If no time is given, use T00:00:00.
- location: venue name and city/town (e.g., "Bangor Civic Center, Bangor")
- source_url: "{source_url}"

Return ONLY a JSON array. If no confirmed upcoming events are found, return [].

Text:
{text}
"""

def extract_events(
    candidate_name: str, text: str, source_url: str
) -> list[dict]:
    """Use Claude to extract structured events from raw text."""
    if not text or not text.strip():
        return []

    client = anthropic.Anthropic()
    prompt = EXTRACTION_PROMPT.format(
        candidate_name=candidate_name,
        source_url=source_url,
        text=text[:8000],
        today=date.today().isoformat(),
    )

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        # Handle markdown code blocks
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        events = json.loads(raw)
        return events if isinstance(events, list) else []
    except Exception as e:
        logger.warning(f"Extraction failed for {candidate_name}: {e}")
        return []
