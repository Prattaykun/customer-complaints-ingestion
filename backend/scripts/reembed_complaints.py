"""One-shot migration + re-embed all complaints into pgvector."""

from models.database import SessionLocal, engine
from models.complaint import EMBEDDING_DIMENSIONS
from services.duplicate_detector import reembed_all_complaints
from sqlalchemy import text


def migrate():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text(
            "ALTER TABLE complaints ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100)"
        ))
        conn.execute(text(
            "ALTER TABLE complaints ADD COLUMN IF NOT EXISTS embedding_updated_at TIMESTAMP"
        ))

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
            print(f"Added embedding vector({EMBEDDING_DIMENSIONS})")
        else:
            data_type, udt_name = row
            if udt_name != "vector":
                print(f"Dropping old embedding column ({data_type}/{udt_name})")
                conn.execute(text("ALTER TABLE complaints DROP COLUMN embedding"))
                conn.execute(text(
                    f"ALTER TABLE complaints ADD COLUMN embedding vector({EMBEDDING_DIMENSIONS})"
                ))
                print(f"Added embedding vector({EMBEDDING_DIMENSIONS})")
            else:
                print("embedding vector column already exists")


def main():
    migrate()
    db = SessionLocal()
    try:
        result = reembed_all_complaints(db, force=True)
        print("Re-embed result:", result)

        rows = db.execute(text(
            """
            SELECT id, product_name, embedding_model,
                   CASE WHEN embedding IS NULL THEN 0 ELSE vector_dims(embedding) END AS dims,
                   embedding_updated_at
            FROM complaints
            ORDER BY created_at DESC
            LIMIT 10
            """
        )).fetchall()
        print("Sample rows:")
        for r in rows:
            print(f"  {r[0]} | {r[1]} | model={r[2]} | dims={r[3]} | updated={r[4]}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
