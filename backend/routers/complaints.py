from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import get_db
from models.complaint import Complaint
from schemas.complaint import ComplaintData

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
