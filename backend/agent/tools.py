import json
from typing import Optional, List
from langchain_core.tools import tool


@tool
def log_complaint(
    product_name: str = "",
    product_strength: str = "",
    dosage_form: str = "",
    batch_number: str = "",
    lot_number: str = "",
    manufacturing_date: str = "",
    expiry_date: str = "",
    complaint_category: str = "",
    complaint_description: str = "",
    complainant_name: str = "",
    complainant_contact: str = "",
    complainant_phone: str = "",
    complainant_email: str = "",
    country_code: str = "",
    date_of_complaint: str = "",
    date_of_incident: str = "",
    severity_level: str = "",
    risk_score: float = 0,
    recommended_actions: Optional[List[str]] = None,
    root_cause_hypothesis: str = "",
    capa_recommendation: str = "",
    complaint_summary: str = "",
) -> str:
    """Log a new customer complaint by extracting details from the user's natural language description.
    
    Use this tool when the user describes a new pharmaceutical complaint. Extract ALL
    relevant product information, batch details, complaint details, and generate a
    risk assessment including severity level, risk score, recommended actions,
    root cause hypothesis, and CAPA recommendation.
    
    Args:
        product_name: Name of the pharmaceutical product (e.g., "Amoxicillin Capsules")
        product_strength: Strength/dosage of the product (e.g., "500mg")
        dosage_form: Form of the product (e.g., "Capsules", "Tablets", "Injection")
        batch_number: Batch/lot identifier for the product
        lot_number: Additional lot tracking number if available
        manufacturing_date: Date the batch was manufactured (YYYY-MM-DD format)
        expiry_date: Expiration date of the batch (YYYY-MM-DD format)
        complaint_category: Category of complaint (Product Quality, Packaging Defect, Adverse Event, Potency/Efficacy, Contamination, Stability, Documentation)
        complaint_description: Detailed description of the complaint
        complainant_name: Name of the person filing the complaint
        complainant_contact: Combined contact information string
        complainant_phone: Phone number of the complainant
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
    complaint_data = {
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
        "recommendedActions": recommended_actions or [],
        "rootCauseHypothesis": root_cause_hypothesis,
        "capaRecommendation": capa_recommendation,
        "complaintSummary": complaint_summary,
        "status": "logged",
    }
    return json.dumps(complaint_data)


@tool
def edit_complaint(
    existing_complaint: str = "{}",
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
    """Edit an existing customer complaint by updating only the specified fields.
    
    Use this tool when the user wants to modify specific fields of an existing complaint.
    Only update the fields that are explicitly provided — preserve all other existing data.
    Pass the current complaint data as existing_complaint JSON string so unchanged fields
    are preserved.
    
    Args:
        existing_complaint: JSON string of the current complaint data to preserve unchanged fields
        product_name: Updated product name (None = keep existing)
        product_strength: Updated strength (None = keep existing)
        dosage_form: Updated dosage form (None = keep existing)
        batch_number: Updated batch number (None = keep existing)
        lot_number: Updated lot number (None = keep existing)
        manufacturing_date: Updated manufacturing date (None = keep existing)
        expiry_date: Updated expiry date (None = keep existing)
        complaint_category: Updated complaint category (None = keep existing)
        complaint_description: Updated description (None = keep existing)
        complainant_name: Updated complainant name (None = keep existing)
        complainant_contact: Updated contact info (None = keep existing)
        complainant_phone: Updated phone number (None = keep existing)
        complainant_email: Updated email address (None = keep existing)
        country_code: Updated country code (None = keep existing)
        date_of_complaint: Updated complaint date (None = keep existing)
        date_of_incident: Updated incident date (None = keep existing)
        severity_level: Updated severity (None = keep existing)
        risk_score: Updated risk score (None = keep existing)
        recommended_actions: Updated actions list (None = keep existing)
        root_cause_hypothesis: Updated root cause (None = keep existing)
        capa_recommendation: Updated CAPA (None = keep existing)
        complaint_summary: Updated summary (None = keep existing)
    
    Returns:
        JSON string of the updated complaint data with all fields (changed + preserved).
    """
    try:
        existing = json.loads(existing_complaint)
    except (json.JSONDecodeError, TypeError):
        existing = {}

    field_mapping = {
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

    for key, value in field_mapping.items():
        if value is not None:
            existing[key] = value

    return json.dumps(existing)


@tool
def extract_document(
    product_name: str = "",
    product_strength: str = "",
    dosage_form: str = "",
    batch_number: str = "",
    lot_number: str = "",
    manufacturing_date: str = "",
    expiry_date: str = "",
    complaint_category: str = "",
    complaint_description: str = "",
    complainant_name: str = "",
    complainant_contact: str = "",
    complainant_phone: str = "",
    complainant_email: str = "",
    country_code: str = "",
    date_of_complaint: str = "",
    date_of_incident: str = "",
    severity_level: str = "",
    risk_score: float = 0,
    recommended_actions: Optional[List[str]] = None,
    root_cause_hypothesis: str = "",
    capa_recommendation: str = "",
    complaint_summary: str = "",
) -> str:
    """Extract complaint details from an uploaded document (PDF, email, or other text).
    
    Use this tool when the user uploads a document containing pharmaceutical complaint
    or manufacturing data. Parse the document text to extract all relevant fields and
    generate a risk assessment. Do NOT echo back the raw document text.
    
    Args:
        product_name: Extracted product name
        product_strength: Extracted product strength
        dosage_form: Extracted dosage form
        batch_number: Extracted batch number
        lot_number: Extracted lot number
        manufacturing_date: Extracted manufacturing date
        expiry_date: Extracted expiry date
        complaint_category: Determined complaint category
        complaint_description: Extracted or synthesized complaint description
        complainant_name: Extracted complainant name
        complainant_contact: Extracted contact information
        complainant_phone: Extracted phone number
        complainant_email: Extracted email address
        country_code: Extracted country phone code (e.g. "+1")
        date_of_complaint: Extracted complaint date
        date_of_incident: Extracted incident date
        severity_level: AI-determined severity (Critical/Major/Minor)
        risk_score: AI-determined risk score (1-100)
        recommended_actions: AI-recommended actions list
        root_cause_hypothesis: AI-generated root cause hypothesis
        capa_recommendation: AI-generated CAPA recommendation
        complaint_summary: AI-generated summary of the document and complaint
    
    Returns:
        JSON string of the extracted and assessed complaint data.
    """
    complaint_data = {
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
        "recommendedActions": recommended_actions or [],
        "rootCauseHypothesis": root_cause_hypothesis,
        "capaRecommendation": capa_recommendation,
        "complaintSummary": complaint_summary,
        "status": "logged",
    }
    return json.dumps(complaint_data)


@tool
def assess_risk(
    complaint_data: str,
    severity_level: str = "",
    risk_score: float = 0,
    recommended_actions: Optional[List[str]] = None,
    root_cause_hypothesis: str = "",
    capa_recommendation: str = "",
) -> str:
    """Generate or update a risk assessment for an existing complaint.
    
    Use this tool to evaluate the risk level of a complaint and provide
    severity classification, risk scoring, recommended actions, root cause
    analysis, and CAPA recommendations based on pharmaceutical QMS standards.
    
    Args:
        complaint_data: JSON string of the current complaint data to assess
        severity_level: Determined severity level (Critical, Major, or Minor)
        risk_score: Numerical risk score from 1-100
        recommended_actions: List of recommended investigation/remediation actions
        root_cause_hypothesis: Preliminary root cause analysis based on complaint details
        capa_recommendation: Corrective and Preventive Action recommendation
    
    Returns:
        JSON string of the complaint data with updated risk assessment fields.
    """
    try:
        existing = json.loads(complaint_data)
    except (json.JSONDecodeError, TypeError):
        existing = {}

    existing["severityLevel"] = severity_level
    existing["riskScore"] = risk_score
    existing["recommendedActions"] = recommended_actions or []
    existing["rootCauseHypothesis"] = root_cause_hypothesis
    existing["capaRecommendation"] = capa_recommendation

    return json.dumps(existing)


@tool
def check_completeness(complaint_data: str) -> str:
    """Check the completeness of a complaint record against QMS requirements.
    
    Evaluates which required fields are filled and calculates a completeness
    percentage. Returns a score and list of missing fields to help ensure
    the complaint record meets quality management standards.
    
    Args:
        complaint_data: JSON string of the current complaint data to evaluate
    
    Returns:
        JSON string with completeness_score (0-100) and missing_fields list.
    """
    try:
        data = json.loads(complaint_data)
    except (json.JSONDecodeError, TypeError):
        data = {}

    required_fields = {
        "productName": "Product Name",
        "productStrength": "Product Strength",
        "dosageForm": "Dosage Form",
        "batchNumber": "Batch Number",
        "manufacturingDate": "Manufacturing Date",
        "expiryDate": "Expiry Date",
        "complaintCategory": "Complaint Category",
        "complaintDescription": "Complaint Description",
        "complainantName": "Complainant Name",
        "complainantEmail": "Complainant Email",
        "complainantPhone": "Complainant Phone",
        "countryCode": "Country Code",
        "dateOfComplaint": "Date of Complaint",
        "severityLevel": "Severity Level",
        "riskScore": "Risk Score",
    }

    filled = 0
    missing = []
    for field_key, field_label in required_fields.items():
        value = data.get(field_key, "")
        if value and str(value).strip() and value != 0:
            filled += 1
        else:
            missing.append(field_label)

    score = round((filled / len(required_fields)) * 100, 1)

    result = {
        "completenessScore": score,
        "missingFields": missing,
        "totalFields": len(required_fields),
        "filledFields": filled,
    }
    return json.dumps(result)


@tool
def request_missing_info(
    missing_fields: List[str],
    prompt: str = "Please provide the missing complaint details to complete the record:"
) -> str:
    """Request missing information from the user by generating an interactive OpenUI form card in chat.
    
    Use this tool whenever required or key fields (such as complainant_email, complainant_phone,
    country_code, batch_number, etc.) are missing during document extraction or complaint logging.
    
    Args:
        missing_fields: List of missing field keys (e.g. ["complainantEmail", "complainantPhone", "countryCode"])
        prompt: Explanation of what fields are needed
    
    Returns:
        JSON string containing the OpenUI component markup and fields list.
    """
    fields_str = ",".join(missing_fields)
    openui_markup = f'<MissingInfoForm title="Provide Missing Details" fields="{fields_str}" prompt="{prompt}" />'
    result = {
        "missing_fields": missing_fields,
        "prompt": prompt,
        "openui_markup": openui_markup,
    }
    return json.dumps(result)


# Export all tools for use in the graph
ALL_TOOLS = [log_complaint, edit_complaint, extract_document, assess_risk, check_completeness, request_missing_info]
