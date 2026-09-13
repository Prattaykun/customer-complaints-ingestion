"""
Duplicate Complaint Detection Service.

Uses a two-stage retrieval pipeline:
1. Embed new complaint text using Google Gemini `gemini-embedding-2`.
2. Compare against persisted pgvector embeddings in Neon.
3. If top candidate exceeds similarity threshold, verify with Groq LLM.
"""

import json
import traceback
from datetime import datetime
from typing import Optional

import numpy as np
from google import genai
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.orm import Session

from config import GOOGLE_API_KEY, GROQ_API_KEY, MODEL_NAME
from services.llm_factory import get_groq_llm
from models.complaint import Complaint, EMBEDDING_DIMENSIONS, _embedding_as_list

EMBEDDING_MODEL = "gemini-embedding-2"


def build_complaint_text(data: dict) -> str:
    """Convert complaint data dict into a single descriptive text for embedding."""
    parts = []
    mapping = [
        ("productName", "Product"),
        ("productStrength", "Strength"),
        ("dosageForm", "Dosage Form"),
        ("batchNumber", "Batch Number"),
        ("lotNumber", "Lot Number"),
        ("complaintCategory", "Category"),
        ("complaintDescription", "Description"),
        ("complainantName", "Complainant"),
        ("complainantEmail", "Email"),
        ("dateOfComplaint", "Date"),
        ("complaintSummary", "Summary"),
    ]
    for key, label in mapping:
        value = data.get(key)
        if value:
            parts.append(f"{label}: {value}")
    return ". ".join(parts) if parts else ""


def get_embedding(text: str) -> list[float]:
    """Generate an embedding vector using Google Gemini gemini-embedding-2."""
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is not configured")
    if not text or not text.strip():
        return []

    client = genai.Client(api_key=GOOGLE_API_KEY)
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )

    embeddings = getattr(result, "embeddings", None)
    if not embeddings:
        embedding = getattr(result, "embedding", None)
        if embedding is not None and hasattr(embedding, "values"):
            values = list(embedding.values)
        else:
            raise RuntimeError("No embeddings returned from Gemini embed_content")
    else:
        first = embeddings[0]
        values = getattr(first, "values", None)
        if values is None and isinstance(first, dict):
            values = first.get("values")
        if values is None:
            raise RuntimeError("Embedding values missing from Gemini response")
        values = list(values)

    if len(values) != EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            f"Unexpected embedding size {len(values)}; expected {EMBEDDING_DIMENSIONS}"
        )
    return values


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    va = np.array(a, dtype=np.float64)
    vb = np.array(b, dtype=np.float64)
    dot = np.dot(va, vb)
    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def generate_and_store_embedding(
    db: Session,
    complaint: Complaint,
    complaint_data: Optional[dict] = None,
    commit: bool = False,
) -> list[float]:
    """Create a Gemini embedding and persist it on the complaint row (pgvector)."""
    data = complaint_data or complaint.to_dict()
    text = build_complaint_text(data)
    if not text:
        return []

    vector = get_embedding(text)
    complaint.embedding = vector
    complaint.embedding_model = EMBEDDING_MODEL
    complaint.embedding_updated_at = datetime.utcnow()

    if commit:
        db.commit()
        db.refresh(complaint)

    return vector


def ensure_complaint_embedding(db: Session, complaint: Complaint) -> list[float]:
    """Return stored embedding, generating and saving one if missing."""
    existing = _embedding_as_list(complaint.embedding)
    if existing:
        return existing
    return generate_and_store_embedding(db, complaint, commit=True)


def reembed_all_complaints(db: Session, force: bool = True) -> dict:
    """Re-generate and store embeddings for all complaints with text content."""
    complaints = db.query(Complaint).all()
    updated = 0
    skipped = 0
    failed = 0

    for complaint in complaints:
        text = build_complaint_text(complaint.to_dict())
        if not text:
            skipped += 1
            continue

        if not force and _embedding_as_list(complaint.embedding):
            skipped += 1
            continue

        try:
            generate_and_store_embedding(db, complaint, commit=False)
            updated += 1
        except Exception:
            traceback.print_exc()
            failed += 1

    db.commit()
    return {
        "total": len(complaints),
        "updated": updated,
        "skipped": skipped,
        "failed": failed,
    }


def find_similar_complaints(
    db: Session,
    new_complaint_data: dict,
    exclude_id: Optional[str] = None,
    threshold: float = 0.82,
    top_k: int = 3,
) -> tuple[list[dict], list[float]]:
    """
    Embed the new complaint and compare against persisted pgvector embeddings.

    Returns (candidates, new_embedding).
    """
    new_text = build_complaint_text(new_complaint_data)
    if not new_text:
        return [], []

    new_embedding = get_embedding(new_text)

    query = db.query(Complaint)
    if exclude_id:
        query = query.filter(Complaint.id != exclude_id)
    existing_complaints = query.all()

    if not existing_complaints:
        return [], new_embedding

    candidates = []
    for complaint in existing_complaints:
        existing_data = complaint.to_dict()
        if not build_complaint_text(existing_data):
            continue

        try:
            existing_embedding = ensure_complaint_embedding(db, complaint)
        except Exception:
            traceback.print_exc()
            continue

        if not existing_embedding:
            continue

        sim = cosine_similarity(new_embedding, existing_embedding)
        if sim >= threshold:
            candidates.append({
                "complaint": existing_data,
                "similarity": round(sim, 4),
            })

    candidates.sort(key=lambda x: x["similarity"], reverse=True)
    return candidates[:top_k], new_embedding


DUPLICATE_CHECK_PROMPT = """You are a pharmaceutical QMS duplicate complaint detector. You are given two complaint records and must determine whether they describe the SAME complaint incident (i.e., a duplicate submission).

Consider these factors:
- Same product, batch number, and lot number → strong duplicate signal
- Very similar complaint descriptions about the same issue
- Same or similar complainant information
- Similar dates of complaint/incident

Respond with a JSON object ONLY (no markdown, no extra text):
{
  "is_duplicate": true/false,
  "confidence": 0.0-1.0,
  "explanation": "Brief explanation of why these are/aren't duplicates"
}
"""


def llm_verify_duplicate(new_complaint: dict, candidate: dict) -> dict:
    """Use Groq LLM with fallbacks for final duplicate verification."""
    llm = get_groq_llm(
        temperature=0.0,
        max_tokens=512,
    )

    new_text = build_complaint_text(new_complaint)
    candidate_text = build_complaint_text(candidate)

    user_msg = f"""NEW COMPLAINT:
{new_text}

EXISTING COMPLAINT (ID: {candidate.get('id', 'unknown')}):
{candidate_text}

Are these the same complaint? Respond with JSON only."""

    messages = [
        SystemMessage(content=DUPLICATE_CHECK_PROMPT),
        HumanMessage(content=user_msg),
    ]

    try:
        response = llm.invoke(messages)
        content = response.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        result = json.loads(content)
        return {
            "is_duplicate": result.get("is_duplicate", False),
            "confidence": result.get("confidence", 0.0),
            "explanation": result.get("explanation", ""),
        }
    except Exception as e:
        traceback.print_exc()
        return {
            "is_duplicate": False,
            "confidence": 0.0,
            "explanation": f"LLM verification failed: {str(e)}",
        }


def check_for_duplicates(
    db: Session,
    complaint_data: dict,
    exclude_id: Optional[str] = None,
) -> dict:
    """Full duplicate detection pipeline using persisted pgvector embeddings."""
    try:
        candidates, new_embedding = find_similar_complaints(
            db, complaint_data, exclude_id=exclude_id
        )

        if not candidates:
            return {
                "duplicate_detected": False,
                "matched_complaint": None,
                "similarity_score": 0.0,
                "confidence": 0.0,
                "explanation": "No similar complaints found in the database.",
                "new_embedding": new_embedding,
            }

        top_candidate = candidates[0]
        llm_result = llm_verify_duplicate(
            complaint_data, top_candidate["complaint"]
        )

        return {
            "duplicate_detected": llm_result["is_duplicate"],
            "matched_complaint": top_candidate["complaint"] if llm_result["is_duplicate"] else None,
            "similarity_score": top_candidate["similarity"],
            "confidence": llm_result["confidence"],
            "explanation": llm_result["explanation"],
            "new_embedding": new_embedding,
        }

    except Exception as e:
        traceback.print_exc()
        return {
            "duplicate_detected": False,
            "matched_complaint": None,
            "similarity_score": 0.0,
            "confidence": 0.0,
            "explanation": f"Duplicate detection encountered an error: {str(e)}. Submission allowed.",
            "new_embedding": [],
        }
