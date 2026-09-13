import traceback
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
import pypdf
import io

from schemas.complaint import UploadResponse, ComplaintData
from agent.graph import run_agent
from models.database import get_db
from models.complaint import Complaint

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a document (PDF, text, email) for AI-powered complaint extraction.
    
    The endpoint:
    1. Reads the uploaded file and extracts text content
    2. Passes the text to the LangGraph agent with extraction instructions
    3. Returns extracted complaint data and AI risk assessment
    """
    try:
        # Read file content
        content = await file.read()
        extracted_text = ""

        # Extract text based on file type
        if file.filename and file.filename.lower().endswith(".pdf"):
            extracted_text = _extract_pdf_text(content)
        elif file.filename and file.filename.lower().endswith((".txt", ".eml", ".msg")):
            extracted_text = content.decode("utf-8", errors="replace")
        else:
            # Try to read as text for any other format
            try:
                extracted_text = content.decode("utf-8", errors="replace")
            except Exception:
                extracted_text = str(content)

        if not extracted_text.strip():
            return UploadResponse(
                response="I couldn't extract any text from the uploaded file. Please try a different file format (PDF, TXT, or email).",
                complaint_data=None,
                extracted_text="",
                tool_calls=[],
            )

        # Create a prompt for the agent to extract document data
        extraction_prompt = (
            f"I've uploaded a document for complaint extraction. "
            f"Please analyze the following document text and extract all relevant "
            f"pharmaceutical complaint details. Use the extract_document tool to "
            f"populate the complaint form and generate a risk assessment.\n\n"
            f"--- DOCUMENT CONTENT ---\n{extracted_text}\n--- END DOCUMENT ---"
        )

        # Run the agent with the extraction prompt
        result = await run_agent(
            user_message=extraction_prompt,
            complaint_data={},
            chat_history=[],
        )

        complaint_data = result.get("complaint_data", {})

        # Save to database
        if complaint_data and any(
            complaint_data.get(k) for k in ["productName", "complaintDescription", "batchNumber"]
        ):
            complaint = Complaint()
            db.add(complaint)
            
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
                if api_field in complaint_data and complaint_data[api_field] is not None:
                    setattr(complaint, db_field, complaint_data[api_field])

            db.commit()
            db.refresh(complaint)
            complaint_data["id"] = str(complaint.id)

        return UploadResponse(
            response=result.get("response", "Document processed successfully."),
            complaint_data=ComplaintData(**complaint_data) if complaint_data else None,
            extracted_text=extracted_text[:2000],  # Limit for response size
            tool_calls=result.get("tool_calls", []),
        )

    except Exception as e:
        traceback.print_exc()
        return UploadResponse(
            response=f"Error processing document: {str(e)}",
            complaint_data=None,
            extracted_text="",
            tool_calls=[],
        )


def _extract_pdf_text(content: bytes) -> str:
    """Extract text from PDF binary content using pypdf."""
    try:
        reader = pypdf.PdfReader(io.BytesIO(content))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n".join(text_parts)
    except Exception as e:
        return f"[PDF extraction error: {str(e)}]"
