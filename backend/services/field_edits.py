"""Parse simple natural-language field edits and apply them to complaint data."""

from __future__ import annotations

import re
from typing import Optional

# Map spoken field names → camelCase complaint keys
FIELD_ALIASES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(?:product\s*)?name\b", re.I), "productName"),
    (re.compile(r"\b(?:product\s*)?strength\b", re.I), "productStrength"),
    (re.compile(r"\bdosage\s*form\b", re.I), "dosageForm"),
    (re.compile(r"\bbatch\s*(?:number|no\.?|#)?\b", re.I), "batchNumber"),
    (re.compile(r"\blot\s*(?:number|no\.?|#)?\b", re.I), "lotNumber"),
    (re.compile(r"\bmanufacturing\s*date\b", re.I), "manufacturingDate"),
    (re.compile(r"\bexpiry\s*date\b", re.I), "expiryDate"),
    (re.compile(r"\b(?:complaint\s*)?categor(?:y|ies)\b", re.I), "complaintCategory"),
    (re.compile(r"\b(?:complaint\s*)?description\b", re.I), "complaintDescription"),
    (re.compile(r"\bcomplainant\s*name\b", re.I), "complainantName"),
    (re.compile(r"\b(?:complainant\s*)?email\b", re.I), "complainantEmail"),
    (re.compile(r"\b(?:complainant\s*)?phone\b", re.I), "complainantPhone"),
    (re.compile(r"\bcountry\s*code\b", re.I), "countryCode"),
    (re.compile(r"\bdate\s*of\s*complaint\b", re.I), "dateOfComplaint"),
    (re.compile(r"\bdate\s*of\s*incident\b", re.I), "dateOfIncident"),
    (re.compile(r"\bseverity\b", re.I), "severityLevel"),
    (re.compile(r"\brisk\s*score\b", re.I), "riskScore"),
]

EDIT_PATTERNS = [
    # edit/change/update/set/modify the batch number to 12345
    re.compile(
        r"(?:please\s+)?(?:edit|change|update|set|modify|correct|fix)\s+"
        r"(?:the\s+)?(?P<field>[\w\s/#.]+?)\s+"
        r"(?:to|=|:)\s*(?P<value>.+?)\s*$",
        re.I,
    ),
    # batch number: 12345 / batch number = 12345
    re.compile(
        r"^(?P<field>batch\s*(?:number|no\.?|#)?|lot\s*(?:number|no\.?|#)?|"
        r"product\s*name|product\s*strength|dosage\s*form|"
        r"complainant\s*(?:name|email|phone)|country\s*code|"
        r"expiry\s*date|manufacturing\s*date)\s*[:=]\s*(?P<value>.+)$",
        re.I,
    ),
]


def _resolve_field(field_text: str) -> Optional[str]:
    text = field_text.strip().strip("\"'")
    for pattern, key in FIELD_ALIASES:
        if pattern.search(text):
            return key
    return None


def _clean_value(raw: str) -> str:
    value = raw.strip().strip(" .")
    value = value.strip("\"'`")
    # Drop trailing polite fluff
    value = re.sub(r"\s+(please|thanks|thank you)\.?$", "", value, flags=re.I)
    return value.strip()


def looks_like_field_edit(message: str) -> bool:
    text = (message or "").strip()
    if not text or len(text) > 240:
        return False
    lowered = text.lower()
    if not any(w in lowered for w in ("edit", "change", "update", "set", "modify", "correct", "fix", "=", ":")):
        return False
    return parse_field_edits(text) != {}


def parse_field_edits(message: str) -> dict:
    """Extract {camelCaseField: value} from a short edit instruction."""
    text = (message or "").strip()
    if not text:
        return {}

    # Prefer last non-empty line (user may paste context + edit)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    candidates = lines[-2:] if len(lines) > 1 else lines

    edits: dict = {}
    for line in candidates:
        for pattern in EDIT_PATTERNS:
            match = pattern.search(line)
            if not match:
                continue
            field_key = _resolve_field(match.group("field"))
            value = _clean_value(match.group("value"))
            if not field_key or not value:
                continue
            if field_key == "riskScore":
                try:
                    edits[field_key] = float(re.sub(r"[^\d.]", "", value) or 0)
                except ValueError:
                    continue
            else:
                edits[field_key] = value
            break
    return edits


def apply_field_edits(complaint_data: dict, message: str) -> dict:
    """Merge parsed NL edits into complaint_data (always wins over stale values)."""
    edits = parse_field_edits(message)
    if not edits:
        return complaint_data
    updated = dict(complaint_data or {})
    updated.update(edits)
    return updated
