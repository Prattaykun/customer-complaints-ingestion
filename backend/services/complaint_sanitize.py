"""Shared complaint field normalization before DB writes."""

from __future__ import annotations

from typing import Any, Optional


def normalize_severity_level(
    value: Any,
    risk_score: Optional[float] = None,
) -> str:
    """Map free-text severity into Critical | Major | Minor (DB-safe)."""
    text = str(value or "").strip()
    lowered = text.lower()

    if "critical" in lowered:
        return "Critical"
    if "major" in lowered or "moderate" in lowered or "significant" in lowered:
        return "Major"
    if "minor" in lowered or "low" in lowered:
        return "Minor"
    if text in {"Critical", "Major", "Minor"}:
        return text

    try:
        score = float(risk_score) if risk_score is not None else None
    except (TypeError, ValueError):
        score = None

    if score is not None:
        if score >= 70:
            return "Critical"
        if score >= 40:
            return "Major"
        if score > 0:
            return "Minor"

    return text[:100] if text else ""


def sanitize_complaint_for_db(data: dict) -> dict:
    """Return a copy of complaint data with DB-safe field values."""
    out = dict(data)
    out["severityLevel"] = normalize_severity_level(
        out.get("severityLevel"),
        out.get("riskScore"),
    )
    # Soft-cap short string columns in case models overflow
    short_caps = {
        "productStrength": 100,
        "dosageForm": 100,
        "batchNumber": 100,
        "lotNumber": 100,
        "manufacturingDate": 50,
        "expiryDate": 50,
        "complaintCategory": 100,
        "countryCode": 20,
        "dateOfComplaint": 50,
        "dateOfIncident": 50,
        "status": 50,
    }
    for key, limit in short_caps.items():
        val = out.get(key)
        if isinstance(val, str) and len(val) > limit:
            out[key] = val[:limit]
    name = out.get("productName")
    if isinstance(name, str) and len(name) > 255:
        out["productName"] = name[:255]
    for key in ("complainantName", "complainantContact", "complainantEmail"):
        val = out.get(key)
        if isinstance(val, str) and len(val) > 255:
            out[key] = val[:255]
    phone = out.get("complainantPhone")
    if isinstance(phone, str) and len(phone) > 100:
        out["complainantPhone"] = phone[:100]
    return out
