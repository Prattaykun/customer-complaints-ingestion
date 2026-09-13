import time
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from models.database import engine, Base
from models.complaint import EMBEDDING_DIMENSIONS
from routers import chat, upload, complaints


def _ensure_complaint_columns() -> None:
    """Ensure Neon schema has contact fields + pgvector embedding column."""
    queries = [
        "CREATE EXTENSION IF NOT EXISTS vector",
        "ALTER TABLE complaints ADD COLUMN IF NOT EXISTS complainant_phone VARCHAR(100)",
        "ALTER TABLE complaints ADD COLUMN IF NOT EXISTS complainant_email VARCHAR(255)",
        "ALTER TABLE complaints ADD COLUMN IF NOT EXISTS country_code VARCHAR(20)",
        "ALTER TABLE complaints ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100)",
        "ALTER TABLE complaints ADD COLUMN IF NOT EXISTS embedding_updated_at TIMESTAMP",
    ]

    for q in queries:
        for attempt in range(2):
            try:
                with engine.begin() as conn:
                    conn.execute(text(q))
                break
            except Exception as err:
                if attempt == 1:
                    print(f"Auto-migration query notice [{q[:30]}...]: {err}")
                time.sleep(0.5)

    # Detect existing embedding column type & migrate to pgvector if needed
    for attempt in range(2):
        try:
            with engine.begin() as conn:
                row = conn.execute(text(
                    """
                    SELECT data_type, udt_name
                    FROM information_schema.columns
                    WHERE table_name = 'complaints' AND column_name = 'embedding'
                    """
                )).fetchone()

                if row is None:
                    conn.execute(text(
                        f"ALTER TABLE complaints ADD COLUMN embedding vector({EMBEDDING_DIMENSIONS})"
                    ))
                    print(f"Added embedding vector({EMBEDDING_DIMENSIONS}) column")
                else:
                    data_type, udt_name = row
                    if udt_name != "vector":
                        print(f"Replacing embedding column type {data_type}/{udt_name} with vector({EMBEDDING_DIMENSIONS})")
                        conn.execute(text("ALTER TABLE complaints DROP COLUMN embedding"))
                        conn.execute(text(f"ALTER TABLE complaints ADD COLUMN embedding vector({EMBEDDING_DIMENSIONS})"))
            break
        except Exception as err:
            if attempt == 1:
                print(f"Auto-migration column notice: {err}")
            time.sleep(0.5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup & shutdown tasks."""
    try:
        Base.metadata.create_all(bind=engine)
        _ensure_complaint_columns()
    except Exception as err:
        print(f"Startup DB initialization notice: {err}")
    yield


app = FastAPI(
    title="PharmaQMS Customer Complaint Management System",
    description="AI-powered pharmaceutical QMS complaint management with LangGraph agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(complaints.router)


@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return {
        "name": "PharmaQMS Customer Complaint Management API",
        "version": "1.0.0",
        "status": "running",
    }


@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {"status": "healthy"}
