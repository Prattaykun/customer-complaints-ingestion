from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from models.database import engine, Base
from routers import chat, upload, complaints

# Create all database tables
Base.metadata.create_all(bind=engine)

# Auto-migrate newly added columns for existing database tables
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE complaints ADD COLUMN IF NOT EXISTS complainant_phone VARCHAR(100);"))
        conn.execute(text("ALTER TABLE complaints ADD COLUMN IF NOT EXISTS complainant_email VARCHAR(255);"))
        conn.execute(text("ALTER TABLE complaints ADD COLUMN IF NOT EXISTS country_code VARCHAR(20);"))
        conn.commit()
except Exception as err:
    print(f"Auto-migration notice: {err}")

app = FastAPI(
    title="PharmaQMS Customer Complaint Management System",
    description="AI-powered pharmaceutical QMS complaint management with LangGraph agent",
    version="1.0.0",
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(complaints.router)


@app.get("/")
async def root():
    return {
        "name": "PharmaQMS Customer Complaint Management API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
