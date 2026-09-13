import json
import traceback
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from schemas.complaint import ChatRequest, ChatResponse, ComplaintData
from agent.graph import run_agent
from models.database import get_db
from models.complaint import Complaint
from services.duplicate_detector import generate_and_store_embedding
from services.complaint_sanitize import sanitize_complaint_for_db

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Process a chat message through the AI agent.
    
    The agent analyzes the user's message, determines which tools to invoke
    (log_complaint, edit_complaint, assess_risk, etc.), executes them, and
    returns both a conversational response and updated complaint data.
    """
    try:
        # Prepare existing complaint data for context
        existing_data = {}
        if request.complaint_data:
            existing_data = request.complaint_data.model_dump()
        elif request.complaint_id:
            complaint = db.query(Complaint).filter(
                Complaint.id == request.complaint_id
            ).first()
            if complaint:
                existing_data = complaint.to_dict()

        # Run the LangGraph agent
        result = await run_agent(
            user_message=request.message,
            complaint_data=existing_data,
            chat_history=request.chat_history,
        )

        # Extract complaint data from agent result
        complaint_data = result.get("complaint_data", {}) or {}
        if complaint_data:
            complaint_data = sanitize_complaint_for_db(complaint_data)

        # Prefer id from current form/state when saving
        save_id = request.complaint_id or (complaint_data.get("id") if complaint_data else None)

        # Persist if possible, but ALWAYS return updated complaint_data to the UI
        if complaint_data and any(
            complaint_data.get(k) for k in ["productName", "complaintDescription", "batchNumber"]
        ):
            try:
                complaint = _save_complaint(db, complaint_data, save_id)
                complaint_data["id"] = str(complaint.id)
            except Exception as save_err:
                traceback.print_exc()
                print(f"Chat save warning (UI still updated): {save_err}")
                try:
                    db.rollback()
                except Exception:
                    pass

        return ChatResponse(
            response=result.get("response", "I couldn't process that request. Please try again."),
            complaint_data=ComplaintData(**complaint_data) if complaint_data else None,
            tool_calls=result.get("tool_calls", []),
        )

    except Exception as e:
        traceback.print_exc()
        return ChatResponse(
            response=f"I encountered an error while processing your request: {str(e)}. Please try again.",
            complaint_data=None,
            tool_calls=[],
        )


def _save_complaint(db: Session, data: dict, complaint_id: str | None = None) -> Complaint:
    """Save or update a complaint record in the database."""
    data = sanitize_complaint_for_db(data)

    if complaint_id:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    else:
        complaint = None

    if not complaint:
        complaint = Complaint()
        db.add(complaint)

    # Map camelCase API fields to snake_case DB fields
    field_mapping = {
        "productName": "product_name",
        "productStrength": "product_strength",
        "dosageForm": "dosage_form",
        "batchNumber": "batch_number",
        "lotNumber": "lot_number",
        "manufacturingDate": "manufacturing_date",
        "expiryDate": "expiry_date",
        "complaintCategory": "complaint_category",
        "complaintDescription": "complaint_description",
        "complainantName": "complainant_name",
        "complainantContact": "complainant_contact",
        "complainantPhone": "complainant_phone",
        "complainantEmail": "complainant_email",
        "countryCode": "country_code",
        "dateOfComplaint": "date_of_complaint",
        "dateOfIncident": "date_of_incident",
        "severityLevel": "severity_level",
        "riskScore": "risk_score",
        "recommendedActions": "recommended_actions",
        "rootCauseHypothesis": "root_cause_hypothesis",
        "capaRecommendation": "capa_recommendation",
        "complaintSummary": "complaint_summary",
        "completenessScore": "completeness_score",
        "status": "status",
    }

    for api_field, db_field in field_mapping.items():
        if api_field in data and data[api_field] is not None:
            setattr(complaint, db_field, data[api_field])

    # Keep embedding in sync when complaint content changes
    try:
        generate_and_store_embedding(db, complaint, data, commit=False)
    except Exception as emb_err:
        print(f"Chat save embedding warning: {emb_err}")

    db.commit()
    db.refresh(complaint)
    return complaint
