import json
import re
from typing import Optional, List, Any
from langchain_core.tools import tool


def _s(value: Any) -> str:
    """Coerce tool args to string; treat null/None as empty."""
    if value is None:
        return ""
    return str(value).strip()


def _f(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_phone_and_country_code(phone: Any, contact: Any, country_code: Any) -> tuple[str, str]:
    """Parse phone number and country code if phone or contact starts with +country_code."""
    phone_val = _s(phone)
    contact_val = _s(contact)
    code_val = _s(country_code)

    target = phone_val if phone_val else (contact_val if "@" not in contact_val else "")

    if target and target.startswith("+"):
        match = re.match(r"^(\+\d{1,4})\s*(.*)$", target)
        if match:
            extracted_code, rest_phone = match.groups()
            code_val = extracted_code
            phone_val = rest_phone

    return phone_val, code_val


@tool
def log_complaint(
    product_name: Optional[str] = None,
    product_strength: Optional[str] = None,
    dosage_form: Optional[str] = None,
    batch_number: Optional[str] = None,
    lot_number: Optional[str] = None,
    manufacturing_date: Optional[str] = None,
    expiry_date: Optional[str] = None,
    complaint_category: Optional[str] = None,
    complaint_description: Optional[str] = None,
    complainant_name: Optional[str] = None,
    complainant_contact: Optional[str] = None,
    complainant_phone: Optional[str] = None,
    complainant_email: Optional[str] = None,
    country_code: Optional[str] = None,
    date_of_complaint: Optional[str] = None,
    date_of_incident: Optional[str] = None,
    severity_level: Optional[str] = None,
    risk_score: Optional[float] = None,
    recommended_actions: Optional[List[str]] = None,
    root_cause_hypothesis: Optional[str] = None,
    capa_recommendation: Optional[str] = None,
    complaint_summary: Optional[str] = None,
) -> str:
    """Log a new customer complaint by extracting details from the user's natural language description.

    ALWAYS use this tool first when the user pastes/describes a new complaint narrative.
    Extract EVERY field present in the text before asking for anything missing.
    For unknown fields: OMIT them or pass an empty string "". NEVER pass null.
    Convert natural dates (e.g. 11 September 2026 → 2026-09-11, July 2028 → 2028-07-31).
    Infer dosage form from product wording (Tablets/Capsules/etc.).
    Infer category (discoloration/spots → Product Quality).
    Infer country_code from location (India → +91).

    Args:
        product_name: Name of the pharmaceutical product (e.g., "Amoxicillin Capsules")
        product_strength: Strength/dosage of the product (e.g., "500mg")
        dosage_form: Form of the product (e.g., "Capsules", "Tablets", "Injection")
        batch_number: Batch/lot identifier for the product
        lot_number: Additional lot tracking number if available (use "" if unknown)
        manufacturing_date: Date the batch was manufactured (YYYY-MM-DD format)
        expiry_date: Expiration date of the batch (YYYY-MM-DD format)
        complaint_category: Category of complaint (Product Quality, Packaging Defect, Adverse Event, Potency/Efficacy, Contamination, Stability, Documentation)
        complaint_description: Detailed description of the complaint
        complainant_name: Name of the person filing the complaint
        complainant_contact: Combined contact information string
        complainant_phone: Phone number of the complainant (use "" if unknown — never null)
        complainant_email: Email address of the complainant
        country_code: Country phone code (e.g., "+1", "+44", "+91")
        date_of_complaint: Date the complaint was received (YYYY-MM-DD format)
        date_of_incident: Date the issue was observed/occurred (YYYY-MM-DD format)
        severity_level: Risk severity classification (Critical, Major, or Minor)
        risk_score: Numerical risk score from 1-100
        recommended_actions: List of recommended actions to take
        root_cause_hypothesis: Preliminary root cause analysis
        capa_recommendation: Corrective and Preventive Action recommendation
        complaint_summary: Brief AI-generated summary of the complaint

    Returns:
        JSON string of the complaint data that was logged.
    """
    phone, code = _parse_phone_and_country_code(
        complainant_phone, complainant_contact, country_code
    )

    complaint_data = {
        "productName": _s(product_name),
        "productStrength": _s(product_strength),
        "dosageForm": _s(dosage_form),
        "batchNumber": _s(batch_number),
        "lotNumber": _s(lot_number),
        "manufacturingDate": _s(manufacturing_date),
        "expiryDate": _s(expiry_date),
        "complaintCategory": _s(complaint_category),
        "complaintDescription": _s(complaint_description),
        "complainantName": _s(complainant_name),
        "complainantContact": _s(complainant_contact),
        "complainantPhone": phone,
        "complainantEmail": _s(complainant_email),
        "countryCode": code,
        "dateOfComplaint": _s(date_of_complaint),
        "dateOfIncident": _s(date_of_incident),
        "severityLevel": _s(severity_level),
        "riskScore": _f(risk_score),
        "recommendedActions": recommended_actions or [],
        "rootCauseHypothesis": _s(root_cause_hypothesis),
        "capaRecommendation": _s(capa_recommendation),
        "complaintSummary": _s(complaint_summary),
        "status": "logged",
    }
    return json.dumps(complaint_data)


@tool
def edit_complaint(
    product_name: Optional[str] = None,
    product_strength: Optional[str] = None,
    dosage_form: Optional[str] = None,
    batch_number: Optional[str] = None,
    lot_number: Optional[str] = None,
    manufacturing_date: Optional[str] = None,
    expiry_date: Optional[str] = None,
    complaint_category: Optional[str] = None,
    complaint_description: Optional[str] = None,
    complainant_name: Optional[str] = None,
    complainant_contact: Optional[str] = None,
    complainant_phone: Optional[str] = None,
    complainant_email: Optional[str] = None,
    country_code: Optional[str] = None,
    date_of_complaint: Optional[str] = None,
    date_of_incident: Optional[str] = None,
    severity_level: Optional[str] = None,
    risk_score: Optional[float] = None,
    recommended_actions: Optional[List[str]] = None,
    root_cause_hypothesis: Optional[str] = None,
    capa_recommendation: Optional[str] = None,
    complaint_summary: Optional[str] = None,
) -> str:
    """Edit an existing complaint by updating ONLY the fields the user provided.

    Do NOT pass the full existing complaint as JSON. Only pass changed fields.
    Never pass null — omit unknown fields or use "".
    The system merges these updates into the current complaint record automatically.

    Returns:
        JSON string of ONLY the changed fields (partial update).
    """
    raw = {
        "productName": product_name,
        "productStrength": product_strength,
        "dosageForm": dosage_form,
        "batchNumber": batch_number,
        "lotNumber": lot_number,
        "manufacturingDate": manufacturing_date,
        "expiryDate": expiry_date,
        "complaintCategory": complaint_category,
        "complaintDescription": complaint_description,
        "complainantName": complainant_name,
        "complainantContact": complainant_contact,
        "complainantPhone": complainant_phone,
        "complainantEmail": complainant_email,
        "countryCode": country_code,
        "dateOfComplaint": date_of_complaint,
        "dateOfIncident": date_of_incident,
        "severityLevel": severity_level,
        "riskScore": risk_score,
        "recommendedActions": recommended_actions,
        "rootCauseHypothesis": root_cause_hypothesis,
        "capaRecommendation": capa_recommendation,
        "complaintSummary": complaint_summary,
    }

    updates: dict[str, Any] = {}
    for key, value in raw.items():
        if value is None:
            continue
        if key == "recommendedActions":
            updates[key] = value if isinstance(value, list) else []
        elif key == "riskScore":
            updates[key] = _f(value)
        else:
            updates[key] = _s(value)

    if any(k in updates for k in ("complainantPhone", "countryCode", "complainantContact")):
        phone, code = _parse_phone_and_country_code(
            updates.get("complainantPhone", ""),
            updates.get("complainantContact", ""),
            updates.get("countryCode", ""),
        )
        if "complainantPhone" in updates or phone:
            updates["complainantPhone"] = phone
        if "countryCode" in updates or code:
            updates["countryCode"] = code

    return json.dumps(updates)


@tool
def extract_document(
    product_name: Optional[str] = None,
    product_strength: Optional[str] = None,
    dosage_form: Optional[str] = None,
    batch_number: Optional[str] = None,
    lot_number: Optional[str] = None,
    manufacturing_date: Optional[str] = None,
    expiry_date: Optional[str] = None,
    complaint_category: Optional[str] = None,
    complaint_description: Optional[str] = None,
    complainant_name: Optional[str] = None,
    complainant_contact: Optional[str] = None,
    complainant_phone: Optional[str] = None,
    complainant_email: Optional[str] = None,
    country_code: Optional[str] = None,
    date_of_complaint: Optional[str] = None,
    date_of_incident: Optional[str] = None,
    severity_level: Optional[str] = None,
    risk_score: Optional[float] = None,
    recommended_actions: Optional[List[str]] = None,
    root_cause_hypothesis: Optional[str] = None,
    capa_recommendation: Optional[str] = None,
    complaint_summary: Optional[str] = None,
) -> str:
    """Extract complaint details from an uploaded document (PDF, email, or other text).

    Parse the document and populate all available fields. Never pass null for missing
    fields — omit them or use "". Do NOT echo back the raw document text.
    """
    phone, code = _parse_phone_and_country_code(
        complainant_phone, complainant_contact, country_code
    )
    complaint_data = {
        "productName": _s(product_name),
        "productStrength": _s(product_strength),
        "dosageForm": _s(dosage_form),
        "batchNumber": _s(batch_number),
        "lotNumber": _s(lot_number),
        "manufacturingDate": _s(manufacturing_date),
        "expiryDate": _s(expiry_date),
        "complaintCategory": _s(complaint_category),
        "complaintDescription": _s(complaint_description),
        "complainantName": _s(complainant_name),
        "complainantContact": _s(complainant_contact),
        "complainantPhone": phone,
        "complainantEmail": _s(complainant_email),
        "countryCode": code,
        "dateOfComplaint": _s(date_of_complaint),
        "dateOfIncident": _s(date_of_incident),
        "severityLevel": _s(severity_level),
        "riskScore": _f(risk_score),
        "recommendedActions": recommended_actions or [],
        "rootCauseHypothesis": _s(root_cause_hypothesis),
        "capaRecommendation": _s(capa_recommendation),
        "complaintSummary": _s(complaint_summary),
        "status": "logged",
    }
    return json.dumps(complaint_data)


@tool
def assess_risk(
    severity_level: Optional[str] = None,
    risk_score: Optional[float] = None,
    recommended_actions: Optional[List[str]] = None,
    root_cause_hypothesis: Optional[str] = None,
    capa_recommendation: Optional[str] = None,
) -> str:
    """Generate or update a risk assessment for the current complaint.

    Do NOT pass complaint_data JSON. Only pass the assessment fields below.
    Never pass null — use "" or omit. The system merges into the current record.
    """
    return json.dumps({
        "severityLevel": _s(severity_level),
        "riskScore": _f(risk_score),
        "recommendedActions": recommended_actions or [],
        "rootCauseHypothesis": _s(root_cause_hypothesis),
        "capaRecommendation": _s(capa_recommendation),
    })


@tool
def check_completeness() -> str:
    """Check completeness of the CURRENT complaint in context.

    Do NOT pass complaint_data JSON. Call with no arguments.
    """
    return json.dumps({"action": "check_completeness"})


@tool
def request_missing_info(
    missing_fields: Optional[List[str]] = None,
    prompt: Optional[str] = None,
) -> str:
    """Request missing information from the user via an interactive OpenUI form card.

    Args:
        missing_fields: List of missing field keys (e.g. ["complainantEmail", "complainantPhone"])
        prompt: Explanation of what fields are needed
    """
    fields = [ _s(f) for f in (missing_fields or []) if _s(f) ]
    prompt_text = _s(prompt) or "Please provide the missing complaint details to complete the record:"
    fields_str = ",".join(fields)
    openui_markup = (
        f'<MissingInfoForm title="Provide Missing Details" '
        f'fields="{fields_str}" prompt="{prompt_text}" />'
    )
    return json.dumps({
        "missing_fields": fields,
        "prompt": prompt_text,
        "openui_markup": openui_markup,
    })


ALL_TOOLS = [
    log_complaint,
    edit_complaint,
    extract_document,
    assess_risk,
    check_completeness,
    request_missing_info,
]
