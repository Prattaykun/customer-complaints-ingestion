import asyncio
import traceback
from fastapi import APIRouter, UploadFile, File
import pypdf
import io

from schemas.complaint import UploadResponse, ComplaintData
from agent.graph import (
    compute_completeness,
    _normalize_missing_info_form,
)
from services.document_extractor import extract_complaint_from_document

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a document for fast direct LLM extraction (no DB write on upload).

    Form fields are returned immediately; persistence + duplicate checks happen on Submit.
    """
    try:
        content = await file.read()
        filename = file.filename or "document"

        if not content:
            return UploadResponse(
                response="The uploaded file was empty. Please try another file.",
                complaint_data=None,
                extracted_text="",
                tool_calls=[],
            )

        extraction_mode = "gemini_direct"
        preview_text = ""

        try:
            # Run sync Gemini I/O off the event loop
            complaint_data = await asyncio.to_thread(
                extract_complaint_from_document, content, filename
            )
        except Exception as gemini_err:
            traceback.print_exc()
            print(f"Direct file extraction failed ({gemini_err}); trying text fallback")
            extraction_mode = "text_fallback"
            if filename.lower().endswith(".pdf") or content[:4] == b"%PDF":
                preview_text = await asyncio.to_thread(_extract_pdf_text, content)
            else:
                preview_text = content.decode("utf-8", errors="replace")

            if not preview_text.strip():
                return UploadResponse(
                    response=(
                        "I couldn't read this document. Please upload a PDF, image, "
                        "or text email, or paste the complaint text in chat."
                    ),
                    complaint_data=None,
                    extracted_text="",
                    tool_calls=[],
                )

            complaint_data = await asyncio.to_thread(
                extract_complaint_from_document,
                preview_text.encode("utf-8"),
                (filename.rsplit(".", 1)[0] + ".txt"),
            )

        completeness = compute_completeness(complaint_data)
        used_model = complaint_data.pop("_extractionModel", None)
        complaint_data.update(completeness)

        preface = (
            "I've read the uploaded document and populated the form on the left."
        )
        response_text = _normalize_missing_info_form("", completeness, complaint_data)
        if response_text.startswith("I've extracted"):
            response_text = response_text.replace(
                "I've extracted the complaint details into the form on the left.",
                preface,
                1,
            )
        else:
            response_text = f"{preface}\n\n{response_text}".strip()

        return UploadResponse(
            response=response_text,
            complaint_data=ComplaintData(**complaint_data) if complaint_data else None,
            extracted_text=(preview_text or "")[:500],
            tool_calls=[
                {
                    "tool": "extract_document_direct",
                    "result": {
                        "mode": extraction_mode,
                        "filename": filename,
                        "model": used_model,
                        "fields_filled": completeness.get("filledFields", 0),
                        "completeness": completeness.get("completenessScore", 0),
                    },
                }
            ],
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
    """Best-effort text extract for fallback only."""
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
