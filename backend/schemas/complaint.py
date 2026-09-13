from pydantic import BaseModel, Field
from typing import Optional, List


class ComplaintData(BaseModel):
    """Schema for complaint data exchanged between frontend and backend."""
    id: Optional[str] = None
    productName: Optional[str] = ""
    productStrength: Optional[str] = ""
    dosageForm: Optional[str] = ""
    batchNumber: Optional[str] = ""
    lotNumber: Optional[str] = ""
    manufacturingDate: Optional[str] = ""
    expiryDate: Optional[str] = ""
    complaintCategory: Optional[str] = ""
    complaintDescription: Optional[str] = ""
    complainantName: Optional[str] = ""
    complainantContact: Optional[str] = ""
    complainantPhone: Optional[str] = ""
    complainantEmail: Optional[str] = ""
    countryCode: Optional[str] = ""
    dateOfComplaint: Optional[str] = ""
    dateOfIncident: Optional[str] = ""
    severityLevel: Optional[str] = ""
    riskScore: Optional[float] = 0
    recommendedActions: Optional[List[str]] = []
    rootCauseHypothesis: Optional[str] = ""
    capaRecommendation: Optional[str] = ""
    complaintSummary: Optional[str] = ""
    completenessScore: Optional[float] = 0
    status: Optional[str] = "draft"


class ChatRequest(BaseModel):
    """Schema for chat API request."""
    message: str
    complaint_id: Optional[str] = None
    complaint_data: Optional[ComplaintData] = None
    chat_history: Optional[List[dict]] = []


class ChatResponse(BaseModel):
    """Schema for chat API response."""
    response: str
    complaint_data: Optional[ComplaintData] = None
    tool_calls: Optional[List[dict]] = []


class UploadResponse(BaseModel):
    """Schema for document upload response."""
    response: str
    complaint_data: Optional[ComplaintData] = None
    extracted_text: Optional[str] = ""
    tool_calls: Optional[List[dict]] = []
