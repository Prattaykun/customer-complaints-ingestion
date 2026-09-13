import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from models.database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Product Information
    product_name = Column(String(255), nullable=True)
    product_strength = Column(String(100), nullable=True)
    dosage_form = Column(String(100), nullable=True)

    # Batch Details
    batch_number = Column(String(100), nullable=True)
    lot_number = Column(String(100), nullable=True)
    manufacturing_date = Column(String(50), nullable=True)
    expiry_date = Column(String(50), nullable=True)

    # Complaint Details
    complaint_category = Column(String(100), nullable=True)
    complaint_description = Column(Text, nullable=True)
    complainant_name = Column(String(255), nullable=True)
    complainant_contact = Column(String(255), nullable=True)
    complainant_phone = Column(String(100), nullable=True)
    complainant_email = Column(String(255), nullable=True)
    country_code = Column(String(20), nullable=True)
    date_of_complaint = Column(String(50), nullable=True)
    date_of_incident = Column(String(50), nullable=True)

    # AI Risk Assessment
    severity_level = Column(String(50), nullable=True)  # Critical / Major / Minor
    risk_score = Column(Float, nullable=True)
    recommended_actions = Column(JSON, nullable=True, default=list)
    root_cause_hypothesis = Column(Text, nullable=True)
    capa_recommendation = Column(Text, nullable=True)
    complaint_summary = Column(Text, nullable=True)
    completeness_score = Column(Float, nullable=True)

    # Status and Metadata
    status = Column(String(50), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert complaint to a dictionary for API responses."""
        return {
            "id": str(self.id),
            "productName": self.product_name or "",
            "productStrength": self.product_strength or "",
            "dosageForm": self.dosage_form or "",
            "batchNumber": self.batch_number or "",
            "lotNumber": self.lot_number or "",
            "manufacturingDate": self.manufacturing_date or "",
            "expiryDate": self.expiry_date or "",
            "complaintCategory": self.complaint_category or "",
            "complaintDescription": self.complaint_description or "",
            "complainantName": self.complainant_name or "",
            "complainantContact": self.complainant_contact or "",
            "complainantPhone": self.complainant_phone or "",
            "complainantEmail": self.complainant_email or "",
            "countryCode": self.country_code or "",
            "dateOfComplaint": self.date_of_complaint or "",
            "dateOfIncident": self.date_of_incident or "",
            "severityLevel": self.severity_level or "",
            "riskScore": self.risk_score or 0,
            "recommendedActions": self.recommended_actions or [],
            "rootCauseHypothesis": self.root_cause_hypothesis or "",
            "capaRecommendation": self.capa_recommendation or "",
            "complaintSummary": self.complaint_summary or "",
            "completenessScore": self.completeness_score or 0,
            "status": self.status or "draft",
            "createdAt": self.created_at.isoformat() if self.created_at else "",
            "updatedAt": self.updated_at.isoformat() if self.updated_at else "",
        }
