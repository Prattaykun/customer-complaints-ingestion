"""
Direct document → LLM extraction.

Sends the uploaded file (PDF/image/text) to Gemini and returns structured
complaint JSON. Avoids lossy pypdf text extraction before the model sees the doc.
"""

from __future__ import annotations

import json
import re
from io import BytesIO
from typing import Any, Optional

from google import genai
from google.genai import types

from config import GOOGLE_API_KEY, DOCUMENT_MODEL, DOCUMENT_FALLBACK_MODELS
from services.complaint_sanitize import normalize_severity_level

COMPLAINT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "productName": {"type": "string"},
        "productStrength": {"type": "string"},
        "dosageForm": {"type": "string"},
        "batchNumber": {"type": "string"},
        "lotNumber": {"type": "string"},
        "manufacturingDate": {"type": "string"},
        "expiryDate": {"type": "string"},
        "complaintCategory": {"type": "string"},
        "complaintDescription": {"type": "string"},
        "complainantName": {"type": "string"},
        "complainantContact": {"type": "string"},
        "complainantPhone": {"type": "string"},
        "complainantEmail": {"type": "string"},
        "countryCode": {"type": "string"},
        "dateOfComplaint": {"type": "string"},
        "dateOfIncident": {"type": "string"},
        "severityLevel": {"type": "string"},
        "riskScore": {"type": "number"},
        "recommendedActions": {"type": "array", "items": {"type": "string"}},
        "rootCauseHypothesis": {"type": "string"},
        "capaRecommendation": {"type": "string"},
        "complaintSummary": {"type": "string"},
    },
    "required": [
        "productName",
        "batchNumber",
        "complaintCategory",
        "complaintDescription",
        "severityLevel",
        "riskScore",
        "complaintSummary",
    ],
}

EXTRACTION_PROMPT = """Extract pharmaceutical complaint fields from this document into JSON.
Use "" for unknown fields (do not invent). Dates → YYYY-MM-DD.
Infer dosageForm, category (discoloration→Product Quality), countryCode (India→+91).
Include severityLevel, riskScore 1-100, recommendedActions, rootCauseHypothesis, capaRecommendation, complaintSummary.
"""

_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not GOOGLE_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY is not configured")
        _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client


def _guess_mime(filename: Optional[str], content: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf") or content[:4] == b"%PDF":
        return "application/pdf"
    if name.endswith(".png"):
        return "image/png"
    if name.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if name.endswith(".webp"):
        return "image/webp"
    if name.endswith((".txt", ".eml", ".msg", ".md")):
        return "text/plain"
    return "application/octet-stream"


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_complaint(raw: dict) -> dict:
    actions = raw.get("recommendedActions") or []
    if isinstance(actions, str):
        actions = [actions]
    if not isinstance(actions, list):
        actions = []

    risk = raw.get("riskScore")
    try:
        risk_score = float(risk) if risk is not None and risk != "" else 0.0
    except (TypeError, ValueError):
        risk_score = 0.0

    data = {
        "productName": _as_str(raw.get("productName")),
        "productStrength": _as_str(raw.get("productStrength")),
        "dosageForm": _as_str(raw.get("dosageForm")),
        "batchNumber": _as_str(raw.get("batchNumber")),
        "lotNumber": _as_str(raw.get("lotNumber")),
        "manufacturingDate": _as_str(raw.get("manufacturingDate")),
        "expiryDate": _as_str(raw.get("expiryDate")),
        "complaintCategory": _as_str(raw.get("complaintCategory")),
        "complaintDescription": _as_str(raw.get("complaintDescription")),
        "complainantName": _as_str(raw.get("complainantName")),
        "complainantContact": _as_str(raw.get("complainantContact")),
        "complainantPhone": _as_str(raw.get("complainantPhone")),
        "complainantEmail": _as_str(raw.get("complainantEmail")),
        "countryCode": _as_str(raw.get("countryCode")),
        "dateOfComplaint": _as_str(raw.get("dateOfComplaint")),
        "dateOfIncident": _as_str(raw.get("dateOfIncident")),
        "severityLevel": normalize_severity_level(
            raw.get("severityLevel"), risk_score
        ),
        "riskScore": risk_score,
        "recommendedActions": [str(a).strip() for a in actions if str(a).strip()],
        "rootCauseHypothesis": _as_str(raw.get("rootCauseHypothesis")),
        "capaRecommendation": _as_str(raw.get("capaRecommendation")),
        "complaintSummary": _as_str(raw.get("complaintSummary")),
        "status": "logged",
    }

    if not data["complainantEmail"] and "@" in data["complainantContact"]:
        data["complainantEmail"] = data["complainantContact"]

    phone = data["complainantPhone"]
    if phone.startswith("+"):
        match = re.match(r"^(\+\d{1,4})\s*(.*)$", phone)
        if match:
            data["countryCode"] = match.group(1)
            data["complainantPhone"] = match.group(2).strip()

    return data


def _parse_json_response(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0))
        raise


def _document_model_chain() -> list[str]:
    """Primary DOCUMENT_MODEL first, then configured Gemini fallbacks (deduped)."""
    chain: list[str] = []
    for model in [DOCUMENT_MODEL, *DOCUMENT_FALLBACK_MODELS]:
        m = (model or "").strip()
        if m and m not in chain:
            chain.append(m)
    return chain


def _generate_with_model(client: genai.Client, model: str, contents: list) -> dict:
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": COMPLAINT_JSON_SCHEMA,
            "temperature": 0,
            "max_output_tokens": 2048,
        },
    )
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, dict):
        raw = parsed
    else:
        raw = _parse_json_response(getattr(response, "text", "") or "")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"{model} returned empty extraction JSON")
    return raw


def extract_complaint_from_document(
    content: bytes,
    filename: Optional[str] = None,
) -> dict:
    """Send the raw file to Gemini (with model fallbacks) and return complaint fields."""
    if not content:
        raise ValueError("Empty document content")

    mime = _guess_mime(filename, content)
    client = _get_client()
    models = _document_model_chain()
    if not models:
        raise RuntimeError("No DOCUMENT_MODEL / DOCUMENT_FALLBACK_MODELS configured")

    use_files_api = len(content) > 15 * 1024 * 1024
    uploaded = None
    errors: list[str] = []

    try:
        if mime.startswith("text/"):
            text_body = content.decode("utf-8", errors="replace")
            contents = [
                EXTRACTION_PROMPT,
                f"DOCUMENT ({filename or 'text'}):\n{text_body}",
            ]
        elif use_files_api:
            uploaded = client.files.upload(
                file=BytesIO(content),
                config=types.UploadFileConfig(
                    mime_type=mime,
                    display_name=filename or "complaint-document",
                ),
            )
            contents = [EXTRACTION_PROMPT, uploaded]
        else:
            contents = [
                EXTRACTION_PROMPT,
                types.Part.from_bytes(data=content, mime_type=mime),
            ]

        for model in models:
            try:
                raw = _generate_with_model(client, model, contents)
                result = _normalize_complaint(raw)
                result["_extractionModel"] = model
                print(f"[document_extractor] success with {model}")
                return result
            except Exception as exc:
                msg = f"{model}: {exc}"
                errors.append(msg)
                print(f"[document_extractor] fallback after failure — {msg}")
                continue

        raise RuntimeError(
            "All Gemini document models failed. " + " | ".join(errors[-5:])
        )
    finally:
        if uploaded is not None and getattr(uploaded, "name", None):
            try:
                client.files.delete(name=uploaded.name)
            except Exception:
                pass
