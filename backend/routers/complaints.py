from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from models.database import get_db
from models.complaint import Complaint
from schemas.complaint import ComplaintData, SubmitResponse, DuplicateDetails
from services.duplicate_detector import (
    check_for_duplicates,
    generate_and_store_embedding,
    EMBEDDING_MODEL,
)
from services.complaint_sanitize import sanitize_complaint_for_db

router = APIRouter(prefix="/api", tags=["complaints"])


@router.get("/complaints", response_model=List[ComplaintData])
async def list_complaints(db: Session = Depends(get_db)):
    """List all complaints ordered by most recent first."""
    complaints = db.query(Complaint).order_by(Complaint.created_at.desc()).all()
    return [ComplaintData(**c.to_dict()) for c in complaints]


@router.get("/complaints/{complaint_id}", response_model=ComplaintData)
async def get_complaint(complaint_id: str, db: Session = Depends(get_db)):
    """Get a single complaint by ID."""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return ComplaintData(**complaint.to_dict())


@router.delete("/complaints/{complaint_id}")
async def delete_complaint(complaint_id: str, db: Session = Depends(get_db)):
    """Delete a complaint by ID."""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    db.delete(complaint)
    db.commit()
    return {"message": "Complaint deleted successfully"}


@router.post("/complaints/submit", response_model=SubmitResponse)
async def submit_complaint(
    data: ComplaintData,
    force: bool = Query(False, description="Force submit even if duplicate detected"),
    db: Session = Depends(get_db),
):
    """Submit a complaint to the database with duplicate detection.
    
    Pipeline:
    1. Convert complaint to embedding via Google Gemini gemini-embedding-2
    2. Compute cosine similarity against all existing complaints
    3. If similar candidate found (>=0.82), verify with Groq LLM
    4. If confirmed duplicate → return 409 with details
    5. If clean → save/update complaint with status="submitted"
    """
    complaint_dict = sanitize_complaint_for_db(data.model_dump())
    new_embedding: list = []

    # Skip duplicate detection if force flag is set
    if not force:
        dup_result = check_for_duplicates(
            db,
            complaint_dict,
            exclude_id=data.id,
        )
        new_embedding = dup_result.get("new_embedding") or []

        if dup_result["duplicate_detected"]:
            matched = dup_result.get("matched_complaint") or {}
            return SubmitResponse(
                success=False,
                message="Submission rejected: duplicate complaint detected by embedding retrieval + LLM verification.",
                complaint=data,
                duplicate_detected=True,
                duplicate_details=DuplicateDetails(
                    matched_complaint_id=matched.get("id", ""),
                    matched_product=matched.get("productName", ""),
                    matched_batch=matched.get("batchNumber", ""),
                    similarity_score=dup_result.get("similarity_score", 0.0),
                    confidence=dup_result.get("confidence", 0.0),
                    explanation=dup_result.get("explanation", ""),
                ),
            )

    # No duplicate — save the complaint
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
    }

    # Find existing or create new
    complaint = None
    if data.id:
        complaint = db.query(Complaint).filter(Complaint.id == data.id).first()

    if not complaint:
        complaint = Complaint()
        db.add(complaint)

    for api_field, db_field in field_mapping.items():
        val = complaint_dict.get(api_field)
        if val is not None:
            setattr(complaint, db_field, val)

    complaint.status = "submitted"

    # Persist Gemini embedding into pgvector column
    if new_embedding:
        from datetime import datetime
        complaint.embedding = new_embedding
        complaint.embedding_model = EMBEDDING_MODEL
        complaint.embedding_updated_at = datetime.utcnow()
    else:
        try:
            generate_and_store_embedding(db, complaint, complaint_dict, commit=False)
        except Exception as emb_err:
            print(f"Embedding persistence warning: {emb_err}")

    db.commit()
    db.refresh(complaint)

    saved_data = ComplaintData(**complaint.to_dict())

    return SubmitResponse(
        success=True,
        message="Complaint submitted successfully. Embedding stored and no duplicates detected.",
        complaint=saved_data,
        duplicate_detected=False,
        duplicate_details=None,
    )

