import json
import logging
import anthropic

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Extract all upcoming political campaign events from the following text for the candidate "{candidate_name}".

For each event, return a JSON object with:
- event_type: one of "Town Hall", "Rally", "Debate", "Fundraiser", "Press Conference", "Campaign Stop", "Forum", "Other"
- date_time: ISO 8601 format (YYYY-MM-DDTHH:MM:SS). If no time is given, use T00:00:00.
- location: venue name and city/town (e.g., "Bangor Civic Center, Bangor")
- source_url: "{source_url}"

Return ONLY a JSON array. If no events are found, return [].
Do NOT include past events (before today's date).
Do NOT hallucinate events — only extract events explicitly mentioned in the text.

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
