"""Merge cases from multiple sources, deduplicating by docket number."""

STATUS_PRIORITY = {"Decided": 3, "Scheduled": 2, "Briefing": 1}


def merge_cases(
    calendar_cases: dict,
    memoranda_cases: dict,
    opinions_cases: dict,
    probed_cases: dict,
) -> dict:
    """Merge cases from all sources. Later sources fill gaps but don't overwrite.
    Status priority: Decided > Scheduled > Briefing."""
    merged = {}

    all_sources = [calendar_cases, memoranda_cases, opinions_cases, probed_cases]
    for source in all_sources:
        for key, case in source.items():
            if key not in merged:
                merged[key] = dict(case)
            else:
                existing = merged[key]
                for field, value in case.items():
                    if field == "status":
                        new_priority = STATUS_PRIORITY.get(value, 0)
                        old_priority = STATUS_PRIORITY.get(existing.get("status", ""), 0)
                        if new_priority > old_priority:
                            existing["status"] = value
                    elif field == "brief_links":
                        existing_links = set(existing.get("brief_links", []))
                        existing["brief_links"] = list(existing_links | set(value))
                    elif not existing.get(field) and value:
                        existing[field] = value

    return merged
